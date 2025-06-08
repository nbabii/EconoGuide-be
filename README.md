# EconoGuide Backend

A FastAPI backend for the 'EconoGuide' (Economic Literacy Assessment application).
For [Hackonomics 2025](https://hackonomics25.devpost.com/) hackathon project EconoGuide.

## Features

- RESTful API endpoints for assessment management
- Integration with Google Cloud Gemini AI
- Question generation and scoring system
- Personalized recommendation generation

## Tech Stack

- Python 3.12
- FastAPI
- Google Cloud Gemini AI 


## Getting Started

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate
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
