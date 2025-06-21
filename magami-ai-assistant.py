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

chat_history = st.session_state.chat_histories[st.session_state.session_id]

# ========================== THEMING ===========================
st.markdown("""
    <style>
    :root {
        --bg-color: #ffffff;
        --text-color: #000000;
        --response-bg: #000000;
        --response-text: #ffffff;
    }
    .dark-theme :root {
        --bg-color: #0e1117;
        --text-color: #ffffff;
        --response-bg: #ffffff;
        --response-text: #000000;
    }
    body, .stApp {
        background-color: var(--bg-color);
        color: var(--text-color);
    }
    .response-block {
        background-color: var(--response-bg);
        color: var(--response-text);
        border-left: 5px solid #0072C6;
        padding: 15px;
        margin-top: 10px;
        margin-bottom: 10px;
        border-radius: 10px;
        font-size: 16px;
        word-wrap: break-word;
    }
    .stButton > button {
        font-size: 18px;
        padding: 10px;
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# ========================== API & CONFIG ===========================
st.set_page_config(page_title="PMAI - Prince Magami AI Assistant", page_icon="🤖", layout="wide")
cohere_api_key = st.secrets["cohere_api_key"]
co = Client(cohere_api_key)

# ========================== SIDEBAR ==========================
with st.sidebar:
    if st.session_state.user and st.session_state.user[2] == "magamiabu@gmail.com":
        menu_items = ["Home", "Logout", "Admin Panel", "Analytics", "Theme"]
    else:
        menu_items = ["Home", "Login", "Register", "Theme"]
    selected = option_menu("PMAI Menu", menu_items,
        icons=['house', 'box-arrow-left', 'shield-lock', 'bar-chart', 'brightness-high'],
        menu_icon="robot", default_index=menu_items.index("Register"))

# ========================== THEME TOGGLE ==========================
selected_theme = st.sidebar.radio("Choose Theme", ["Light", "Dark"])
if selected_theme == "Dark":
    components.html("""<script>document.body.classList.add('dark-theme');</script>""", height=0)
else:
    components.html("""<script>document.body.classList.remove('dark-theme');</script>""", height=0)

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

def save_message(user_id, mode, message, response):
    timestamp = str(datetime.datetime.now())
    c.execute("INSERT INTO messages (user_id, mode, message, response, timestamp) VALUES (?, ?, ?, ?, ?)",
              (user_id, mode, message, response, timestamp))
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

# ========================== AUTH ==============================
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
        st.markdown("Already have an account? Click the sidebar and go to Login.")

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

def logout():
    st.session_state.user = None
    st.experimental_rerun()

# ========================== MAIN CHAT ==============================
def main_app():
    st.subheader("Talk to PMAI")
    voice_enabled = st.checkbox("🔊 Enable Voice")
    languages = ["English", "Pidgin English"]
    modes = ["Chatbox", "Scam/Email Checker", "Exam/Academic Assistant", "Business Helper", "Cybersecurity Advisor"]

    lang = st.selectbox("Language", languages)
    mode = st.selectbox("Assistant Mode", modes)
    audio_btn = st.button("🎤 Speak Instead")

    if audio_btn:
        user_input = record_audio()
    else:
        user_input = st.text_area("Type your message:")

    if user_input:
        if mode == "Scam/Email Checker":
            reply = scam_checker_api(user_input)
        else:
            prompt = f"You are a helpful AI. The user said: '{user_input}'"
            reply = get_response(prompt)

        if voice_enabled:
            speak_with_browser(reply)

        st.markdown(f"<div class='response-block'><b>PMAI:</b> {reply}</div>", unsafe_allow_html=True)

        if st.session_state.user:
            save_message(st.session_state.user[0], mode, user_input, reply)

# ========================== ADMIN ==============================
def admin_panel():
    st.subheader("Admin Panel - Prince Magami")
    c.execute("SELECT COUNT(*) FROM users")
    st.metric("Total Registered Users", c.fetchone()[0])
    c.execute("SELECT COUNT(*) FROM messages")
    st.metric("Total Messages", c.fetchone()[0])

    with st.expander("Latest Messages"):
        c.execute("SELECT * FROM messages ORDER BY timestamp DESC LIMIT 50")
        for row in c.fetchall():
            st.markdown(f"**{row[4]}** | Mode: {row[1]} | <br><b>You:</b> {row[2]}<br><b>PMAI:</b> {row[3]}", unsafe_allow_html=True)

# ========================== ANALYTICS ==============================
def analytics():
    st.subheader("Usage Analytics")
    c.execute("SELECT mode, COUNT(*) FROM messages GROUP BY mode")
    data = c.fetchall()
    st.bar_chart({mode: count for mode, count in data})

# ========================== ROUTING ==============================
if selected == "Home":
    main_app()
elif selected == "Login":
    login()
elif selected == "Register":
    register()
elif selected == "Logout":
    logout()
elif selected == "Admin Panel" and st.session_state.user and st.session_state.user[2] == "magamiabu@gmail.com":
    admin_panel()
elif selected == "Analytics" and st.session_state.user and st.session_state.user[2] == "magamiabu@gmail.com":
    analytics()
else:
    st.info("Please register or login to use the app.")

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
