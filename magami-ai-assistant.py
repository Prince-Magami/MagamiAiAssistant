import streamlit as st
import random
import validators
from huggingface_hub import InferenceClient
from textblob import TextBlob 

# Loads the key from Streamlit secrets
api_key = st.secrets["huggingface"]["api_key"]

# Initialize the Hugging Face client
client = InferenceClient(token=api_key)

# --- Setup ---
st.set_page_config(page_title="Prince Magami AI Assistant", page_icon="🤖", layout="centered")
client = InferenceClient(model="mistralai/Mixtral-8x7B-Instruct-v0.1")

# --- Session State Init ---
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# --- Mode Selection ---
st.title("Magami AI Assistant")
st.markdown("""
#### This AI fit help you check scam links, give emotional support, help your business grow, and teach cybersecurity.
Choose your mode, pick your language (Pidgin or English), and let's go!
""")
mode = st.selectbox("Choose your mode:", [
    "Chatbox Mode",
    "Scam/Email Checker",
    "Emotional Advice",
    "Business Help",
    "Cybersecurity Tips"
])
language = st.radio("Choose your language:", ["English", "Pidgin"])

# --- Function to Query HuggingFace ---
def ask_huggingface(prompt):
    try:
        system_msg = "You are a helpful assistant that speaks {}. Respond to each query with a unique and informative answer. If the query is off-topic, gently inform the user you're not programmed for that.".format(language)
        response = client.text_generation(
            prompt=f"<s>[INST] <<SYS>>\n{system_msg}\n<</SYS>>\n{prompt} [/INST]",
            max_new_tokens=300,
            temperature=0.9,
            top_p=0.95,
            repetition_penalty=1.15
        )
        return response.strip()
    except Exception as e:
        return f"Wahala dey: {str(e)}"

# --- Chatbox Mode ---
if mode == "Chatbox Mode":
    st.subheader("Chat with AI")
    user_input = st.text_area("Type your message:", height=200)
    if st.button("Send") and user_input:
        funny_replies = [
            "Haha! That one burst my brain.",
            "You sharp die!",
            "No be lie, na so e be.",
            "That one na cruise!",
            "I go think am, but you sabi well!"
        ]
        prompt = f"User said: {user_input}. Respond like a funny, helpful AI in {language}."
        answer = ask_huggingface(prompt)
        if any(word in user_input.lower() for word in ["joke", "funny", "laugh"]):
            answer += "\n\n" + random.choice(funny_replies)
        st.session_state.chat_history.append((user_input, answer))

# --- Scam/Email Checker ---
elif mode == "Scam/Email Checker":
    st.subheader("Scam Detector")
    user_input = st.text_area("Paste the email or link you want to check:", height=150)
    if st.button("Scan") and user_input:
        if validators.url(user_input):
            prompt = f"Check if this link is scam: {user_input}. Explain in {language}."
        else:
            prompt = f"Check if this email/text is scam: {user_input}. Explain in {language}."
        answer = ask_huggingface(prompt)
        st.session_state.chat_history.append((user_input, answer))

# --- Emotional Advice ---
elif mode == "Emotional Advice":
    st.subheader("Talk to your AI Buddy")
    feelings = st.text_area("How do you feel?", height=150)
    if st.button("I need advice") and feelings:
        sentiment = TextBlob(feelings).sentiment.polarity
        if sentiment < -0.5:
            tone = "very sad"
        elif sentiment < 0:
            tone = "a bit down"
        elif sentiment > 0.5:
            tone = "very happy"
        else:
            tone = "neutral"
        prompt = f"User feels {tone}. Message: '{feelings}'. Give emotional advice in {language} for someone who feels {tone}."
        answer = ask_huggingface(prompt)
        st.session_state.chat_history.append((feelings, answer))

# --- Business Help ---
elif mode == "Business Help":
    st.subheader("Business Growth Assistant")
    biz_question = st.text_area("What's your business idea or challenge?", height=150)
    if st.button("Give me business tips") and biz_question:
        prompt = f"User asked: '{biz_question}'. Respond with clear Nigerian business strategies and advice in {language}. If unclear, ask for more info."
        answer = ask_huggingface(prompt)
        st.session_state.chat_history.append((biz_question, answer))

# --- Cybersecurity Tips ---
elif mode == "Cybersecurity Tips":
    st.subheader("Cybersecurity Awareness")
    cyber_question = st.text_area("Ask any cybersecurity question or concern:", height=150)
    if st.button("Get cyber advice") and cyber_question:
        prompt = f"User asked about cybersecurity: '{cyber_question}'. Provide detailed local cybersecurity awareness, practices and explanations in {language}."
        answer = ask_huggingface(prompt)
        st.session_state.chat_history.append((cyber_question, answer))

# --- Display Chat History ---
if st.session_state.chat_history:
    st.markdown("---")
    st.markdown("### Chat History")
    for user_msg, ai_reply in reversed(st.session_state.chat_history):
        st.markdown(f"**You:** {user_msg}")
        st.markdown(f"**AI:** {ai_reply}")
