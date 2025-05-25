# EconoGuide Backend

A FastAPI backend for the 'EconoGuide' (Economic Literacy Assessment application).
For [Hackonomics 2025](https://hackonomics25.devpost.com/) hackathon project EconoGuide.

## Features

- RESTful API endpoints for assessment management
- Integration with Google Cloud Gemini AI (optional)
- Question generation and scoring system
- Personalized recommendation generation
- CORS support for frontend integration

## Tech Stack

- Python 3.8+
- FastAPI
- Uvicorn (ASGI server)
- Google Cloud Gemini AI (optional)
- Pydantic for data validation

## Project Structure

```
be/
├── main.py             # Main application file
├── requirements.txt    # Python dependencies
└── .env               # Environment variables (create this)
```

## Getting Started

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start the development server:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

## API Endpoints

### GET /
- Health check endpoint
- Returns: Welcome message

### GET /generate-questions
- Generates economic literacy assessment questions
- Returns: JSON array of questions with answer options

### POST /submit-quiz
- Processes quiz submissions and generates recommendations
- Request Body: Array of answers with question IDs
- Returns: Score and personalized recommendations

## Data Models

### QuizAnswer
```python
class QuizAnswer(BaseModel):
    question_id: int
    answer: str
```

### QuizSubmission
```python
class QuizSubmission(BaseModel):
    answers: List[QuizAnswer]
```

## Mock Data

The application includes mock data for development:
- 15 economic literacy questions
- 7 personalized recommendations
- Simulated scoring system

## Google Cloud Integration (Optional)

To enable Gemini AI integration:

1. Create a `.env` file with:
```
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/credentials.json
```

2. Install additional dependencies:
```bash
pip install google-cloud-aiplatform python-dotenv
```

3. Update the code to use Gemini AI instead of mock data

## Dependencies

- fastapi - Web framework
- uvicorn - ASGI server
- pydantic - Data validation
- python-multipart - Form data parsing
- google-cloud-aiplatform (optional) - Gemini AI integration
- python-dotenv (optional) - Environment variable management 