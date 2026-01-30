import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field

DATA_DIR = Path("data")
QUESTIONS_PATH = DATA_DIR / "questions.json"
DB_PATH = DATA_DIR / "app.db"

Choice = Literal["A", "B", "C", "D", "E"]

app = FastAPI(title="Guess Keith Ward")

def db_init():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS champagne_claims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id TEXT NOT NULL,
                user_name TEXT NOT NULL,
                user_email TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()

def load_questions() -> List[Dict]:
    if not QUESTIONS_PATH.exists():
        raise HTTPException(status_code=500, detail="questions.json not found. Run extract_docx.py first.")
    return json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))

def save_questions(items: List[Dict]) -> None:
    QUESTIONS_PATH.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")

def find_question(items: List[Dict], qid: str) -> Optional[Dict]:
    for q in items:
        if q.get("id") == qid:
            return q
    return None

class SubmitGuessRequest(BaseModel):
    question_id: str
    choice: Choice

class SubmitGuessResponse(BaseModel):
    correct: bool
    message: str
    correct_choice: Choice
    explanation: Optional[str] = None
    hint: Optional[str] = None

class ClaimRequest(BaseModel):
    question_id: str
    user_name: str = Field(min_length=1, max_length=200)
    user_email: str = Field(min_length=3, max_length=320)

class QuestionListItem(BaseModel):
    id: str
    title: str
    question_preview: str

class QuestionDetail(BaseModel):
    id: str
    title: str
    question_text: str
    choices: List[str]   # exactly five
    # answer text is separate endpoint so you only see it after choosing or clicking through

@app.on_event("startup")
def on_startup():
    db_init()

@app.get("/api/questions", response_model=List[QuestionListItem])
def api_questions():
    items = load_questions()
    out = []
    for q in items:
        qt = (q.get("question_text") or "").strip()
        preview = qt[:220] + ("…" if len(qt) > 220 else "")
        out.append({
            "id": q["id"],
            "title": q.get("title", q["id"]),
            "question_preview": preview
        })
    return out

@app.get("/api/questions/{qid}", response_model=QuestionDetail)
def api_question_detail(qid: str):
    items = load_questions()
    q = find_question(items, qid)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    choices = q.get("choices") or []
    if len(choices) != 5:
        raise HTTPException(status_code=500, detail=f"Question {qid} does not have exactly 5 choices.")
    return {
        "id": q["id"],
        "title": q.get("title", q["id"]),
        "question_text": q.get("question_text", ""),
        "choices": choices
    }

@app.get("/api/questions/{qid}/answer")
def api_question_answer(qid: str):
    items = load_questions()
    q = find_question(items, qid)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    return {
        "id": q["id"],
        "title": q.get("title", q["id"]),
        "answer_text": q.get("answer_text", "")
    }

@app.post("/api/submit", response_model=SubmitGuessResponse)
def api_submit(req: SubmitGuessRequest):
    items = load_questions()
    q = find_question(items, req.question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    correct_choice: Choice = (q.get("correct_choice") or "C")
    is_correct = (req.choice == correct_choice)

    if is_correct:
        return {
            "correct": True,
            "message": "Correct — you've got Ward exactly right.",
            "correct_choice": correct_choice,
            "explanation": q.get("explanation_right") or None
        }
    else:
        return {
            "correct": False,
            "message": "Not quite right.",
            "correct_choice": correct_choice,
            "hint": q.get("hint_wrong") or "Try again: Ward's answer is subtler than this option suggests."
        }

@app.post("/api/claim")
def api_claim(req: ClaimRequest):
    items = load_questions()
    q = find_question(items, req.question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO champagne_claims (question_id, user_name, user_email) VALUES (?, ?, ?)",
            (req.question_id, req.user_name.strip(), req.user_email.strip())
        )
        conn.commit()

    return {"ok": True, "message": "Claim recorded. We'll be in touch about the champagne!"}

# Serve the frontend (static files)
FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"

@app.get("/", response_class=HTMLResponse)
def index():
    return (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")

@app.get("/styles.css")
def styles():
    return FileResponse(FRONTEND_DIR / "styles.css")

@app.get("/app.js")
def appjs():
    return FileResponse(FRONTEND_DIR / "app.js")
