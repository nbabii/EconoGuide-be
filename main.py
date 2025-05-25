from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json

app = FastAPI(title="EconoGuide API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuizAnswer(BaseModel):
    question_id: int
    answer: str

class QuizSubmission(BaseModel):
    answers: List[QuizAnswer]

# Mock questions data
MOCK_QUESTIONS = [
    {
        "question": "What is the primary purpose of a budget?",
        "answers": [
            "To track daily expenses only",
            "To plan and control spending, saving, and investing",
            "To calculate monthly bills",
            "To record past purchases",
            "To impress others with financial knowledge"
        ]
    },
    {
        "question": "What is compound interest?",
        "answers": [
            "Interest earned only on the principal amount",
            "Interest earned on both principal and accumulated interest",
            "A fixed interest rate that never changes",
            "Interest paid to compound your debt",
            "A type of tax deduction"
        ]
    },
    {
        "question": "Which investment typically carries the highest risk?",
        "answers": [
            "Government bonds",
            "Individual stocks",
            "Cryptocurrency",
            "Certificates of deposit",
            "High-yield savings accounts"
        ]
    }
] * 5  # Multiply to get 15 questions (temporary for mock data)

# Mock recommendations data
MOCK_RECOMMENDATIONS = [
    {
        "title": "Build an Emergency Fund",
        "description": "Start with a basic emergency fund to cover unexpected expenses.",
        "implementation_plan": [
            "Open a high-yield savings account",
            "Set up automatic monthly transfers of $100",
            "Review and adjust transfer amount quarterly",
            "Aim for 3-6 months of expenses saved",
            "Consider increasing savings rate",
            "Review emergency fund policies",
            "Maintain and monitor progress",
            "Evaluate and adjust goals",
            "Consider additional savings vehicles",
            "Review insurance coverage",
            "Optimize emergency fund allocation",
            "Celebrate reaching initial goal"
        ]
    }
] * 7  # Multiply to get 7 recommendations (temporary for mock data)

@app.get("/")
async def root():
    return {"message": "Welcome to EconoGuide API"}

@app.get("/generate-questions")
async def generate_questions():
    try:
        return {"questions": json.dumps(MOCK_QUESTIONS)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/submit-quiz")
async def submit_quiz(submission: QuizSubmission):
    try:
        # Mock scoring logic - each answer gets a random score between 60 and 100
        import random
        total_score = sum(random.randint(60, 100) for _ in submission.answers)
        
        return {
            "score": total_score,
            "recommendations": json.dumps(MOCK_RECOMMENDATIONS)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 