import streamlit as st
import openai
from textblob import TextBlob
import validators

# Load OpenAI API key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

st.set_page_config(page_title="Prince Magami AI Assistant & Chatbox", page_icon="🤖")

st.title("Prince Magami AI Assistant & Chatbox")
st.markdown("""
By Abubakar Muhammad Magami | FellowID: FE/23/75909764 | Cohort 3 - 3MTT  
**Magami AI Assistant and Chatbox**  
Choose a mode and language to get started.
""")

# Language selection (Pidgin or English)
lang = st.radio("Choose language:", ("Pidgin English", "English"))

def ask_openai(prompt):
    """
    Ask OpenAI GPT-3.5-turbo with updated syntax
    """
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are a helpful assistant who speaks in {lang}."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Wahala dey: {str(e)}"

def detect_emotion(text):
    """
    Detect emotions with extended set for better advice
    """
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity
    lowered = text.lower()
    
    # Check keywords for some specific emotions
    if any(word in lowered for word in ["nervous", "anxious", "worried"]):
        return "nervous"
    elif any(word in lowered for word in ["scared", "fear", "frightened"]):
        return "scared"
    elif any(word in lowered for word in ["excited", "happy", "joy"]):
        return "excited"
    elif any(word in lowered for word in ["depressed", "sad", "unhappy", "down"]):
        return "depressed"
    elif any(word in lowered for word in ["don’t know", "i don't know", "confused", "unsure"]):
        return "confused"
    elif polarity > 0.4:
        return "happy"
    elif polarity < -0.4:
        return "sad"
    elif subjectivity > 0.6:
        return "anxious"
    else:
        return "neutral"

def handle_out_of_scope():
    """
    Professional fallback answer for out-of-scope questions
    """
    if lang == "Pidgin English":
        return ("Sorry, I no fit help you with dat kind matter. "
                "I sabi only emotional support, small business advice, "
                "and cyber security tips for Nigerians. "
                "Abeg ask wetin relate to those areas.")
    else:
        return ("Sorry, I can't assist with that topic. "
                "I specialize in emotional support, small business advice, "
                "and cybersecurity awareness tailored for Nigerians. "
                "Please ask something related to these areas.")

# Mode selection with separate modes for Business and Cybersecurity
mode = st.selectbox("Select mode:", [
    "Scam/Email Checker",
    "Emotional Advice ChatBox",
    "Business Helper",
    "Cybersecurity Tips"
])

# -- Scam/Email Checker Mode --
if mode == "Scam/Email Checker":
    st.subheader("Scam Detector")
    user_input = st.text_area("Paste email or link you wan check:", height=150)
    if st.button("Scan am!") and user_input.strip():
        if validators.url(user_input.strip()):
            prompt = (f"Is this link a scam? Link: {user_input.strip()}. "
                      f"Explain why in {lang}. "
                      "If not scam, explain why it is safe.")
        else:
            prompt = (f"Is this email or text a scam? Text: {user_input.strip()}. "
                      f"Explain why in {lang}. "
                      "If not scam, explain why it is safe.")
        result = ask_openai(prompt)
        st.success(result)

# -- Emotional Advice Chat Mode --
elif mode == "Emotional Advice Chat":
    st.subheader("Talk to your AI Buddy")
    feelings = st.text_area("How you dey feel? Talk true.", height=200)
    if st.button("Send") and feelings.strip():
        emotion = detect_emotion(feelings)
        
      
        prompt = (
            f"Person talk say: '{feelings.strip()}'. "
            f"Detect emotion as '{emotion}'. "
            f"Give {lang} emotional support advice considering these emotions: nervous, scared, excited, anxious, depressed, confused, happy, sad, neutral. "
            "Add multiple advice and encouragements, make e warm and supportive. "
            "If person dey confused or don't know, encourage patience and offer hope. "
            "Answer kindly and professionally."
        )
        result = ask_openai(prompt)
        st.info(result)

# -- Business Helper Mode --
elif mode == "Business Helper":
    st.subheader("Small Business Helper")
    business_input = st.text_area("Tell me your business idea, complaint, or question:", height=200)
    if st.button("Send") and business_input.strip():
        # AI asks for clarification if input is too vague
        prompt = (
            f"User talk say: '{business_input.strip()}'. "
            f"Give {lang} concise advice and strategies for small Nigerian businesses. "
            "If the business question or idea is unclear, ask the user one clarifying question politely. "
            "Otherwise, give practical tips, advice, and business growth strategies. "
            "Be culturally relevant and beginner friendly."
        )
        result = ask_openai(prompt)
        st.success(result)

# -- Cybersecurity tips --
elif mode == "Cybersecurity Advice":
    st.subheader("Cybersecurity Awareness & Tips")
    cyber_input = st.text_area("Ask about cybersecurity, risks, tips, or concerns:", height=200)
    if st.button("Send") and cyber_input.strip():
        prompt = (
            f"User talk say: '{cyber_input.strip()}'. "
            f"Provide {lang} local Nigerian cybersecurity awareness, practical tips, and education for small businesses and individuals. "
            "Give detailed advice about protecting data, avoiding scams, and using safe online practices. "
            "If the question is out of cybersecurity scope, respond professionally and guide the user to ask relevant questions."
        )
        result = ask_openai(prompt)
        st.success(result)
