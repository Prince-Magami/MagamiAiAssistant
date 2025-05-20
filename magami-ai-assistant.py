import streamlit as st
import requests
import validators

# App title and config
st.set_page_config(page_title="Magami AI Assistant & Chatbox")
st.title("Magami AI Assistant & Chatbox")
st.markdown("""
**By Abubakar Muhammad Magami**  
Email: magamiabu@gmail.com  
Fellow ID: FE/23/75909764  
Cohort 3 - 3MTT Knowledge Showcase
""")

# API info
API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-large"
headers = {"Authorization": "Bearer YOUR_HUGGINGFACE_API_KEY"}

# Helper function to query Hugging Face
def query_huggingface(prompt):
    try:
        response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
        return response.json()[0]['generated_text']
    except Exception as e:
        return f"Wahala dey: {str(e)}"

# Intelligent fallback for off-topic or confusing queries
def handle_fallback(prompt):
    fallback_keywords = [
        "weather", "celebrity", "joke", "game", "sports", "who is", "what is", "movie", "song",
        "define", "explain", "AI girlfriend", "crypto", "hack", "code", "how do I"
    ]
    polite_responses = [
        "I no fit answer this one. Try ask me sometin wey concern business, cybersecurity or emotions.",
        "This matter no dey my area. Ask me better question about feelings, scam, or biz tips.",
        "Abeg rephrase your question. I sabi business, emotions, or cyber advice well well."
    ]
    if any(keyword in prompt.lower() for keyword in fallback_keywords):
        return polite_responses[len(prompt) % len(polite_responses)]
    return None

# Mode selection
mode = st.sidebar.selectbox("Select Mode", [
    "Emotional Advice Chat",
    "Business Helper",
    "Cybersecurity Tips",
    "Scam/Email Checker"
])

# Emotional Mode
if mode == "Emotional Advice Chat":
    st.subheader("Talk to your AI Buddy")
    st.write("Feel free to share how you dey feel")
    feelings = st.text_area("How you dey feel?")
    if st.button("Send") and feelings:
        emotion_tags = ["sad", "happy", "nervous", "excited", "angry", "scared", "confused", "depressed", "anxious", "I don't know"]
        detected_emotion = next((tag for tag in emotion_tags if tag in feelings.lower()), "")
        prompt = f"User say: '{feelings}'. Give emotional advice in Pidgin English. Emotion: {detected_emotion}"
        fallback = handle_fallback(feelings)
        result = fallback if fallback else query_huggingface(prompt)
        st.info(result)

# Business Mode
elif mode == "Business Helper":
    st.subheader("Na Business Matter")
    biz_question = st.text_area("Tell me wetin concern your business")
    if st.button("Send") and biz_question:
        prompt = f"Person wan start or run business for Nigeria. E talk say: '{biz_question}'. Give helpful Pidgin advice with local examples and clear steps."
        fallback = handle_fallback(biz_question)
        result = fallback if fallback else query_huggingface(prompt)
        st.success(result)

# Cybersecurity Mode
elif mode == "Cybersecurity Tips":
    st.subheader("Cybersecurity Advice")
    cyber_question = st.text_area("Wetin you wan know for cyber matter?")
    if st.button("Send") and cyber_question:
        prompt = f"User get question about cybersecurity. E say: '{cyber_question}'. Give practical Pidgin cyber tips for normal Nigerian business or student."
        fallback = handle_fallback(cyber_question)
        result = fallback if fallback else query_huggingface(prompt)
        st.success(result)

# Scam Detection Mode
elif mode == "Scam/Email Checker":
    st.subheader("Scam Detector")
    scam_input = st.text_area("Paste email or link wey you wan check:")
    if st.button("Scan am!") and scam_input:
        if validators.url(scam_input):
            prompt = f"This link fit be scam? Link: {scam_input}. Explain why or why not in Pidgin."
        else:
            prompt = f"This email or text fit be scam? Text: {scam_input}. Explain why or why not in Pidgin."
        fallback = handle_fallback(scam_input)
        result = fallback if fallback else query_huggingface(prompt)
        st.warning(result)

# Note
st.markdown("---")
st.markdown("Magami AI powered by Hugging Face model - flan-t5-large")
st.markdown("Na beginner friendly Python project for knowledge showcase.")
