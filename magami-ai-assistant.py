import streamlit as st
from cohere import Client
from random import choice
import uuid
import sqlite3
import datetime
import requests
import json
import pyttsx3
import speech_recognition as sr
from streamlit_option_menu import option_menu

import os
use_voice = not os.environ.get("STREAMLIT_CLOUD")
if use_voice:
    import pyttsx3
    engine = pyttsx3.init()


# ========================== DATABASE SETUP ==========================
conn = sqlite3.connect("pmai_users.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, username TEXT, email TEXT, password TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS messages (user_id TEXT, mode TEXT, message TEXT, response TEXT, timestamp TEXT, rating TEXT)''')
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

# ========================== API & ENGINE ===========================
cohere_api_key = st.secrets["cohere_api_key"]
co = Client(cohere_api_key)
engine = pyttsx3.init()

# ========================== APP CONFIGURATION =============================
st.set_page_config(page_title="PMAI - Prince Magami AI Assistant", page_icon="🤖", layout="wide")

with st.sidebar:
    selected = option_menu("PMAI Menu", ["Home", "Login", "Register", "Admin Panel", "Analytics"],
        icons=['house', 'box-arrow-in-right', 'person-plus', 'shield-lock', 'bar-chart'],
        menu_icon="robot", default_index=0)

# ========================== LOGO AND STYLES ========================
st.markdown("""
<style>
.logo-container {
    text-align: center;
    margin-top: 20px;
    margin-bottom: 20px;
}
.logo-text {
    font-size: 36px;
    font-weight: bold;
    color: #0072C6;
}
.response-block {
    background-color: #f0f8ff;
    border-left: 5px solid #0072C6;
    padding: 10px;
    margin-bottom: 10px;
    border-radius: 10px;
}
</style>
<div class='logo-container'>
    <div class='logo-text'>🤖 PMAI - Prince Magami AI Assistant</div>
</div>
""", unsafe_allow_html=True)

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

def speak(text):
    engine.say(text)
    engine.runAndWait()

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


def save_message(user_id, mode, message, response, rating=None):
    timestamp = str(datetime.datetime.now())
    c.execute("INSERT INTO messages (user_id, mode, message, response, timestamp, rating) VALUES (?, ?, ?, ?, ?, ?)",
              (user_id, mode, message, response, timestamp, rating))
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

if use_voice:
    engine.say(response)
    engine.runAndWait()


# ========================== AUTH SYSTEM ============================
def register():
    st.subheader("Create New Account")
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Register"):
        user_id = str(uuid.uuid4())
        c.execute("INSERT INTO users (id, username, email, password) VALUES (?, ?, ?, ?)",
                  (user_id, username, email, password))
        conn.commit()
        st.success("Registered successfully! Please login.")

def login():
    st.subheader("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = c.fetchone()
        if user:
            st.session_state.user = user
            st.success(f"Welcome back, {user[1]}!")
        else:
            st.error("Invalid credentials.")

# ========================== MAIN CHAT HOME =========================
def main_app():
    st.subheader("Talk to PMAI")

    languages = ["English", "Pidgin English"]
    modes = ["Chatbox", "Scam/Email Checker", "Exam/Academic Assistant", "Business Helper", "Cybersecurity Advisor"]

    lang = st.selectbox("Language", languages, index=0)
    mode = st.selectbox("Assistant Mode", modes)
    audio_btn = st.button("🎤 Speak Instead")

    if audio_btn:
        user_input = record_audio()
    else:
        user_input = st.text_area("Type your message (Press Enter to send):", key="input_area")

    if user_input and st.session_state.user:
        if mode == "Scam/Email Checker":
            reply = scam_checker_api(user_input)
        elif mode == "Exam/Academic Assistant":
            prompt = f"You are an academic assistant for students in Nigeria (secondary and university level). Student asks: '{user_input}'. Reply with a helpful, intelligent answer."
            reply = get_response(prompt)
        elif mode == "Business Helper":
            prompt = f"You are a Nigerian business advisor. User says: '{user_input}'. Provide smart, practical strategies."
            reply = get_response(prompt)
        elif mode == "Cybersecurity Advisor":
            prompt = f"You are a cybersecurity expert for Nigerian users. They say: '{user_input}'. Provide tips or guidance."
            reply = get_response(prompt)
        elif mode == "Chatbox":
            prompt = f"You are a witty and smart AI chatbot. Chat with the user naturally. They said: '{user_input}'."
            reply = get_response(prompt)
        else:
            reply = "Unknown mode."

        speak(reply)
        st.markdown(f"<div class='response-block'><b>PMAI:</b> {reply}</div>", unsafe_allow_html=True)

        rating = st.radio("Was this helpful?", ["👍🏽 Yes", "👎🏽 No"], horizontal=True)
        save_message(st.session_state.user[0], mode, user_input, reply, rating)

# ========================== ADMIN PANEL ============================
def admin_panel():
    st.subheader("Admin Panel - Prince Magami")
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM messages")
    total_msgs = c.fetchone()[0]
    st.metric("Total Registered Users", total_users)
    st.metric("Total Messages Exchanged", total_msgs)

    with st.expander("View All Messages"):
        c.execute("SELECT * FROM messages ORDER BY timestamp DESC LIMIT 50")
        data = c.fetchall()
        for row in data:
            st.markdown(f"**Mode:** {row[1]} | **Input:** {row[2]} | **Response:** {row[3]} | **Rating:** {row[5]} | {row[4]}")

# ========================== ANALYTICS ==============================
def analytics():
    st.subheader("Usage Analytics")
    c.execute("SELECT mode, COUNT(*) FROM messages GROUP BY mode")
    data = c.fetchall()
    st.bar_chart({mode: count for mode, count in data})

# ========================== ROUTER ================================
if selected == "Home" and st.session_state.user:
    main_app()
elif selected == "Login":
    login()
elif selected == "Register":
    register()
elif selected == "Admin Panel" and st.session_state.user and st.session_state.user[1] == "Magami":
    admin_panel()
elif selected == "Analytics" and st.session_state.user:
    analytics()
else:
    st.warning("Please login to access this section.")

# ========================== FOOTER INFO ==========================
st.markdown("---", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; font-size: 16px;'>
    <strong>Developed by:</strong> Abubakar Muhammad Magami<br>
    <strong>Email:</strong> magamiabu@gmail.com<br>
    <strong>Fellow ID:</strong> FE/23/75909764<br>
    <strong>Project:</strong> 3MTT Knowledge Showcase - Cohort 3
</div>
""", unsafe_allow_html=True)


