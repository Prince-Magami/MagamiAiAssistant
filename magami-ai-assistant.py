import streamlit as st
import streamlit.components.v1 as components
from cohere import Client
import uuid, sqlite3, datetime, requests, json
from streamlit_option_menu import option_menu
from random import choice

# =================== CONFIG =====================
st.set_page_config(page_title="PMAI - Prince Magami AI Assistant", page_icon="🤖", layout="wide")
co = Client(st.secrets["cohere_api_key"])
conn = sqlite3.connect("pmai_users.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, username TEXT, email TEXT, password TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS messages (user_id TEXT, mode TEXT, message TEXT, response TEXT, timestamp TEXT)''')
conn.commit()

# =================== STATE =====================
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "user" not in st.session_state:
    st.session_state.user = None

# =================== STYLE =====================
st.markdown("""
    <style>
    body, .stApp {
        background-color: #0c1a2b;
        color: #ffffff;
        font-family: 'Segoe UI', sans-serif;
    }
    .title {
        text-align: center;
        font-size: 36px;
        color: #1e90ff;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .response-block {
        background-color: #122c47;
        color: #fff;
        padding: 15px;
        border-left: 5px solid #1e90ff;
        border-radius: 8px;
        margin-bottom: 15px;
        font-size: 16px;
    }
    .form-box {
        background-color: #112233;
        padding: 30px;
        border-radius: 10px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }
    input, textarea {
        background-color: #0c1a2b !important;
        color: #ffffff !important;
        border: 1px solid #1e90ff;
    }
    </style>
""", unsafe_allow_html=True)

# =================== SPEAK =====================
def speak_with_browser(text):
    escaped = text.replace("'", "\'")
    components.html(f"""
        <script>
            var msg = new SpeechSynthesisUtterance('{escaped}');
            window.speechSynthesis.speak(msg);
        </script>
    """, height=0)

# =================== AI =====================
def get_response(prompt):
    try:
        result = co.generate(
            model="command-r-plus",
            prompt=prompt,
            max_tokens=250,
            temperature=0.7
        )
        return result.generations[0].text.strip()
    except Exception as e:
        return f"Error: {str(e)}"

def scam_checker_api(text):
    try:
        import urllib.parse
        base_url = "https://ipqualityscore.com/api/json/url/"
        api_key = st.secrets["ipqs_api_key"]
        url = urllib.parse.quote(text.strip())
        response = requests.get(f"{base_url}{api_key}/{url}").json()
        if response.get("unsafe"):
            return f"⚠️ Warning: Unsafe link. Reason: {response.get('suspicious')}"
        else:
            return "✅ Link appears safe."
    except Exception as e:
        return f"Error: {str(e)}"

# =================== UTIL =====================
def save_message(user_id, mode, msg, res):
    timestamp = str(datetime.datetime.now())
    c.execute("INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?)", (user_id, mode, msg, res, timestamp, ""))
    conn.commit()

# =================== UI BLOCKS =====================
def welcome():
    st.markdown("<div class='title'>🤖 Welcome to PMAI</div>", unsafe_allow_html=True)
    st.info("""
    PMAI is your smart Nigerian AI assistant.
    - 💼 Business support
    - 🛡 Scam & email checker
    - 🎓 Academic help
    - 💬 Smart chat
    - 🔐 Cybersecurity advice

    ⚠ Note: PMAI does not give medical or illegal advice.
    """)

def login():
    st.markdown("<div class='form-box'>", unsafe_allow_html=True)
    st.subheader("🔐 Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = c.fetchone()
        if user:
            st.session_state.user = user
            st.success("Login successful.")
        else:
            st.error("Invalid credentials.")
    st.markdown("</div>", unsafe_allow_html=True)

def register():
    st.markdown("<div class='form-box'>", unsafe_allow_html=True)
    st.subheader("📝 Register")
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Register"):
        if username and email and password:
            user_id = str(uuid.uuid4())
            c.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (user_id, username, email, password))
            conn.commit()
            st.success("Registration complete! Please login.")
        else:
            st.warning("All fields are required.")
    st.markdown("</div>", unsafe_allow_html=True)

def chat():
    st.subheader("🧠 Talk to PMAI")
    modes = ["Chatbox", "Scam/Email Checker", "Exam/Academic Assistant", "Business Helper", "Cybersecurity Advisor"]
    mode = st.selectbox("Choose Mode", modes)
    user_input = st.text_area("Ask PMAI:")
    if user_input:
        if mode == "Scam/Email Checker":
            reply = scam_checker_api(user_input)
        else:
            prompt = f"Mode: {mode}. User said: {user_input}"
            reply = get_response(prompt)
        speak_with_browser(reply)
        st.markdown(f"<div class='response-block'><b>PMAI:</b> {reply}</div>", unsafe_allow_html=True)
        save_message(st.session_state.user[0], mode, user_input, reply)

def admin():
    st.subheader("🔐 Admin Panel")
    c.execute("SELECT COUNT(*) FROM users")
    st.metric("Total Users", c.fetchone()[0])
    c.execute("SELECT COUNT(*) FROM messages")
    st.metric("Messages Exchanged", c.fetchone()[0])

def analytics():
    st.subheader("📊 Analytics")
    c.execute("SELECT mode, COUNT(*) FROM messages GROUP BY mode")
    data = c.fetchall()
    st.bar_chart({row[0]: row[1] for row in data})

# =================== SIDEBAR ROUTER =====================
with st.sidebar:
    menu = ["Welcome", "Login", "Register"] if not st.session_state.user else ["Home", "Analytics", "Logout"]
    if st.session_state.user and st.session_state.user[2] == "magamiabu@gmail.com":
        menu.append("Admin Panel")
    selected = option_menu("PMAI Menu", menu, icons=['house', 'box-arrow-in-right', 'person-plus', 'bar-chart', 'shield-lock'], menu_icon="robot", default_index=0)

# =================== ROUTES =====================
if selected == "Welcome":
    welcome()
elif selected == "Login":
    login()
elif selected == "Register":
    register()
elif selected == "Home":
    chat()
elif selected == "Admin Panel" and st.session_state.user and st.session_state.user[2] == "magamiabu@gmail.com":
    admin()
elif selected == "Analytics":
    analytics()
elif selected == "Logout":
    st.session_state.user = None
    st.success("Logged out successfully")

# =================== FOOTER =====================
st.markdown("""---
<center>
<b>Developed by:</b> Abubakar Muhammad Magami | <b>Email:</b> magamiabu@gmail.com<br>
<b>Project:</b> 3MTT Knowledge Showcase - Cohort 3
</center>
""", unsafe_allow_html=True)
