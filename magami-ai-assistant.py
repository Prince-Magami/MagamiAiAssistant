import streamlit as st
from cohere import Client
from random import choice
import uuid

# --- Cohere API Key ---
cohere_api_key = st.secrets["cohere_api_key"]
co = Client(cohere_api_key)

# --- Session State Initialization ---
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "chat_histories" not in st.session_state:
    st.session_state.chat_histories = {}

if st.session_state.session_id not in st.session_state.chat_histories:
    st.session_state.chat_histories[st.session_state.session_id] = []

chat_history = st.session_state.chat_histories[st.session_state.session_id]

# --- Options ---
languages = ["Pidgin English", "English"]
modes = [
    "Scam/Email Checker",
    "Emotional Advice Chat",
    "Business Helper",
    "Cybersecurity Advisor",
    "General Chatbox"
]

# --- Fallback Replies ---
fallback_replies = [
    "Sorry o, I no sabi that one well well. Try ask me something wey relate.",
    "Hmm, I no get answer to that matter. Abeg try ask wetin relate.",
    "Omo, dat one pass my hand. Make we yarn about something else.",
    "Wahala dey to understand dat one. Abeg make we focus on the correct topic.",
    "I no fit answer dat one now. Try ask me question about business, cyber, or emotions."
]

# --- Emotional Replies ---
emotion_responses = {
    "happy": [
        "You dey shine! Keep the good vibes rolling.",
        "That joy dey sweet like sugar, no let am go.",
        "Happy days ahead, my guy!"
    ],
    "nervous": [
        "No worry, e normal to feel nervous sometimes.",
        "Take deep breaths, you go better.",
        "Calm down, everything go smooth."
    ],
    "scared": [
        "No fear, better days dey come.",
        "I dey here for you, no be only you.",
        "Face am small small, you fit handle am."
    ],
    "excited": [
        "Wetin dey burst your brain? Good excitement be dat!",
        "Make you enjoy am well well!",
        "Excitement na better thing, channel am well."
    ],
    "anxious": [
        "I understand your feelings, try relax small.",
        "Everything go dey alright, one step at a time.",
        "Focus on the positive things."
    ],
    "depressed": [
        "I dey with you. No be the end, better days dey.",
        "Try talk to someone close or a pro.",
        "Small small, things go improve."
    ],
    "idk": [
        "No wahala if you no know, we dey learn together.",
        "Try put mouth for wetin dey happen around you.",
        "Ask more questions, you go sabi soon."
    ]
}

# --- Business & Cyber Tips ---
business_tips = [
    "Know your customer well, e important for business success.",
    "Always dey plan ahead and manage your money carefully.",
    "Use social media to promote your business for free.",
    "Try small small product testing before full launch.",
    "Customer service fit make or break your business."
]

cybersecurity_tips = [
    "Never share your passwords with anybody.",
    "Always update your software to avoid hackers.",
    "Use strong passwords with letters, numbers and symbols.",
    "Beware of phishing emails, no click suspicious links.",
    "Backup your important files regularly."
]

# --- AI Response Generator ---
def get_cohere_response(prompt):
    try:
        response = co.generate(
            model="xlarge",
            prompt=prompt,
            max_tokens=250,
            temperature=0.75,
            k=0,
            stop_sequences=["--"],
            return_likelihoods="NONE"
        )
        return response.generations[0].text.strip()
    except Exception as e:
        return f"Wahala dey: {str(e)}"

# --- Fallback ---
def get_fallback_response():
    return choice(fallback_replies)

# --- Streamlit UI ---
st.set_page_config(page_title="Magami AI Assistant", page_icon="🤖", layout="centered")

st.markdown("""
<style>
body {
    background-color: #f5f5f7;
    color: #333;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
.stButton>button {
    background-color: #0072C6;
    color: white;
    border-radius: 8px;
    padding: 8px 16px;
}
.stButton>button:hover {
    background-color: #005A9E;
}
.stTextArea textarea, .stTextInput input {
    border-radius: 8px;
    padding: 10px;
}
</style>
""", unsafe_allow_html=True)

st.title("Magami AI Assistant & Chatbox")
st.markdown("**By Abubakar Muhammad Magami**")
st.markdown("---")

st.info("""
### What this AI can do:
- Detect scams in emails and links  
- Give emotional support & advice in Pidgin or English  
- Offer business ideas & strategies for Nigerian small businesses  
- Provide cyber security awareness & tips  
- Fun general chat

**Note:**  
It cannot give medical/legal/financial advice or replace real experts.
""")

lang = st.selectbox("Choose language:", languages)
mode = st.selectbox("Choose mode:", modes)

user_input = st.text_area("Type your message:", height=100, key="input_area")
send = st.button("Send")

if send and user_input.strip() != "":
    user_text = user_input.strip()
    prompt = ""

    if mode == "Scam/Email Checker":
        prompt = f"You be scam detector. Check if this is scam: '{user_text}'. Explain in {'Pidgin' if lang == 'Pidgin English' else 'English'}."

    elif mode == "Emotional Advice Chat":
        emotion_key = next((e for e in emotion_responses if e in user_text.lower()), "idk")
        random_reply = choice(emotion_responses[emotion_key])
        prompt = f"You be emotional support AI. User talk: '{user_text}'. Advice in {lang}. Add this: '{random_reply}'."

    elif mode == "Business Helper":
        prompt = f"You be business advisor. User talk: '{user_text}'. Give {lang} strategies for small Nigerian business."

    elif mode == "Cybersecurity Advisor":
        prompt = f"You be cyber security expert. User talk: '{user_text}'. Give {lang} tips and awareness."

    elif mode == "General Chatbox":
        funny_line = choice([
            "You dey funny o!",
            "Chai, you get sense well!",
            "I dey hear you, make we yarn more.",
            "No wahala, I dey here gidigba for you.",
            "Your own sabi, I go try follow you waka."
        ])
        prompt = f"You be friendly chat AI. User talk: '{user_text}'. Reply in {lang}. Add this line: '{funny_line}'."

    ai_response = get_cohere_response(prompt)
    if len(ai_response) < 10 or "error" in ai_response.lower():
        ai_response = get_fallback_response()

    chat_history.append(("You", user_text))
    chat_history.append(("Magami AI", ai_response))
    st.session_state.input_area = ""

# --- Display Chat History ---
for speaker, message in chat_history:
    st.markdown(f"**{speaker}**: {message}")
