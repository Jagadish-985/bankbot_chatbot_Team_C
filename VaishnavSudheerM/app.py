import ollama
import streamlit as st
import base64
import json
import re

# ---------------- LOAD BANKING LIBRARY ----------------
with open("banking_library.json") as f:
    banking_data = json.load(f)

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="BankBot AI", page_icon="🏦", layout="wide")

# ---------------- BACKGROUND ----------------
def add_bg_with_overlay(image_file):
    with open(image_file, "rb") as image:
        encoded = base64.b64encode(image.read()).decode()

    st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(
            rgba(0,0,0,0.65),
            rgba(0,0,0,0.65)
        ),
        url("data:image/jpeg;base64,{encoded}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    </style>
    """, unsafe_allow_html=True)

add_bg_with_overlay("background.jpg")

# ---------------- STYLE ----------------
st.markdown("""
<style>
h1 {color:#4CAF50;}
.stChatInputContainer {border-radius:15px;}
</style>
""", unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------
st.sidebar.title("🏦 BankBot AI")
st.sidebar.markdown("### Smart Banking Assistant")
st.sidebar.write("Built using Streamlit")

menu = st.sidebar.radio("Navigate", ["Chat Assistant","EMI Calculator"])

# ---------------- SESSION ----------------
if "search_history" not in st.session_state:
    st.session_state.search_history = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ---------------- SEARCH HISTORY ----------------
st.sidebar.subheader("📜 Search History")

if st.sidebar.button("🗑 Clear History"):
    st.session_state.search_history=[]
    st.session_state.chat_history=[]

for i,q in enumerate(st.session_state.search_history[::-1]):
    st.sidebar.write(f"{i+1}. {q}")

# ---------------- CHAT PAGE ----------------
if menu=="Chat Assistant":

    st.title("🏦 BankBot AI - Smart Banking Assistant")
    st.write("Ask me anything related to banking.")

    user_input=st.chat_input("Ask your banking question...")

    def generate_response(question):

        q = question.lower().strip()
        clean = re.sub(r"[^\w\s]","",q)

        # ---------------- STEP 1: LIBRARY DEFINITIONS ----------------
        if clean.startswith("what is") or clean.startswith("define"):

            for key,value in banking_data.items():

                if key in clean:
                    return f"📚 Source: Banking Library\n\n{value}"

        # ---------------- STEP 2: BANKING DOMAIN CHECK ----------------
        banking_keywords=[
            "bank","banks","loan","interest","deposit","account",
            "credit","debit","atm","money","finance","transaction",
            "savings","current","emi","profit","card"
        ]

        if not any(word in clean for word in banking_keywords):
            return "🚫 I can only answer banking-related questions."

        # ---------------- STEP 3: AI RESPONSE ----------------
        response=ollama.chat(
            model="llama3",
            messages=[
                {
                    "role":"system",
                    "content":
                    "You are BankBot AI, a professional banking assistant. "
                    "Answer only banking related questions clearly."
                },
                {
                    "role":"user",
                    "content":question
                }
            ]
        )

        return f"🤖 Source: AI Model\n\n{response['message']['content']}"

    if user_input:

        st.session_state.search_history.append(user_input)
        st.session_state.chat_history.append(("You",user_input))

        with st.spinner("🤖 BankBot is thinking..."):
            reply=generate_response(user_input)

        st.session_state.chat_history.append(("BankBot",reply))

    for sender,message in st.session_state.chat_history:

        if sender=="You":
            st.chat_message("user").write(message)
        else:
            st.chat_message("assistant").write(message)

# ---------------- EMI CALCULATOR ----------------
elif menu=="EMI Calculator":

    st.title("💰 Loan EMI Calculator")

    loan_amount=st.number_input("Loan Amount (₹)",min_value=1000)
    interest_rate=st.number_input("Interest Rate (%)",min_value=1.0)
    tenure=st.number_input("Tenure (Years)",min_value=1)

    if st.button("Calculate EMI"):

        monthly_rate=interest_rate/(12*100)
        months=tenure*12

        emi=(loan_amount*monthly_rate*(1+monthly_rate)**months)/((1+monthly_rate)**months-1)

        st.success(f"Monthly EMI: ₹{emi:,.2f}")
