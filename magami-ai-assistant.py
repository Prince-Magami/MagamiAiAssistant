import streamlit as st
from cohere import Client
from random import choice
import uuid

cohere_api_key = st.secrets["cohere_api_key"]
co = Client(cohere_api_key)

# Session state initialization for multiple user sessions and chat histories
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Language options
languages = ["Pidgin English", "English"]

# Modes of the assistant
modes = [
    "Scam/Email Checker",
    "Emotional Advice Chat",
    "Business Helper",
    "Cybersecurity Advisor",
    "General Chatbox"
]

# Large library of fallback replies for off-topic or unknown questions
fallback_replies = [
    "Sorry o, I no sabi that one well well. Try ask me something wey relate.",
    "Hmm, I no get answer to that matter. Abeg try ask wetin relate.",
    "Omo, dat one pass my hand. Make we yarn about something else.",
    "Wahala dey to understand dat one. Abeg make we focus on the correct topic.",
    "I no fit answer dat one now. Try ask me question about business, cyber, or emotions."
    # (Add many more to reach your desired size, or generate dynamically)
]

# Expanded emotional categories & sample diverse replies
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
    # Add more emotions and replies as needed
}

# Business tips samples (should be large in real app)
business_tips = [
    "Know your customer well, e important for business success.",
    "Always dey plan ahead and manage your money carefully.",
    "Use social media to promote your business for free.",
    "Try small small product testing before full launch.",
    "Customer service fit make or break your business."
]

# Cybersecurity tips samples
cybersecurity_tips = [
    "Never share your passwords with anybody.",
    "Always update your software to avoid hackers.",
    "Use strong passwords with letters, numbers and symbols.",
    "Beware of phishing emails, no click suspicious links.",
    "Backup your important files regularly."
]

# Function to generate AI response via Cohere generate endpoint
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

# Function to get a fallback response randomly
def get_fallback_response():
    return choice(fallback_replies)

# UI layout and logic

st.set_page_config(page_title="Prince Magami AI Assistant", page_icon="🤖", layout="centered")

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

st.title("Prince Magami AI Assistant & Chatbox")
st.markdown("FE/23/75909764")
st.markdown("3MTT NIGERIA | COHORT 3 | KNOWLEDGE SHOWCASE")
st.markdown("By Abubakar Muhammad Magami")
st.markdown("magamiabu@gmail.com")
st.markdown("---")

# Short description about AI scope
st.info("""
**What this AI can do:**  
- Detect scams in emails and links  
- Give emotional support & advice in Pidgin or English  
- Offer tailored business ideas & strategies for Nigerian small businesses  
- Provide cyber security awareness & tips  
- General chat with fun and serious replies  

**What it cannot do:**  
- Provide professional medical, legal, or financial advice  
- Answer unrelated or offensive questions (it will alert you)  
- Replace human experts or therapists
""")

# Language selector
lang = st.selectbox("Choose language: ", languages)

# Mode selector
mode = st.selectbox("Choose mode: ", modes)

# User input area (text area with send button, enter inserts newline)
user_input = st.text_area("Type your message:", height=100, key="input_area")

send = st.button("Send")

if send and user_input.strip() != "":
    # Format prompt based on mode and language
    # Also handle expanded libraries and multi-answer style with randomization
    
    prompt = ""
    user_text = user_input.strip()

    # Build prompts differently per mode + language
    if mode == "Scam/Email Checker":
        if lang == "Pidgin English":
            prompt = f"You be scam detector. Check if this is scam: '{user_text}'. Explain in Pidgin."
        else:
            prompt = f"You are a scam detector. Check if this is a scam: '{user_text}'. Explain in clear English."

    elif mode == "Emotional Advice Chat":
        # Detect emotion keywords roughly and pick category; expand with more emotions & responses in real app
        lowered = user_text.lower()
        emotion_key = None
        for emo in emotion_responses:
            if emo in lowered:
                emotion_key = emo
                break
        if not emotion_key:
            emotion_key = "idk"

        # Random emotional response from category
        response_list = emotion_responses.get(emotion_key, emotion_responses["idk"])
        random_reply = choice(response_list)
        
        if lang == "Pidgin English":
            prompt = f"You be emotional support AI wey dey talk Pidgin. Person talk say: '{user_text}'. Advice am well. Also add this reply: '{random_reply}'."
        else:
            prompt = f"You are an emotional support AI. Person says: '{user_text}'. Give thoughtful advice in English. Also add this reply: '{random_reply}'."

    elif mode == "Business Helper":
        if lang == "Pidgin English":
            prompt = f"You be business advisor for small Nigerian business. User talk say: '{user_text}'. Give Pidgin business ideas, strategies, and advice."
        else:
            prompt = f"You are a business advisor for small Nigerian businesses. User says: '{user_text}'. Give clear English business strategies and advice."

    elif mode == "Cybersecurity Advisor":
        if lang == "Pidgin English":
            prompt = f"You be cybersecurity expert wey sabi advise Nigerians. User ask: '{user_text}'. Give Pidgin cybersecurity tips and awareness."
        else:
            prompt = f"You are a cybersecurity expert advising Nigerians. User says: '{user_text}'. Give cybersecurity tips and awareness in English."

    elif mode == "General Chatbox":
        # Add funny and varied replies for general chit-chat
        funny_replies = [
            "You dey funny o!",
            "Chai, you get sense well!",
            "I dey hear you, make we yarn more.",
            "No wahala, I dey here gidigba for you.",
            "Your own sabi, I go try follow you waka."
        ]
        random_funny = choice(funny_replies)
        if lang == "Pidgin English":
            prompt = f"You be friendly chat AI wey sabi Pidgin. User talk: '{user_text}'. Reply well, add dis funny line: '{random_funny}'."
        else:
            prompt = f"You are a friendly chatbot. User says: '{user_text}'. Reply kindly in English. Add this funny line: '{random_funny}'."

    else:
        prompt = ""

    # Generate AI response from Cohere
    if prompt:
        ai_response = get_cohere_response(prompt)

        # If AI response seems empty or error, use fallback
        if len(ai_response) < 10 or "error" in ai_response.lower():
            ai_response = get_fallback_response()

        # Append to chat history
        st.session_state.chat_history.append(("You", user_text))
        st.session_state.chat_history.append(("Magami AI", ai_response))

        # Clear input box
        st.session_state.input_area = ""

# Show chat history messages
for speaker, message in st.session_state.chat_history:
    if speaker == "You":
        st.markdown(f"**You:** {message}")
    else:
        st.markdown(f"**Magami AI:** {message}")

