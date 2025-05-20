import streamlit as st
import openai 
from textblob import TextBlob 
import validators

#CONFIG

openai.api_key = st.secrets["openai"]["api_key"]

st.set_page_config(page_title="Magami AI Assistant & Chatbox", page_icon="🤖")

#PAGE TITLE

st.title("Magami AI Assistant & Chatbox") 

st.markdown(""" By Abubakar Muhammad Magami
Fellow ID: FE/23/75909764 | 3MTT Cohort 3 """)

#MODE SELECTION

mode = st.selectbox("Choose your mode:", [ "Scam/Email Checker", "Emotional Advice Chat", "Business + Cybersecurity Helper" ])

#Helper Function to call OpenAI

def ask_openai(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You be helpful assistant wey sabi talk Pidgin English."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        return response.choices[0].message["content"]
    except Exception as e:
        return f"Wahala dey: {str(e)}"
        
#Scam/Email Checker

if mode == "Scam/Email Checker":
    st.subheader("Scam Detector")
    user_input = st.text_area("Paste email or link wey you wan check:")
    
    if st.button("Scan am!") and user_input:
        if validators.url(user_input):
            result = ask_openai(f"This link fit be scam? Link: {user_input}. Explain why in Pidgin.")
        else:
            result = ask_openai(f"This email/text fit be scam? Text: {user_input}. Explain why in Pidgin.")
        
        st.success(result)

#Emotional Advice Chat

elif mode == "Emotional Advice Chat":
    st.subheader("Talk to your AI Buddy")
    feelings = st.text_area("How you dey feel?")
    
    if st.button("I need advice") and feelings:
        sentiment = TextBlob(feelings).sentiment.polarity
        prompt = f"Person talk say: '{feelings}'. Give better emotional support in Pidgin."
        
        if sentiment < 0:
            prompt += " Na sad message. Help am feel better."
        
        result = ask_openai(prompt)
        st.info(result)

#Business + Cybersecurity Helper

elif mode == "Business + Cybersecurity Helper":
    st.subheader("Business and Cyber Tips")
    biz_input = st.text_input("Wetyn be your business idea or question?")
    
    if st.button("Give me tips") and biz_input:
        prompt = (
            f"Help small Nigerian business. User talk say: '{biz_input}'. "
            "Give Pidgin advice for biz success and add local cyber security awareness, tips and education."
        )
        result = ask_openai(prompt)
        st.success(result)

st.markdown("---") 
st.markdown("""Powered by OpenAI | Built for 3MTT Knowledge Showcase | 2025""")

