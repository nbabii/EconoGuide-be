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
    prompt = """Generate 15 financial literacy assessment questions. Each question should have 5 answers that represent different levels of financial understanding, from basic to optimal choices. Return ONLY a JSON array in this exact format:
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

            Requirements:
            - Generate exactly 15 questions
            - Each question must have exactly 5 answers
            - Answers should be ordered from basic (10 points) to optimal (100 points)
            - Cover topics: budgeting, investing, debt, retirement, risk management
            - All answers should be technically valid but represent different levels of financial sophistication
            
            IMPORTANT: Return ONLY the JSON array, no additional text or explanation.
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

        # Clean the response text to ensure it only contains JSON
        response_text = response.text.strip()
        # Remove any potential markdown code block markers
        response_text = response_text.replace('```json', '').replace('```', '')
        # Remove any leading/trailing whitespace or newlines
        response_text = response_text.strip()

        try:
            questions = json.loads(response_text)
            
            # Validate the structure of the questions
            if not isinstance(questions, list):
                raise ValueError("Response is not a JSON array")
            
            for q in questions:
                if not isinstance(q, dict):
                    raise ValueError("Question is not a dictionary")
                if "question" not in q or "answers" not in q:
                    raise ValueError("Question missing required fields")
                if not isinstance(q["answers"], list) or len(q["answers"]) != 5:
                    raise ValueError("Question must have exactly 5 answers")

            frontend_questions = []
            for q in questions:
                frontend_questions.append({
                    "question": q["question"],
                    "answers": [a.split(" (")[0] for a in q["answers"]]  # Remove points from answers
                })
            return frontend_questions

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
    answers_text = "\n".join([f"Q{a.question_id}: {a.selected_answer}" for a in answers])
    
    prompt = f"""Based on these quiz answers about personal finance, generate personalized recommendations: {answers_text}"""

    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 40
        },
        safety_settings={
            "HARASSMENT": "block_none",
            "HATE_SPEECH": "block_none",
            "SEXUALLY_EXPLICIT": "block_none",
            "DANGEROUS_CONTENT": "block_none"
        },
        stream=False,
        tools=[{
            "function_declarations": [{
                "name": "generate_recommendations",
                "description": "Generate financial recommendations based on quiz answers",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "recommendations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {
                                        "type": "string",
                                        "description": "Title of the recommendation"
                                    },
                                    "description": {
                                        "type": "string",
                                        "description": "Brief description of the recommendation"
                                    },
                                    "implementation_plan": {
                                        "type": "array",
                                        "items": {
                                            "type": "string"
                                        },
                                        "minItems": 3,
                                        "description": "List of implementation steps"
                                    }
                                },
                                "required": ["title", "description", "implementation_plan"]
                            },
                            "minItems": 7,
                            "maxItems": 7
                        }
                    },
                    "required": ["recommendations"]
                }
            }]
        }]
    )

    try:
        recommendations = json.loads(response.text)
        
        if not isinstance(recommendations, list):
            raise ValueError("Response is not a JSON array")
            
        for r in recommendations:
            if not isinstance(r, dict) or "title" not in r or "description" not in r or "implementation_plan" not in r:
                raise ValueError("Recommendation format is incorrect")
            if len(r["implementation_plan"]) < 3:
                raise ValueError("Each recommendation must have at least 3 implementation steps")
        
        return recommendations
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse AI response as JSON")
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
        total_score = 0
        for answer in submission.answers:
            answer_index = answer.all_answers.index(answer.selected_answer)
            points = [10, 25, 50, 75, 100][answer_index]
            total_score += points

        recommendations = await analyze_answers_and_generate_recommendations(submission.answers)
        
        return {
            "score": total_score / len(submission.answers),
            "recommendations": recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 