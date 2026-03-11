

from ollama import chat
import json
import streamlit as st

# ---------------- JSON LOAD ----------------
with open("banking_data.json", "r", encoding="utf-8") as f:
    banking_data = json.load(f)

# ---------------- JSON RESPONSE FUNCTION ----------------
def get_json_response(query, lang):
    q = query.lower().strip()
    
    for category, items in banking_data.items():  # Account Services, ATM & Card, etc.
        for faq_title, answers in items.items():
            if faq_title.lower() in q:
                if lang == "Hindi":
                    return answers.get("hi", "उत्तर उपलब्ध नहीं है।")
                else:
                    return answers.get("en", "Answer not available")
    return None

# ---------------- AI FUNCTION ----------------
def ask_ai(user_query):
    response = chat(
        model="llama3",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a banking assistant chatbot. "
                    "Answer only banking-related questions in simple language. "
                    "If the user asks anything unrelated to banking, reply: "
                    "'Please ask banking-related question.'"
                )
            },
            {"role": "user", "content": user_query}
        ]
    )
    return response["message"]["content"]

# ---------------- STREAMLIT CONFIG ----------------
st.set_page_config(page_title="AI Banking Assistant", layout="wide")

# ---------------- SESSION ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "ai"
if "chats" not in st.session_state:
    st.session_state.chats = {}
if "current_chat" not in st.session_state:
    st.session_state.current_chat = None
if "auto_prompt" not in st.session_state:
    st.session_state.auto_prompt = ""
if "show_settings" not in st.session_state:
    st.session_state.show_settings = False
if "lang" not in st.session_state:
    st.session_state.lang = "English"
if "show_lang" not in st.session_state:
    st.session_state.show_lang = False

# ---------------- STYLE ----------------
st.markdown("""
<style>
.stApp { background: linear-gradient(to right, #141E30, #243B55); color: white; }
.bank-title { text-align: center; font-size: 42px; font-weight: bold; color: white; }
div.stButton > button { border-radius:12px; height:45px; width:100%; border:none; font-size:15px; font-weight:bold; background:#00BFA6; color:white; margin-bottom:6px; }
[data-testid="stChatMessageContent"] {color:white !important;}
[data-testid="stMarkdownContainer"] p {color:white !important;}
</style>
""", unsafe_allow_html=True)

# ---------------- LOGIN PAGE ----------------
if not st.session_state.logged_in:

    st.markdown('<h1 class="bank-title">🏦 Banking AI Assistant</h1>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([3,2,3])
    with col2:
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login", key="login_button"):
            if username.strip() and password.strip():
                st.session_state.logged_in = True
                st.session_state.page = "ai"
                st.rerun()
            else:
                st.warning("Please enter username and password")

# ---------------- MAIN APP ----------------
else:

    # -------- SIDEBAR --------
    with st.sidebar:
        st.title("🏦 FinFusion")

        if st.button("🤖 AI Assistant", key="sidebar_ai"):
            st.session_state.page = "ai"
            st.rerun()

        if st.button("➕ New Chat", key="sidebar_new_chat"):
            st.session_state.current_chat = None
            st.rerun()

        st.markdown("---")
        st.subheader("💬 Chat History")
        for chat_name in st.session_state.chats:
            if st.button(chat_name, key=f"chat_{chat_name}"):
                st.session_state.current_chat = chat_name
                st.session_state.page = "ai"
                st.rerun()

        st.markdown("---")
        if st.button("⚙️ Settings", key="sidebar_settings"):
            st.session_state.show_settings = not st.session_state.show_settings

        if st.session_state.show_settings:
            if st.button("🧹 Clear Current Chat", key="clear_current_chat"):
                if st.session_state.current_chat in st.session_state.chats:
                    st.session_state.chats[st.session_state.current_chat] = []
                    st.success("Current chat cleared!")

            if st.button("🗑️ Clear All Chats", key="clear_all_chats"):
                st.session_state.chats = {}
                st.session_state.current_chat = None
                st.success("All chat history deleted!")

            if st.button("🌐 Language", key="settings_language"):
                st.session_state.show_lang = not st.session_state.show_lang

            if st.session_state.show_lang:
                selected_lang = st.selectbox(
                    "Select Language",
                    ["English", "Hindi"],
                    index=0 if st.session_state.lang=="English" else 1,
                    key="lang_select"
                )
                st.session_state.lang = selected_lang
                st.success(f"Language set to {selected_lang}")

            if st.button("🔁 Reset Bot", key="reset_bot"):
                st.session_state.current_chat = None
                st.success("Bot memory cleared!")

        st.markdown("---")
        if st.button("🚪 Logout", key="sidebar_logout"):
            st.session_state.logged_in = False
            st.session_state.current_chat = None
            st.rerun()

    # ---------------- AI PAGE ----------------
    if st.session_state.page == "ai":

        st.title("🤖 AI Assistant")

        # --------- BANKING FAQ BUTTONS ---------
        with st.expander("▶ Banking FAQs"):

            for category, items in banking_data.items():
                with st.expander(f"▸ {category}"):
                    for faq_title in items:
                        if st.button(faq_title, key=f"faq_{category}_{faq_title}"):
                            st.session_state.auto_prompt = faq_title

        st.markdown("---")

        # --------- CHAT MESSAGES ---------
        if st.session_state.current_chat:
            for msg in st.session_state.chats[st.session_state.current_chat]:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        prompt = st.chat_input("Message Bank Relation AI...", key="chat_input")

        if st.session_state.auto_prompt:
            prompt = st.session_state.auto_prompt
            st.session_state.auto_prompt = ""

        if prompt:
            if not st.session_state.current_chat:
                st.session_state.current_chat = prompt[:25]
                st.session_state.chats[st.session_state.current_chat] = []

            messages = st.session_state.chats[st.session_state.current_chat]
            messages.append({"role":"user","content":prompt})

            lang = st.session_state.lang
            json_reply = get_json_response(prompt, lang)

            if json_reply:
                reply = json_reply
            else:
                try:
                    reply = ask_ai(prompt)
                except:
                    reply = "Sorry, AI service abhi available nahi hai. Thodi der baad try karo."

            messages.append({"role":"assistant","content":reply})
            st.rerun()