import streamlit as st
from cohere import Client
from random import choice
import uuid
import sqlite3
import datetime
import requests
import json
import speech_recognition as sr
from streamlit_option_menu import option_menu
import streamlit.components.v1 as components
import re

# ========================== SETUP ==========================
def speak_with_browser(text):
    escaped_text = text.replace("'", "\\'")
    components.html(f"""
        <script>
            var msg = new SpeechSynthesisUtterance('{escaped_text}');
            window.speechSynthesis.speak(msg);
        </script>
    """, height=0)

conn = sqlite3.connect("pmai_users.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, username TEXT, email TEXT, password TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS messages (user_id TEXT, mode TEXT, message TEXT, response TEXT, timestamp TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS views (count INTEGER)''')
c.execute("INSERT INTO views (count) SELECT 0 WHERE NOT EXISTS (SELECT 1 FROM views)")
conn.commit()

# ========================== SESSION STATE ==========================
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "user" not in st.session_state:
    st.session_state.user = None
if "chat_histories" not in st.session_state:
    st.session_state.chat_histories = {}
if st.session_state.session_id not in st.session_state.chat_histories:
    st.session_state.chat_histories[st.session_state.session_id] = []
chat_history = st.session_state.chat_histories[st.session_state.session_id]

# ========================== THEMING ===========================
st.set_page_config(page_title="PMAI - Prince Magami AI Assistant", page_icon="🤖", layout="wide")
st.markdown("""
    <style>
    body, .stApp {
        background-color: #0c1a2b;
        color: #ffffff;
        font-family: 'Segoe UI', sans-serif;
    }
    .response-block {
        background-color: #1c2d45;
        color: white;
        border-left: 4px solid #3399ff;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .custom-box {
        background-color: rgba(255, 255, 255, 0.1);
        padding: 2rem;
        border-radius: 10px;
        backdrop-filter: blur(10px);
    }
    input, textarea {
        background-color: #1f2f40 !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

# ========================== API ==========================
co = Client(st.secrets["cohere_api_key"])

# ========================== SIDEBAR ==========================
with st.sidebar:
    if st.session_state.user and st.session_state.user[2] == "magamiabu@gmail.com":
        menu = ["Home", "Logout", "Admin Panel", "Analytics"]
    else:
        menu = ["Home", "Login", "Register"]
    selected = option_menu("PMAI Menu", menu, icons=['house', 'box-arrow-left', 'shield-lock', 'bar-chart'],
        menu_icon="robot", default_index=0)

# ========================== UTILITIES ==========================
def validate_password(pw):
    return len(pw) >= 8 and re.search(r"[A-Za-z]", pw) and re.search(r"[0-9!@#]", pw)

def get_response(prompt):
    try:
        res = co.generate(model="command-r-plus", prompt=prompt, max_tokens=250, temperature=0.7)
        return res.generations[0].text.strip()
    except Exception as e:
        return f"Error: {str(e)}"

def scam_checker_api(text):
    try:
        import urllib.parse
        api_key = st.secrets["ipqs_api_key"]
        url = f"https://ipqualityscore.com/api/json/url/{api_key}/{urllib.parse.quote(text.strip())}"
        res = requests.get(url).json()
        return f"⚠️ Warning: Unsafe ({res.get('suspicious', 'Risky')})" if res.get("unsafe") else "✅ Link appears safe."
    except Exception as e:
        return f"Scan error: {str(e)}"

def save_message(user_id, mode, msg, res):
    c.execute("INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?)",
              (user_id, mode, msg, res, str(datetime.datetime.now()), ""))
    conn.commit()

def record_audio():
    try:
        rec = sr.Recognizer()
        with sr.Microphone() as source:
            st.info("🎤 Listening...")
            audio = rec.listen(source)
            return rec.recognize_google(audio)
    except:
        return "Sorry, could not recognize your voice."

# ========================== AUTH ==========================
def register():
    with st.container():
        st.markdown("""<div class='custom-box'>""", unsafe_allow_html=True)
        st.subheader("🔐 Create New Account")
        u = st.text_input("Username")
        e = st.text_input("Email")
        p = st.text_input("Password", type="password")
        if st.button("Register"):
            if not (u and e and p):
                st.error("Please fill in all fields.")
            elif not validate_password(p):
                st.warning("Password must be 8+ chars with letters & numbers/specials.")
            else:
                uid = str(uuid.uuid4())
                c.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (uid, u, e, p))
                conn.commit()
                st.session_state.user = (uid, u, e, p)
                st.success("Account created! Redirecting to Home...")
                st.experimental_rerun()
        st.markdown("Already have an account? Go to Login.")
        st.markdown("""</div>""", unsafe_allow_html=True)

def login():
    with st.container():
        st.markdown("""<div class='custom-box'>""", unsafe_allow_html=True)
        st.subheader("👤 Login")
        e = st.text_input("Email")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            c.execute("SELECT * FROM users WHERE email=? AND password=?", (e, p))
            u = c.fetchone()
            if u:
                st.session_state.user = u
                st.success("Welcome!")
                st.experimental_rerun()
            else:
                st.error("Invalid credentials.")
        st.markdown("Don't have an account? Go to Register.")
        st.markdown("""</div>""", unsafe_allow_html=True)

def logout():
    st.session_state.user = None
    st.experimental_rerun()

# ========================== CHAT ==========================
def chat():
    st.subheader("💬 PMAI Chat")
    voice = st.checkbox("🔊 Enable Voice")
    lang = st.radio("Language", ["English", "Pidgin"], horizontal=True)
    mode = st.selectbox("Mode", ["Chatbox", "Scam Checker", "Academic Help", "Business Tips", "Cybersecurity"])
    user_input = st.text_area("Type your message:", key="chatbox")
    if st.button("Send") or (user_input and st.session_state.get("enter_trigger")):
        if user_input:
            st.session_state.enter_trigger = False
            if mode == "Scam Checker":
                reply = scam_checker_api(user_input)
            else:
                prompt = f"Respond in {lang}. User said: {user_input}" if mode == "Chatbox" else f"You are a {mode} expert. Help the user: {user_input}"
                reply = get_response(prompt)
            if voice:
                speak_with_browser(reply)
            st.markdown(f"<div class='response-block'><b>PMAI:</b> {reply}</div>", unsafe_allow_html=True)
            if st.session_state.user:
                save_message(st.session_state.user[0], mode, user_input, reply)
            st.session_state.chatbox = ""

# ========================== ADMIN ==========================
def admin():
    st.title("🔐 Admin Panel")
    c.execute("SELECT COUNT(*) FROM users")
    st.metric("Users", c.fetchone()[0])
    c.execute("SELECT COUNT(*) FROM messages")
    st.metric("Messages", c.fetchone()[0])
    c.execute("SELECT * FROM users")
    with st.expander("📧 Registered Emails"):
        for u in c.fetchall():
            st.text(u[2])
    with st.expander("🧠 All Chat History"):
        c.execute("SELECT * FROM messages ORDER BY timestamp DESC LIMIT 100")
        for m in c.fetchall():
            st.markdown(f"**{m[4]}** - {m[1]}\n\n**User:** {m[2]}\n\n**PMAI:** {m[3]}")

# ========================== ANALYTICS ==========================
def analytics():
    st.subheader("📊 Usage Analytics")
    c.execute("SELECT mode, COUNT(*) FROM messages GROUP BY mode")
    data = c.fetchall()
    st.bar_chart({d[0]: d[1] for d in data})

# ========================== ROUTING ==========================
c.execute("UPDATE views SET count = count + 1")
conn.commit()
if selected == "Register":
    register()
elif selected == "Login":
    login()
elif selected == "Logout":
    logout()
elif selected == "Home":
    chat()
elif selected == "Admin Panel" and st.session_state.user and st.session_state.user[2] == "magamiabu@gmail.com":
    admin()
elif selected == "Analytics" and st.session_state.user and st.session_state.user[2] == "magamiabu@gmail.com":
    analytics()

# ========================== FOOTER ==========================
st.markdown("""---
<div style='text-align:center;'>
<b>PMAI Assistant by Abubakar Muhammad Magami</b><br>
<small>Email: magamiabu@gmail.com | Fellow ID: FE/23/75909764 | 3MTT Cohort 3</small>
</div>
""", unsafe_allow_html=True)
