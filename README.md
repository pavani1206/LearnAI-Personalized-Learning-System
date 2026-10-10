# LearnAI — Personalized Learning and Course Recommendation System

A local full-stack student project using React + Vite, Flask, SQLAlchemy, SQLite by default, and scikit-learn TF-IDF cosine similarity for course recommendations. No paid AI API is required.

## Features included
- Student registration/login with password hashing and token-based API sessions
- Three-stage onboarding: degree/course, branch/specialization/year, weak topics, interests and career goal
- Supports Engineering, Pharmacy, Medical/Health Sciences, Business/Management, BA, BSc, BCom and other degrees
- Course catalog and profile-aware course recommendations (TF-IDF + cosine similarity, with a safe fallback)
- Learning roadmap, learning resources, quizzes/assessments, aptitude practice, quiz scores and progress tracking
- Career direction suggestions based on chosen goal and profile (guidance, not a guaranteed prediction)
- Flask REST API and persistent database
- SQLite works out of the box. Optional MySQL configuration is documented below.

## Run on Windows
Requirements: Python 3.10+ and Node.js 18+.

### 1. Start backend
Open a terminal in this folder:
```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python seed.py
python app.py
```
Backend runs at `http://127.0.0.1:5000`.
If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal, then activate again.

### 2. Start frontend (a second terminal)
```powershell
cd frontend
npm install
npm run dev
```
Open the local URL Vite prints, usually `http://localhost:5173`.

### Demo
Register a new account with your own email/password. No pre-filled demo account is needed.

## Optional MySQL
SQLite is the default so the project starts without a database server. To use MySQL, create a database named `learnai`, install the optional driver with `pip install pymysql`, then set `DATABASE_URL` before starting Flask:
```powershell
$env:DATABASE_URL="mysql+pymysql://YOUR_USER:YOUR_PASSWORD@localhost/learnai?charset=utf8mb4"
python seed.py
python app.py
```
Use your own credentials; do not commit passwords. The schema is created automatically.

## Important project notes
- Recommendation logic uses TF-IDF and cosine similarity over student profile text and course descriptions. If scikit-learn is unavailable, the backend uses a deterministic keyword fallback.
- This is an educational prototype. Authentication is suitable for local demonstration, not production deployment without HTTPS, stronger session management, rate limiting, and security review.
- Course materials are curated starter content and links. They are not a complete official syllabus for every university. Students should verify materials against their institution's curriculum.
- The AI Assistant provides built-in study guidance; it does not call a paid external LLM.
