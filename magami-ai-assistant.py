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
if "chatbox" not in st.session_state:
    st.session_state.chatbox = ""
if "show_welcome" not in st.session_state:
    st.session_state.show_welcome = True

chat_history = st.session_state.chat_histories[st.session_state.session_id]

# ========================== THEMING ===========================
st.markdown("""
    <style>
    :root {
        --bg-color-dark: #010922;
        --text-color-dark: #ffffff;
        --response-bg-dark: #121a3c;
    }
    body, .stApp {
        background-color: var(--bg-color-dark);
        color: var(--text-color-dark);
    }
    .response-block {
        background-color: var(--response-bg-dark);
        color: var(--text-color-dark);
        border-left: 5px solid #0072C6;
        padding: 15px;
        margin-top: 10px;
        margin-bottom: 10px;
        border-radius: 10px;
        font-size: 16px;
    }
    .custom-box {
        background: rgba(0,0,0,0.8);
        color: white;
        border-radius: 10px;
        padding: 2rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    }
    .stButton > button {
        font-size: 16px;
        padding: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# ========================== API & CONFIG ===========================
st.set_page_config(page_title="PMAI - Prince Magami AI Assistant", page_icon="🤖", layout="wide")
cohere_api_key = st.secrets["cohere_api_key"]
co = Client(cohere_api_key)

# ========================== UTILITIES ==============================
def get_response(prompt):
    try:
        response = co.generate(
            model="command-r-plus",
            prompt=prompt,
            max_tokens=250,
            temperature=0.7,
            k=0,
            stop_sequences=["--"],
            return_likelihoods="NONE"
        )
        return response.generations[0].text.strip()
    except Exception as e:
        return f"Error: {str(e)}"

def scam_checker_api(text):
    try:
        import urllib.parse
        base_url = "https://ipqualityscore.com/api/json/url/"
        api_key = st.secrets["ipqs_api_key"]
        encoded_url = urllib.parse.quote(text.strip())
        query_url = f"{base_url}{api_key}/{encoded_url}"
        response = requests.get(query_url)
        result = response.json()
        if result.get("unsafe"):
            return f"⚠️ Warning: This link is flagged as unsafe. Reason: {result.get('suspicious', 'Potentially harmful')}"
        else:
            return "✅ This link appears safe based on real-time scan."
    except Exception as e:
        return f"Error checking link: {str(e)}"

def save_message(user_id, mode, msg, res):
    timestamp = str(datetime.datetime.now())
    c.execute("INSERT INTO messages (user_id, mode, message, response, timestamp) VALUES (?, ?, ?, ?, ?)",
              (user_id, mode, msg, res, timestamp))
    conn.commit()

def record_audio():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("Listening...")
        audio = recognizer.listen(source)
        try:
            return recognizer.recognize_google(audio)
        except:
            return "Voice not recognized."

def is_valid_password(password):
    return (
        len(password) >= 8 and
        re.search(r"[a-zA-Z]", password) and
        re.search(r"[0-9]", password) and
        re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)
    )

# ========================== WELCOME ==============================
def welcome():
    st.title("🤖 Welcome to PMAI - Prince Magami AI")
    st.markdown("""
        PMAI is a futuristic AI assistant built to solve problems for students, businesses, and individuals across Nigeria.

        🔹 Scam detection  
        🔹 Academic support  
        🔹 Emotional chat  
        🔹 Cybersecurity tips  
        🔹 And more — in both Pidgin and English!
    """)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔐 Login"):
            st.session_state.show_welcome = False
            st.session_state.page = "Login"
    with col2:
        if st.button("🆕 Register"):
            st.session_state.show_welcome = False
            st.session_state.page = "Register"

# ========================== AUTH ==============================
def register():
    st.markdown("""<div class='custom-box'>""", unsafe_allow_html=True)
    st.subheader("Create Your Account")
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Register"):
        if not username or not email or not password:
            st.warning("All fields are required.")
        elif not is_valid_password(password):
            st.warning("Password must be at least 8 characters long and include letters, numbers, and special characters.")
        else:
            user_id = str(uuid.uuid4())
            c.execute("INSERT INTO users (id, username, email, password) VALUES (?, ?, ?, ?)",
                      (user_id, username, email, password))
            conn.commit()
            c.execute("SELECT * FROM users WHERE email=?", (email,))
            st.session_state.user = c.fetchone()
            st.success("Registration successful! Redirecting...")
            st.session_state.page = "Home"
    st.markdown("Already have an account? [Login here](#)")
    st.markdown("""</div>""", unsafe_allow_html=True)

def login():
    st.markdown("""<div class='custom-box'>""", unsafe_allow_html=True)
    st.subheader("Login to PMAI")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = c.fetchone()
        if user:
            st.session_state.user = user
            st.success(f"Welcome back, {user[1]}!")
            st.session_state.page = "Home"
        else:
            st.error("Invalid credentials.")
    st.markdown("Don't have an account? [Register here](#)")
    st.markdown("""</div>""", unsafe_allow_html=True)

def logout():
    st.session_state.user = None
    st.session_state.page = "Login"
    st.experimental_rerun()

# ========================== CHAT ==============================
def chat():
    st.subheader("Talk to PMAI")
    lang = st.selectbox("Language", ["English", "Pidgin"], key="lang")
    mode = st.selectbox("Assistant Mode", ["Chatbox", "Scam/Email Checker", "Academic Assistant", "Business Helper", "Cybersecurity Advisor"], key="mode")

    st.session_state.chatbox = st.text_area("Type your message:", value=st.session_state.chatbox, key="input_text")

    if st.button("Send") or st.session_state.get("send_on_enter"):
        user_input = st.session_state.chatbox.strip()
        if user_input:
            st.session_state.chatbox = ""
            if mode == "Scam/Email Checker":
                reply = scam_checker_api(user_input)
            else:
                if lang == "Pidgin":
                    prompt = f"You be smart AI wey sabi yarn for pidgin. Person talk say: '{user_input}'"
                else:
                    prompt = f"You are a smart AI. The user said: '{user_input}'"
                reply = get_response(prompt)

            st.markdown(f"<div class='response-block'><b>PMAI:</b> {reply}</div>", unsafe_allow_html=True)
            if st.session_state.user:
                save_message(st.session_state.user[0], mode, user_input, reply)

# ========================== ROUTING ==============================
if "page" not in st.session_state:
    st.session_state.page = "Welcome"

if st.session_state.page == "Welcome" and st.session_state.show_welcome:
    welcome()
elif st.session_state.page == "Register":
    register()
elif st.session_state.page == "Login":
    login()
elif st.session_state.page == "Home":
    chat()

# ========================== FOOTER ==============================
st.markdown("---")
st.markdown("""
<div style='text-align: center; font-size: 16px;'>
    <strong>Developed by:</strong> Abubakar Muhammad Magami<br>
    <strong>Email:</strong> magamiabu@gmail.com<br>
    <strong>Fellow ID:</strong> FE/23/75909764<br>
    <strong>Project:</strong> 3MTT Knowledge Showcase - Cohort 3
</div>
""", unsafe_allow_html=True)
