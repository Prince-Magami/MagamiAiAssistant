# PMAI - Prince Magami AI
# Monolithic app.py built with FastAPI and Cohere
# Includes: 7 Modes, Auth, Chat System, Admin Dashboard, Session Tracking, Timed Exam, Job Suggestion

# ------------ IMPORTS ------------
import uvicorn
from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import secrets, random, json, hashlib, re, time, os, sqlite3
import cohere

# ------------ INITIALIZE APP ------------
app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

co = cohere.Client(os.getenv("COHERE_API_KEY"))

# ------------ DATABASE SETUP ------------
db = sqlite3.connect("pmai.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    password TEXT,
    name TEXT,
    is_verified INTEGER,
    is_admin INTEGER DEFAULT 0,
    registered_on TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    mode TEXT,
    lang TEXT,
    started_on TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS chats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    sender TEXT,
    message TEXT,
    reply TEXT,
    timestamp TEXT,
    FOREIGN KEY(session_id) REFERENCES sessions(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS exam_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    exam_type TEXT,
    subject TEXT,
    questions TEXT,
    user_answers TEXT,
    score INTEGER,
    timestamp TEXT,
    duration INTEGER
)
""")

db.commit()

# ------------ UTILITIES ------------
def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def check_password(pw, hashed):
    return hash_password(pw) == hashed

def strong_password(pw):
    return bool(re.match(r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d).{8,}$", pw))

def build_prompt(mode, lang, user_input):
    base_persona = {
        "scam": "Act like a cybersecurity analyst. Scan messages for phishing and fraud attempts. Respond seriously.",
        "cyber": "Act like a professional cybersecurity advisor. Provide practical and technical security advice.",
        "edu": "Act like a tutor. Help secondary and university students understand complex topics clearly.",
        "exam": "Act like an examiner. Ask subject-based questions and score them fairly with explanations.",
        "job": "Act like a career coach. Suggest jobs and CV improvements based on user's skills.",
        "chat": "Be witty, fun, and informal. Just like ChatGPT in freestyle mode.",
        "advice": "Be wise and kind. Give helpful, honest life advice."
    }
    persona = base_persona.get(mode, "Respond clearly to user input.")
    language_note = "Respond only in Nigerian Pidgin" if lang == "pidgin" else "Respond in formal English"
    return f"{persona}\n{language_note}.\nUser: {user_input}\nAssistant:"

# ------------ AUTH ROUTES ------------
@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login_post(request: Request, email: str = Form(...), password: str = Form(...)):
    cursor.execute("SELECT id, password FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    if not user or not check_password(password, user[1]):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid login"})
    response = RedirectResponse("/chat", status_code=302)
    response.set_cookie("user_id", str(user[0]), max_age=3600)
    return response

@app.get("/register", response_class=HTMLResponse)
async def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register_post(request: Request, email: str = Form(...), name: str = Form(...), password: str = Form(...), confirm: str = Form(...)):
    if password != confirm or not strong_password(password):
        return templates.TemplateResponse("register.html", {"request": request, "error": "Passwords don't match or not strong"})
    try:
        cursor.execute("INSERT INTO users (email, password, name, is_verified, registered_on) VALUES (?, ?, ?, ?, ?)",
            (email, hash_password(password), name, 1, datetime.utcnow().isoformat()))
        db.commit()
    except:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Email exists"})
    return RedirectResponse("/login", status_code=302)

@app.get("/logout")
async def logout():
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie("user_id")
    return response

# ------------ LANDING ------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ------------ CHAT PAGE ------------
@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    user_id = request.cookies.get("user_id")
    cursor.execute("SELECT name FROM users WHERE id = ?", (user_id,))
    name = cursor.fetchone()
    return templates.TemplateResponse("chat.html", {"request": request, "name": name[0] if name else "Guest"})

# ------------ MODE LOGIC ------------
@app.post("/api/chat")
async def process_chat(request: Request):
    data = await request.json()
    user_input = data.get("message")
    mode = data.get("mode")
    lang = data.get("lang")
    user_id = request.cookies.get("user_id")

    if not user_id:
        return {"reply": "Please log in to continue."}

    prompt = build_prompt(mode, lang, user_input)
    cohere_response = co.chat(model="command-r-plus", message=user_input, preamble=prompt)
    reply = cohere_response.text.strip()

    cursor.execute("INSERT INTO sessions (user_id, mode, lang, started_on) VALUES (?, ?, ?, ?)",
                   (user_id, mode, lang, datetime.utcnow().isoformat()))
    session_id = cursor.lastrowid
    cursor.execute("INSERT INTO chats (session_id, sender, message, reply, timestamp) VALUES (?, ?, ?, ?, ?)",
                   (session_id, "user", user_input, reply, datetime.utcnow().isoformat()))
    db.commit()
    return {"reply": reply}

# ------------ ADMIN PAGE ------------
@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    user_id = request.cookies.get("user_id")
    cursor.execute("SELECT email FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if not row or row[0] != "magamiabu@gmail.com":
        raise HTTPException(status_code=403)
    cursor.execute("SELECT COUNT(*), SUM(LENGTH(message)) FROM chats")
    chat_stats = cursor.fetchone()
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    return templates.TemplateResponse("admin.html", {"request": request, "stats": chat_stats, "users": user_count})

# ------------ START ------------
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
    
