from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json
import os
from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel

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

vertexai.init(project="econoguide", location="us-central1")
model = GenerativeModel("gemini-2.0-flash")

async def generate_quiz_questions():
    prompt = """You are a financial literacy coach.
            You are a financial literacy coach.

            Your task is to generate 15 single-choice financial literacy assessment questions.

            Requirements:
            - Each question must assess an individual's financial knowledge.
            - Each question must have exactly 5 answer choices.
            - All 5 answers must be technically valid but represent increasing levels of financial understanding, from basic to optimal.
            - The 15 questions must collectively cover the following topics: budgeting, investing, debt, retirement, and risk management.
            - Answers should reflect real-world financial concepts, habits, and tools (e.g., savings accounts, credit utilization, 401(k), diversification, insurance).
            - Ensure that no answers are factually incorrect, just less optimal.

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
            """

    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 40
            }
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
    except Exception as e:
        print(f"Gemini API Error: {str(e)}")
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
    
    prompt = f"""You are a financial literacy coach.
    Analyze these quiz answers and provide a comprehensive assessment with scores and recommendations.
    Each question score is based on the answer selected by the user, min score is 10 and max score is 100.
    The quiz answers are about personal finance and financial literacy of individual.
    The quiz answers are about the following topics: budgeting, investing, debt, retirement, risk management.
    The quiz answers are following:
    
    Quiz Responses:
    {answers_text}

    Provide a response in the following JSON format:
    {{
        "question_scores": [
            {{
                "question_id": number,
                "question": string,
                "selected_answer": string,
                "score": number (10-100),
                "explanation": string (brief explanation of the score)
            }}
        ],
        "overall_assessment": {{
            "total_score": number (sum of scores for all questions),
            "score_interpretation": string (brief interpretation of the overall score)
        }},
        "targeted_recommendations": [
            {{
                "area": string (financial topic needing most improvement),
                "current_status": string (brief assessment of understanding),
                "improvement_plan": {{
                    "immediate_actions": [string] (2-3 specific actions),
                    "long_term_goals": [string] (2-3 goals),
                    "resources": [string] (2-3 specific resources like books, websites, tools)
                }}
            }}
        ]
    }}

    Requirements:
    - Provide 5-7 targeted recommendations focusing on lowest scoring areas
    - Keep explanations concise but actionable, and up to current date
    - Include specific, practical resources for improvement

    IMPORTANT: Return ONLY valid JSON, no additional text or explanation."""

    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 40
        }
    )

    try:
        response_text = response.text.strip()
        response_text = response_text.replace('```json', '').replace('```', '').strip()
        analysis_result = json.loads(response_text)
        return analysis_result
    except json.JSONDecodeError as e:
        print(f"JSON Parse Error: {str(e)}")
        print(f"Response text: {response_text}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse AI response as JSON"
        )
    except Exception as e:
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