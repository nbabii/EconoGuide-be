from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import aiohttp

load_dotenv()

app = FastAPI(title="EconoGuide API")

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8080",
    "https://econoguide-frontend-349130934423.us-central1.run.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuizAnswer(BaseModel):
    question_id: int
    question: str
    selected_answer: str
    all_answers: List[str]

class QuizSubmission(BaseModel):
    answers: List[QuizAnswer]


api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY environment variable is required")

client = genai.Client(api_key=api_key)

grounding_tool = types.Tool(
    google_search=types.GoogleSearch()
)

config = types.GenerateContentConfig(
    tools=[grounding_tool]
)

async def generate_quiz_questions():
    prompt = """
            You are a financial literacy coach.

            Your task is to generate 15, up to the current date, single-choice financial literacy assessment questions.

            Requirements:
            - Each question must assess an individual's financial knowledge.
            - Each question must have exactly 5 answer choices.
            - All 5 answers must be technically valid but represent increasing levels of financial understanding, from basic to optimal.
            - The 15 questions must collectively cover the following topics: budgeting, investing, debt, retirement, and risk management.
            - Answers should reflect real-world financial concepts, habits, and tools.
            - Ensure that no answers are factually incorrect, just less optimal.
            - Ensure that answers are not ordered by the most optimal to the least optimal.

            Format:
            Return ONLY a JSON array in the **exact format** shown below. Do not include any explanation or text outside the array.

            Example format:
            [
                {
                    "question": "What is the most effective way to build long-term wealth?",
                    "answers": [
                        "Keeping all savings in a basic checking account",
                        "Investing only in high-risk cryptocurrency",
                        "Putting money in a high-yield savings account",
                        "Investing in a mix of stocks and bonds",
                        "Regular contributions to a diversified portfolio with automatic rebalancing"
                    ]
                }
            ]

            IMPORTANT:
            - Return exactly 15 objects in the array.
            - Each object must follow the format above.
            - Do not add any commentary, markdown, or explanations.
            - Output must be valid JSON only.
            - Use current financial information and market trends when generating questions.
            """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        if response is None:
            raise HTTPException(
                status_code=500,
                detail="Gemini API returned None response. Please check your API key and model availability."
            )

        if not hasattr(response, 'text') or response.text is None:
            raise HTTPException(
                status_code=500,
                detail="Gemini API response has no text content. Please check your API key and model availability."
            )

        response_text = response.text.strip()
        response_text = response_text.replace('```json', '').replace('```', '').strip()

        try:
            questions = json.loads(response_text)
            
            if not isinstance(questions, list):
                raise ValueError("Response is not a JSON array")
            
            for q in questions:
                if not isinstance(q, dict):
                    raise ValueError("Question is not a dictionary")
                if "question" not in q or "answers" not in q:
                    raise ValueError("Question missing required fields")
                if not isinstance(q["answers"], list) or len(q["answers"]) != 5:
                    raise ValueError("Question must have exactly 5 answers")

            return questions

        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {str(e)}")
            print(f"Response text: {response_text}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse AI response as JSON. Response: {response_text[:200]}..."
            )
        except ValueError as e:
            print(f"Validation Error: {str(e)}")
            print(f"Response text: {response_text}")
            raise HTTPException(
                status_code=500,
                detail=f"Invalid response format: {str(e)}"
            )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Gemini API Error: {str(e)}")
        print(f"Error type: {type(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating questions: {str(e)}"
        )

async def analyze_answers_and_generate_recommendations(answers: List[QuizAnswer]):
    answers_text = "\n".join([
        f"Question {a.question_id}: {a.question}\n"
        f"Selected Answer: {a.selected_answer}\n"
        f"All Options: {' | '.join(a.all_answers)}\n"
        for a in answers
    ])
    
    prompt = f"""
            You are a financial literacy coach and expert in personal finance education.
            Analyze the following quiz answers and generate a comprehensive assessment in JSON format, including individual question scoring, overall evaluation, and personalized recommendations.
            Each question is scored based on the selected answer, with a minimum of 10 and a maximum of 100 points, you need to score each question based on the selected answer.

            ---

            Quiz Responses:
            {answers_text}

            ---

            Output Format (strictly follow this JSON structure):
            {{
            "question_scores": [
                {{
                "question_id": number,
                "question": string,
                "selected_answer": string,
                "score": number (between 10 and 100),
                "explanation": string (brief rationale behind the score)
                }}
            ],
            "overall_assessment": {{
                "total_score": number (sum of individual scores),
                "score_interpretation": string (interpret the user's overall financial literacy level)
            }},
            "targeted_recommendations": [
                {{
                "area": string (financial topic needing the most improvement),
                "area_label": {{
                    "type": string ("svg"),
                    "value": string (inline SVG markup suitable for direct rendering in HTML/React)
            }},
                "current_status": string (brief status of user's understanding),
                "improvement_plan": {{
                    "immediate_actions": [string, string, ...] (2-3 specific actions),
                    "long_term_goals": [string, string, ...] (2-3 goals),
                    "resources": [
                    {{
                        "title": string,
                        "url": string (MUST be a real, active URL found through web search, check requirements under 'CRITICAL GUIDELINES FOR IMPROVEMENT PLAN RESOURCES')
                    }}
                    ]
                }}
                }}
            ]
            }}

            CRITICAL GUIDELINES FOR IMPROVEMENT PLAN RESOURCES:
            - You MUST use web search tool to find real, active URLs for financial education resources to explain the recommendation
            - ONLY include educational content
            - DO NOT include tools, apps, services, or commercial products
            - Prefer well-known, reputable financial websites, educational institutions, and organizations
            - Include 2-3 resources per recommendation area


            GENERAL GUIDELINES:
            - Provide valid JSON output only. No additional text, explanation, or markdown.
            - Include 5 to 7 targeted recommendations based on the lowest-scoring areas.
            - For each `area_label`, include a compact inline SVG suitable for embedding in a React app.
                - Visually clean, modern designed, and representative of the appropriate financial area.
                - Ensure the SVGs are #1976d2 color.
            - Be specific and constructive in recommendations and improvement plans.
            - Explanations and suggestions should be concise but actionable.
            - Leverage current financial market conditions, interest rates, and economic trends when providing recommendations.
            - Include recent financial news and regulatory changes that might affect personal finance decisions.

            STRICTLY RETURN ONLY A VALID JSON OBJECT.
            """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"tools": [{"google_search": {}}]},
        )

        if response is None:
            raise HTTPException(
                status_code=500,
                detail="Gemini API returned None response. Please check your API key and model availability."
            )

        if not hasattr(response, 'text') or response.text is None:
            raise HTTPException(
                status_code=500,
                detail="Gemini API response has no text content. Please check your API key and model availability."
            )

        response_text = response.text.strip()
        response_text = response_text.replace('```json', '').replace('```', '').strip()
        analysis_result = json.loads(response_text)
        return analysis_result
    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        print(f"JSON Parse Error: {str(e)}")
        print(f"Response text: {response_text}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse AI response as JSON"
        )
    except Exception as e:
        print(f"Gemini API Error: {str(e)}")
        print(f"Error type: {type(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Welcome to EconoGuide API"}

@app.get("/generate-questions")
async def generate_questions():
    try:
        questions = await generate_quiz_questions()
        return {"questions": questions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/submit-quiz")
async def submit_quiz(submission: QuizSubmission):
    try:
        result = await analyze_answers_and_generate_recommendations(submission.answers)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
