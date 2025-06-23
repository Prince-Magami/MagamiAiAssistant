import streamlit as st
from streamlit_option_menu import option_menu
from cohere import Client
import uuid
import datetime
import sqlite3
import requests
import json
import re

# ========================== CONFIG ==========================
st.set_page_config(page_title="PMAI - AI Assistant", layout="wide")

co = Client(st.secrets["cohere_api_key"])
ipqs_api_key = st.secrets["ipqs_api_key"]
admin_email = "magamiabu@gmail.com"

# ========================== DB INIT ==========================
conn = sqlite3.connect("pmai_users.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT,
    email TEXT,
    password TEXT,
    joined TEXT,
    is_admin INTEGER DEFAULT 0
)''')
c.execute('''CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    mode TEXT,
    lang TEXT,
    prompt TEXT,
    response TEXT,
    timestamp TEXT
)''')
conn.commit()

# ========================== SESSION ==========================
if "user" not in st.session_state:
    st.session_state.user = None
if "lang" not in st.session_state:
    st.session_state.lang = "English"
if "chatbox" not in st.session_state:
    st.session_state.chatbox = ""
if "msg_count" not in st.session_state:
    st.session_state.msg_count = 0

# ========================== UTILS ==========================
def save_user(username, email, password):
    user_id = str(uuid.uuid4())
    joined = str(datetime.datetime.now())
    is_admin = 1 if email == admin_email else 0
    c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)", (user_id, username, email, password, joined, is_admin))
    conn.commit()
    return user_id

def save_message(user_id, mode, lang, prompt, response):
    msg_id = str(uuid.uuid4())
    timestamp = str(datetime.datetime.now())
    c.execute("INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?, ?)", (msg_id, user_id, mode, lang, prompt, response, timestamp))
    conn.commit()

def get_response(prompt):
    try:
        response = co.generate(
            model="command-r-plus",
            prompt=prompt,
            max_tokens=200,
            temperature=0.7
        )
        return response.generations[0].text.strip()
    except Exception as e:
        return f"[Error]: {e}"

def scam_check(text):
    try:
        import urllib.parse
        encoded = urllib.parse.quote(text)
        url = f"https://ipqualityscore.com/api/json/url/{ipqs_api_key}/{encoded}"
        res = requests.get(url)
        data = res.json()
        if data.get("unsafe"):
            return f"🚨 Unsafe Link: {data.get('domain')} flagged as dangerous."
        else:
            return "✅ This link appears safe."
    except Exception as e:
        return f"[API Error]: {e}"

# ========================== PAGES ==========================
def show_logo():
    st.markdown("""
    <div style='font-size:24px; font-weight:bold; color:#1ecbe1; text-shadow: 0 0 5px #00ffff;'>
        🤖 PMAI
    </div>""", unsafe_allow_html=True)

def welcome():
    show_logo()
    st.title("Welcome to PMAI")
    st.write("Your smart AI assistant for academic support, cybersecurity, scam detection & more.")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Register"):
            st.session_state.page = "Register"
    with col2:
        if st.button("Login"):
            st.session_state.page = "Login"
    with col3:
        if st.button("Continue without Account"):
            st.session_state.user = None
            st.session_state.page = "Chat"

def register():
    show_logo()
    st.subheader("Create an Account")
    with st.form("register_form"):
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm Password", type="password")
        submit = st.form_submit_button("Register")
        if submit:
            if not username or not email or not password or not confirm:
                st.warning("Please fill all fields.")
            elif password != confirm:
                st.warning("Passwords do not match.")
            elif len(password) < 8 or not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
                st.warning("Password must be 8+ characters and include letters and numbers.")
            else:
                save_user(username, email, password)
                c.execute("SELECT * FROM users WHERE email=?", (email,))
                st.session_state.user = c.fetchone()
                st.success("Account created successfully. Taking you to home page...")
                st.session_state.page = "Chat"

def login():
    show_logo()
    st.subheader("Login")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        if submit:
            c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
            user = c.fetchone()
            if user:
                st.session_state.user = user
                st.success("Welcome back!")
                st.session_state.page = "Chat"
            else:
                st.error("Invalid credentials")
    st.markdown("Don't have an account? [Register here](#)", unsafe_allow_html=True)

def chat():
    show_logo()
    user = st.session_state.user
    st.subheader("Talk to PMAI")
    if st.button("Logout"):
        st.session_state.user = None
        st.session_state.page = "Login"

    lang_toggle = st.radio("Language", ["English", "Pidgin"], horizontal=True)
    st.session_state.lang = lang_toggle
    mode = st.selectbox("Mode", ["Chatbox", "Scam/Email Checker", "Exam/Academic Assistant", "Business Helper", "Cybersecurity Advisor"])

    with st.form("chat_form"):
        st.session_state.chatbox = st.text_area("Your Message", value=st.session_state.chatbox, height=100)
        submitted = st.form_submit_button("Send")
        if submitted and st.session_state.chatbox:
            if not user and st.session_state.msg_count >= 10:
                st.warning("You have reached the message limit. Please register to continue chatting.")
                return

            user_input = st.session_state.chatbox.strip()
            st.session_state.chatbox = ""  # Clear input

            if mode == "Scam/Email Checker":
                reply = scam_check(user_input)
            else:
                if st.session_state.lang == "Pidgin":
                    user_input = f"Explain in Nigerian pidgin: {user_input}"
                reply = get_response(user_input)

            with st.container():
                st.markdown(f"""
                    <div style='background:#fff;color:#000;padding:1rem;border-radius:8px;'>
                        <b>You:</b> {user_input}<br>
                        <b>PMAI:</b> {reply}
                    </div>
                """, unsafe_allow_html=True)

            if user:
                save_message(user[0], mode, st.session_state.lang, user_input, reply)
            else:
                st.session_state.msg_count += 1

def analytics():
    st.subheader("Admin Analytics")
    c.execute("SELECT COUNT(*) FROM users")
    st.metric("Total Registered Users", c.fetchone()[0])

    c.execute("SELECT email FROM users")
    st.write("Registered Emails:")
    st.json([e[0] for e in c.fetchall()])

    c.execute("SELECT mode, COUNT(*) FROM messages GROUP BY mode")
    st.bar_chart(dict(c.fetchall()))

    with st.expander("All Messages"):
        c.execute("SELECT * FROM messages ORDER BY timestamp DESC LIMIT 100")
        for msg in c.fetchall():
            st.markdown(f"**{msg[6]}** | Mode: {msg[2]} | {msg[3]}<br><b>Q:</b> {msg[4]}<br><b>A:</b> {msg[5]}", unsafe_allow_html=True)

def profile():
    user = st.session_state.user
    st.subheader("Profile Settings")
    st.write(f"**Username:** {user[1]}")
    st.write(f"**Email:** {user[2]}")
    st.write(f"**Joined:** {user[4]}")

    if st.button("Delete Account"):
        c.execute("DELETE FROM users WHERE email=?", (user[2],))
        conn.commit()
        st.success("Account deleted. Reloading...")
        st.session_state.user = None
        st.session_state.page = "Welcome"

# ========================== ROUTING ==========================
if "page" not in st.session_state:
    st.session_state.page = "Welcome"

page = st.session_state.page

with st.sidebar:
    show_logo()
    if st.session_state.user:
        menu = ["Chat", "Profile"]
        if st.session_state.user[2] == admin_email:
            menu.append("Analytics")
        choice = option_menu("Menu", menu)
        st.session_state.page = choice
    else:
        st.session_state.page = page

if page == "Welcome":
    welcome()
elif page == "Register":
    register()
elif page == "Login":
    login()
elif page == "Chat":
    chat()
elif page == "Analytics" and st.session_state.user and st.session_state.user[2] == admin_email:
    analytics()
elif page == "Profile":
    profile()

# ========================== FOOTER ==========================
st.markdown("""
---
<div style='text-align: center; font-size: 14px;'>
<b>Abubakar Muhammad Magami</b><br>
<b>Email:</b> magamiabu@gmail.com<br>
<b>Fellow ID:</b> FE/23/75909764<br>
<b>Project:</b> 3MTT Knowledge Showcase (Cohort 3)
</div>
""", unsafe_allow_html=True)
