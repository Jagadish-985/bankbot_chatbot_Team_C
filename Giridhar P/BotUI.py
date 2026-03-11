import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import json
import random
import ollama

# Initialize session state variables
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'page' not in st.session_state:
    st.session_state.page = 'login'
if 'username' not in st.session_state:
    st.session_state.username = ''
if 'user_data' not in st.session_state:
    st.session_state.user_data = {}
if 'selected_language' not in st.session_state:
    st.session_state.selected_language = ''
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 'dashboard'
if 'show_queries' not in st.session_state:
    st.session_state.show_queries = True
if 'faqs_cache' not in st.session_state:
    st.session_state.faqs_cache = None

# FAQ Management
def load_faqs():
    if st.session_state.faqs_cache is not None:
        return st.session_state.faqs_cache
    try:
        with open('faqs.json', 'r', encoding='utf-8') as f:
            faqs = json.load(f)
            st.session_state.faqs_cache = faqs
            return faqs
    except (FileNotFoundError, json.JSONDecodeError):
        st.session_state.faqs_cache = []
        return []

def save_to_faq(question, answer):
    faqs = load_faqs()
    if not any(faq['question'].lower() == question.lower() for faq in faqs):
        faqs.append({"question": question, "answer": answer})
        st.session_state.faqs_cache = faqs
        with open('faqs.json', 'w', encoding='utf-8') as f:
            json.dump(faqs, f, indent=4)

def find_faq_answer(user_query):
    faqs = load_faqs()
    user_query = user_query.lower().strip()
    
    # Pre-processing: remove common punctuation
    for char in "?!.":
        user_query = user_query.replace(char, "")
    
    user_words = set(user_query.split())
    if not user_words:
        return None
    
    best_match = None
    max_score = 0
    
    for faq in faqs:
        faq_q = faq['question'].lower()
        # Clean FAQ question for matching
        for char in "?!.":
            faq_q = faq_q.replace(char, "")
        
        # 1. Exact match (fastest)
        if faq_q == user_query:
            return faq['answer']
            
        # 2. Substring match
        if faq_q in user_query or user_query in faq_q:
            # Substring is a very strong signal
            score = 0.8 + (min(len(faq_q), len(user_query)) / max(len(faq_q), len(user_query)) * 0.2)
            if score > max_score:
                max_score = score
                best_match = faq['answer']
            continue
            
        # 3. Word overlap match (Jaccard-like)
        faq_words = set(faq_q.split())
        overlap = user_words.intersection(faq_words)
        if overlap:
            # Banking keywords are worth more
            banking_bonus = 0
            banking_keywords = {'balance', 'account', 'loan', 'interest', 'money', 'transfer', 'emi'}
            for word in overlap:
                if word in banking_keywords:
                    banking_bonus += 0.2
            
            score = (len(overlap) / len(faq_words.union(user_words))) + banking_bonus
            if score > max_score and score > 0.3: # Lowered threshold
                max_score = score
                best_match = faq['answer']
            
    return best_match

def is_banking_query(query):
    """Check if the query is related to banking/finance using keywords."""
    banking_keywords = {
        'account', 'balance', 'transaction', 'loan', 'interest', 'transfer', 'money', 
        'emi', 'savings', 'credit', 'debit', 'card', 'bank', 'payment', 'deposit', 
        'withdrawal', 'statement', 'rate', 'mortgage', 'investment', 'finance', 
        'insurance', 'pension', 'tax', 'salary', 'wallet', 'funds', 'atm', 'branch'
    }
    
    non_banking_keywords = {
        'recipe', 'cook', 'game', 'weather', 'movie', 'song', 'joke', 'travel', 
        'vacation', 'history', 'science', 'math', 'sports', 'football', 'cricket', 
        'celebrity', 'politics', 'fashion', 'health', 'fitness', 'beauty'
    }
    
    query_lower = query.lower()
    words = set(query_lower.split())
    
    # If it contains any non-banking triggers, reject it early
    if any(nbw in query_lower for nbw in non_banking_keywords):
        return False
        
    # If it contains banking keywords, it's likely safe
    if any(bw in query_lower for bw in banking_keywords):
        return True
        
    # Heuristic for generic natural language that might be banking related
    # Let the LLM handle ambiguous cases, but filter out obvious junk
    return True 

# Database setup
def init_db():
    conn = sqlite3.connect('bankbot.db')
    c = conn.cursor()
    
    # Users table with extended information
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, 
                  password TEXT)''')
    
    # Schema migration: check if columns exist and add them if not
    c.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in c.fetchall()]
    
    needed_columns = [
        ('full_name', 'TEXT'),
        ('email', 'TEXT'),
        ('phone', 'TEXT'),
        ('account_number', 'TEXT'),
        ('balance', 'REAL'),
        ('account_type', 'TEXT'),
        ('registration_date', 'TEXT')
    ]
    
    for col_name, col_type in needed_columns:
        if col_name not in columns:
            c.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
    
    # Transactions table
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT,
                  transaction_type TEXT,
                  amount REAL,
                  description TEXT,
                  timestamp TEXT,
                  FOREIGN KEY (username) REFERENCES users(username))''')
    
    # Loans table
    c.execute('''CREATE TABLE IF NOT EXISTS loans
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT,
                  loan_type TEXT,
                  loan_amount REAL,
                  interest_rate REAL,
                  tenure_months INTEGER,
                  monthly_emi REAL,
                  amount_paid REAL,
                  remaining_amount REAL,
                  status TEXT,
                  application_date TEXT,
                  FOREIGN KEY (username) REFERENCES users(username))''')
    
    # Chat history table
    c.execute('''CREATE TABLE IF NOT EXISTS chat_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT,
                  timestamp TEXT,
                  conversation TEXT,
                  FOREIGN KEY (username) REFERENCES users(username))''')
    
    conn.commit()
    conn.close()

init_db()

# Indian languages
INDIAN_LANGUAGES = [
    "English", "हिंदी (Hindi)", "বাংলা (Bengali)", "తెలుగు (Telugu)",
    "मराठी (Marathi)", "தமிழ் (Tamil)", "ગુજરાતી (Gujarati)",
    "ಕನ್ನಡ (Kannada)", "മലയാളം (Malayalam)", "ਪੰਜਾਬੀ (Punjabi)"
]

# Quick FAQs
QUICK_FAQS = [
    "💰Check Account Balance",
    "💵View Recent Transactions",
    "🏠Loan Information",
    "🏠Apply for New Loan",
    "💵%Interest Rates",
    "💸Transfer Money"
]

def verify_login(username, password):
    conn = sqlite3.connect('bankbot.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    result = c.fetchone()
    conn.close()
    return result is not None

def register_user(username, password, full_name, email, phone):
    try:
        conn = sqlite3.connect('bankbot.db')
        c = conn.cursor()
        
        # Generate account number
        account_number = str(random.randint(1000000000, 9999999999))
        registration_date = datetime.now().strftime("%Y-%m-%d")
        
        c.execute("""INSERT INTO users (username, password, full_name, email, phone, 
                     account_number, balance, account_type, registration_date) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (username, password, full_name, email, phone, account_number, 
                   1000.0, 'Savings', registration_date))
        
        conn.commit()
        conn.close()
        return True, account_number
    except sqlite3.IntegrityError:
        return False, None

def get_user_data(username):
    conn = sqlite3.connect('bankbot.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    
    if user:
        return {
            'username': user[0],
            'full_name': user[2],
            'email': user[3],
            'phone': user[4],
            'account_number': user[5],
            'balance': user[6],
            'account_type': user[7],
            'registration_date': user[8]
        }
    return None

def get_transactions(username, limit=10):
    conn = sqlite3.connect('bankbot.db')
    c = conn.cursor()
    c.execute("""SELECT transaction_type, amount, description, timestamp 
                 FROM transactions WHERE username=? 
                 ORDER BY timestamp DESC LIMIT ?""", (username, limit))
    transactions = c.fetchall()
    conn.close()
    return transactions

def get_loans(username):
    conn = sqlite3.connect('bankbot.db')
    c = conn.cursor()
    c.execute("SELECT * FROM loans WHERE username=?", (username,))
    loans = c.fetchall()
    conn.close()
    return loans

def save_chat_history():
    if st.session_state.messages:
        conn = sqlite3.connect('bankbot.db')
        c = conn.cursor()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conversation = json.dumps(st.session_state.messages)
        c.execute("INSERT INTO chat_history (username, timestamp, conversation) VALUES (?, ?, ?)",
                  (st.session_state.username, timestamp, conversation))
        conn.commit()
        conn.close()

def get_chat_history():
    conn = sqlite3.connect('bankbot.db')
    c = conn.cursor()
    c.execute("SELECT id, timestamp, conversation FROM chat_history WHERE username=? ORDER BY timestamp DESC",
              (st.session_state.username,))
    history = c.fetchall()
    conn.close()
    return history

def load_chat(chat_id):
    conn = sqlite3.connect('bankbot.db')
    c = conn.cursor()
    c.execute("SELECT conversation FROM chat_history WHERE id=?", (chat_id,))
    result = c.fetchone()
    conn.close()
    if result:
        st.session_state.messages = json.loads(result[0])

def delete_chat(chat_id):
    conn = sqlite3.connect('bankbot.db')
    c = conn.cursor()
    c.execute("DELETE FROM chat_history WHERE id=?", (chat_id,))
    conn.commit()
    conn.close()

def logout():
    st.session_state.logged_in = False
    st.session_state.page = 'login'
    st.session_state.username = ''
    st.session_state.user_data = {}
    st.session_state.selected_language = ''
    st.session_state.messages = []
    st.session_state.active_tab = 'dashboard'
    st.rerun()

# Page 1: Login/Registration Page
def login_registration_page():
    st.title("🏦 UNI BankBot - Your Digital Banking Partner")
    
    tab1, tab2 = st.tabs(["Login", "New Member Registration"])
    
    with tab1:
        st.header("Welcome to UNI BankBot!")
        st.write("")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            
            st.write("")
            
            if st.button("Login", use_container_width=True, type="primary"):
                if verify_login(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.user_data = get_user_data(username)
                    st.session_state.page = 'language_selection'
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            
        
        with col2:
            st.write("")
            st.write("")
            st.subheader("Why Choose BankBot?")
            st.write("🕑 24/7 AI-Powered Support")
            st.write("🔒 Bank-Grade Security")
            st.write("🌐 Multi-language Support")
            st.write("⚡ Instant Assistance")
            st.write("📊 Complete Financial Dashboard")
            st.write("💰 Loan Tracking & Management")
    
    with tab2:
        st.header("Join BankBot Today!")
        st.write("")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            new_full_name = st.text_input("Full Name", key="reg_fullname")
            new_email = st.text_input("Email Address", key="reg_email")
            new_phone = st.text_input("Phone Number", key="reg_phone", placeholder="+91-XXXXXXXXXX")
        
        with col2:
            new_username = st.text_input("Choose Username", key="reg_username")
            new_password = st.text_input("Create Password", type="password", key="reg_password")
            new_password_confirm = st.text_input("Confirm Password", type="password", key="reg_password_confirm")
        
        st.write("")
        
        if st.button("Register Now", use_container_width=True, type="primary"):
            if not all([new_full_name, new_email, new_phone, new_username, new_password]):
                st.error("Please fill in all fields")
            elif new_password != new_password_confirm:
                st.error("Passwords do not match")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters long")
            else:
                success, account_number = register_user(new_username, new_password, 
                                                       new_full_name, new_email, new_phone)
                if success:
                    st.success(f"Registration successful! Your account number is: {account_number}")
                    st.info("Please login with your credentials")
                else:
                    st.error("Username already exists. Please choose a different username.")

# Page 2: Language Selection
def language_selection_page():
    st.title("Select Your Preferred Language")
    st.subheader("अपनी पसंदीदा भाषा चुनें")
    
    st.write("")
    st.write(f"Welcome, {st.session_state.user_data.get('full_name', '')}!")
    st.write("Choose a language to continue:")
    st.write("")
    
    cols = st.columns(3)
    for idx, lang in enumerate(INDIAN_LANGUAGES):
        with cols[idx % 3]:
            if st.button(lang, key=f"lang_{idx}", use_container_width=True):
                st.session_state.selected_language = lang
                st.session_state.page = 'main'
                st.rerun()
    
    st.write("")
    st.write("")
    if st.button("← Logout"):
        logout()

# Enhanced Sidebar
def create_sidebar():
    with st.sidebar:
        st.title("🏦UNI Bank Bot")
        
        user_data = st.session_state.user_data
        
        # User Profile Section
        st.write("---")
        st.subheader("Profile Information")
        st.write(f"👤 **{user_data.get('full_name', 'N/A')}**")
        st.caption(f"@{st.session_state.username}")
        
        st.write("")
        st.write(f"📧 {user_data.get('email', 'N/A')}")
        st.write(f"📱 {user_data.get('phone', 'N/A')}")
        st.write(f"🌐 {st.session_state.selected_language}")
        
        st.write("---")
        
        # Account Details
        st.subheader("Account Details")
        st.write(f"💳 **Account Number**")
        st.code(user_data.get('account_number', 'N/A'))
        
        st.write(f"📊 **Account Type**")
        st.info(user_data.get('account_type', 'N/A'))
        
        st.write(f"💰 **Current Balance**")
        balance = user_data.get('balance', 0)
        st.success(f"₹ {balance:,.2f}")
        
        st.write(f"📅 **Member Since**")
        st.caption(user_data.get('registration_date', 'N/A'))
        
        st.write("---")
        
        # Quick Actions
        st.subheader("Quick Actions")
        
        if st.button("🏠 Dashboard", use_container_width=True):
            st.session_state.active_tab = 'dashboard'
            st.rerun()
        
        if st.button("💬 Chat Assistant", use_container_width=True):
            st.session_state.active_tab = 'chat'
            st.rerun()
        
        if st.button("💳 Transactions", use_container_width=True):
            st.session_state.active_tab = 'transactions'
            st.rerun()
        
        if st.button("🏦 Loan Tracking", use_container_width=True):
            st.session_state.active_tab = 'loans'
            st.rerun()
        
        st.write("---")
        
        # Logout
        if st.button("🚪 Logout", use_container_width=True, type="primary"):
            if st.session_state.messages:
                save_chat_history()
            logout()

# Dashboard Tab
def dashboard_tab():
    st.title("📊 Financial Dashboard")
    st.caption(f"Welcome back, {st.session_state.user_data.get('full_name', '')}!")
    
    st.write("")
    
    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Account Balance", f"₹ {st.session_state.user_data.get('balance', 0):,.2f}", 
                 delta="2.5%", delta_color="normal")
    
    with col2:
        transactions = get_transactions(st.session_state.username, limit=30)
        monthly_spending = sum([t[1] for t in transactions if t[0] == 'Debit'])
        st.metric("Monthly Spending", f"₹ {monthly_spending:,.2f}", 
                 delta="-5%", delta_color="inverse")
    
    with col3:
        monthly_income = sum([t[1] for t in transactions if t[0] == 'Credit'])
        st.metric("Monthly Income", f"₹ {monthly_income:,.2f}", 
                 delta="10%", delta_color="normal")
    
    with col4:
        loans = get_loans(st.session_state.username)
        active_loans = len([l for l in loans if l[9] == 'Active'])
        st.metric("Active Loans", active_loans)
    
    st.write("")
    st.write("---")
    st.write("")
    
    # Recent Activity and Loan Summary
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Recent Transactions")
        transactions = get_transactions(st.session_state.username, limit=5)
        
        if transactions:
            for trans in transactions:
                trans_type, amount, description, timestamp = trans
                
                if trans_type == 'Credit':
                    st.success(f"✅ +₹{amount:,.2f} - {description}")
                else:
                    st.error(f"❌ -₹{amount:,.2f} - {description}")
                
                st.caption(timestamp)
                st.write("")
        else:
            st.info("No recent transactions")
    
    with col2:
        st.subheader("Loan Summary")
        loans = get_loans(st.session_state.username)
        
        if loans:
            for loan in loans:
                loan_type = loan[2]
                loan_amount = loan[3]
                remaining = loan[8]
                status = loan[9]
                
                st.write(f"**{loan_type}**")
                progress = ((loan_amount - remaining) / loan_amount) * 100 if loan_amount > 0 else 0
                st.progress(progress / 100)
                st.caption(f"₹{remaining:,.2f} remaining of ₹{loan_amount:,.2f}")
                st.write("")
        else:
            st.info("No active loans")
    
    st.write("")
    st.write("---")
    st.write("")
    
    # Quick Links
    st.subheader("Quick Access")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("💸 Transfer Money", use_container_width=True):
            st.info("Money transfer feature coming soon!")
    
    with col2:
        if st.button("📄 Statements", use_container_width=True):
            st.info("Statement download feature coming soon!")
    
    with col3:
        if st.button("💳 Cards", use_container_width=True):
            st.info("Card management feature coming soon!")
    
    with col4:
        if st.button("⚙️ Settings", use_container_width=True):
            st.info("Settings feature coming soon!")

# Transactions Tab
def transactions_tab():
    st.title("💳 Transaction History")
    
    st.write("")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_type = st.selectbox("Transaction Type", ["All", "Credit", "Debit"])
    
    with col2:
        limit = st.selectbox("Show Last", [10, 25, 50, 100])
    
    with col3:
        st.write("")
        if st.button("Export to CSV", use_container_width=True):
            st.info("Export feature coming soon!")
    
    st.write("")
    st.write("---")
    st.write("")
    
    # Get transactions
    transactions = get_transactions(st.session_state.username, limit=limit)
    
    if transactions:
        # Create table
        st.subheader(f"Showing {len(transactions)} transactions")
        st.write("")
        
        for idx, trans in enumerate(transactions, 1):
            trans_type, amount, description, timestamp = trans
            
            col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
            
            with col1:
                if trans_type == 'Credit':
                    st.success("CREDIT")
                else:
                    st.error("DEBIT")
            
            with col2:
                st.write(f"**{description}**")
            
            with col3:
                if trans_type == 'Credit':
                    st.write(f"**+₹{amount:,.2f}**")
                else:
                    st.write(f"**-₹{amount:,.2f}**")
            
            with col4:
                st.caption(timestamp)
            
            if idx < len(transactions):
                st.divider()
    else:
        st.info("No transactions found")

# Loan Tracking Tab
def loans_tab():
    st.title("🏦 Loan Management & Tracking")
    
    st.write("")
    
    loans = get_loans(st.session_state.username)
    
    if loans:
        # Loan Overview
        st.subheader("Your Active Loans")
        st.write("")
        
        for loan in loans:
            loan_id, username, loan_type, loan_amount, interest_rate, tenure_months, monthly_emi, amount_paid, remaining_amount, status, application_date = loan
            
            # Loan Card
            with st.container():
                st.write(f"### {loan_type}")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Loan Amount", f"₹{loan_amount:,.2f}")
                    st.metric("Interest Rate", f"{interest_rate}% p.a.")
                
                with col2:
                    st.metric("Monthly EMI", f"₹{monthly_emi:,.2f}")
                    st.metric("Tenure", f"{tenure_months} months")
                
                with col3:
                    st.metric("Amount Paid", f"₹{amount_paid:,.2f}")
                    st.metric("Remaining", f"₹{remaining_amount:,.2f}")
                
                st.write("")
                
                # Progress bar
                progress = (amount_paid / loan_amount) * 100 if loan_amount > 0 else 0
                st.progress(progress / 100)
                st.caption(f"Progress: {progress:.1f}% completed")
                
                st.write("")
                
                # Loan details
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Status:** {status}")
                
                with col2:
                    st.write(f"**Application Date:** {application_date}")
                
                with col3:
                    months_completed = int((amount_paid / monthly_emi)) if monthly_emi > 0 else 0
                    months_remaining = tenure_months - months_completed
                    st.write(f"**Months Remaining:** {months_remaining}")
                
                st.write("")
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("Pay EMI", key=f"pay_emi_{loan_id}", use_container_width=True):
                        st.info("EMI payment feature coming soon!")
                
                with col2:
                    if st.button("View Statement", key=f"statement_{loan_id}", use_container_width=True):
                        st.info("Statement feature coming soon!")
                
                with col3:
                    if st.button("Prepayment", key=f"prepay_{loan_id}", use_container_width=True):
                        st.info("Prepayment feature coming soon!")
                
                st.write("---")
                st.write("")
    
    else:
        st.info("You don't have any active loans")
        st.write("")
    
    # Apply for new loan
    st.write("")
    st.subheader("Apply for a New Loan")
    st.write("")
    
    with st.expander("Loan Application Form"):
        loan_type = st.selectbox("Loan Type", 
                                ["Home Loan", "Car Loan", "Personal Loan", "Education Loan", "Business Loan"])
        
        col1, col2 = st.columns(2)
        
        with col1:
            loan_amount = st.number_input("Loan Amount (₹)", min_value=10000, max_value=10000000, step=10000)
            tenure = st.selectbox("Tenure (Years)", [1, 2, 3, 5, 7, 10, 15, 20, 25, 30])
        
        with col2:
            interest_rate = st.number_input("Interest Rate (% p.a.)", min_value=5.0, max_value=20.0, value=8.5, step=0.1)
            
            # Calculate EMI
            if loan_amount and tenure and interest_rate:
                r = interest_rate / (12 * 100)
                n = tenure * 12
                emi = (loan_amount * r * (1 + r)**n) / ((1 + r)**n - 1)
                st.metric("Estimated Monthly EMI", f"₹{emi:,.2f}")
        
        st.write("")
        
        if st.button("Submit Application", use_container_width=True, type="primary"):
            st.success("Loan application submitted successfully! You will receive a confirmation email shortly.")

def generate_llm_response(prompt, history, stream=True):
    """Generate a response using local Qwen 2.5 via Ollama."""
    try:
        user_data = st.session_state.user_data
        selected_language = st.session_state.selected_language
        
        # Strict domain restriction
        if not is_banking_query(prompt):
            msg = "this system only applied of banking queries and the given query is not related to the banking"
            if stream:
                def rejection_generator():
                    yield {"message": {"content": msg}}
                return rejection_generator()
            return msg

        # Ultra-condensed system context for speed and strictness
        system_context = f"""Role: UNI BankBot (Digital Bank Assistant).
Language: {selected_language} only.
Ctx: Acct {user_data.get('account_number')}, Bal ₹{user_data.get('balance', 0):,.2f}.
STRICT Rules:
1. Answer ONLY banking/financial queries.
2. If NOT banking/finance -> "this system only applied of banking queries and the given query is not related to the banking"
3. No personal advice, just bank info/FAQs.
4. Be brief. Max 2-3 sentences.
5. Prefix [FAQ] for generic answers that can be reused.
"""
        
        messages = [{"role": "system", "content": system_context}]
        # Minimal history for speed
        for msg in history[-1:]: 
            messages.append(msg)
        
        messages.append({"role": "user", "content": prompt})
        
        # Performance optimizations for low latency
        options = {
            "temperature": 0.1,
            "num_predict": 100,  # Limits generation length for speed
            "num_ctx": 512,      # Smaller context window for faster prompt processing
            "top_k": 10,         # Limits token sampling space
            "num_thread": 8,     # Utilize multiple CPU threads
            "repeat_penalty": 1.2
        }
        
        if stream:
            response = ollama.chat(model='qwen2.5', messages=messages, stream=True, options=options)
            return response
        else:
            response = ollama.chat(model='qwen2.5', messages=messages, options=options)
            return response['message']['content']
    except Exception as e:
        error_msg = f"I apologize, but I'm having trouble connecting to my AI core right now. (Error: {str(e)}). How else can I assist you with your banking needs?"
        if stream:
            def error_generator():
                yield {"message": {"content": error_msg}}
            return error_generator()
        return error_msg

# Chat Tab
def chat_tab():
    # Header with toggle button
    col_title, col_toggle = st.columns([4, 1])
    with col_title:
        st.title("💬 BankBot Assistant")
        st.caption("Ask me anything about your banking needs")
    with col_toggle:
        st.write("")
        st.write("")
        label = "📂 Show FAQs" if not st.session_state.show_queries else "📁 Hide FAQs"
        if st.button(label, use_container_width=True):
            st.session_state.show_queries = not st.session_state.show_queries
            st.rerun()

    # Conditional layout
    if st.session_state.show_queries:
        col_chat, col_info = st.columns([2, 1])
    else:
        col_chat = st.container()

    with col_chat:
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        # Check if the last message is from user and needs a response
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
            prompt = st.session_state.messages[-1]["content"]
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                full_response = ""
                
                # Check FAQs first
                faq_answer = find_faq_answer(prompt)
                
                if faq_answer:
                    full_response = faq_answer
                    response_placeholder.markdown(full_response)
                else:
                    # Generate response using local Qwen 2.5 with streaming
                    try:
                        stream = generate_llm_response(prompt, st.session_state.messages[:-1], stream=True)
                        for chunk in stream:
                            content = chunk['message']['content']
                            full_response += content
                            # Strip UI tags if they appear during streaming (optional)
                            display_response = full_response.replace("[FAQ]", "").strip()
                            response_placeholder.markdown(display_response + "▌")
                        
                        # Final processing
                        is_faq = "[FAQ]" in full_response
                        full_response = full_response.replace("[FAQ]", "").strip()
                        response_placeholder.markdown(full_response)
                        
                        if full_response != "this system only applied of banking queries and the given query is not related to the banking":
                            save_to_faq(prompt, full_response)
                            
                    except Exception as e:
                        error_str = str(e)
                        if "10061" in error_str or "connect" in error_str.lower():
                            full_response = "I apologize, but my AI backend (Ollama) is currently offline. Please ensure the Ollama application is running on your machine."
                        else:
                            full_response = f"An unexpected error occurred: {error_str}"
                        response_placeholder.markdown(full_response)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            st.rerun()
        
    if st.session_state.show_queries:
        with col_info:
            # Quick FAQs
            st.subheader("💡 Quick Questions")
            # Display FAQs in a list format for the sidebar
            for idx, faq in enumerate(QUICK_FAQS):
                if st.button(faq, key=f"faq_{idx}", use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": faq})
                    st.rerun()

            st.write("---")
            
            # Controls
            if st.button("🆕 New Chat", use_container_width=True):
                if st.session_state.messages:
                    save_chat_history()
                st.session_state.messages = []
                st.rerun()
                
            st.write("---")

            # Previous chats section
            st.subheader("📝 Previous Chats")
            chat_history = get_chat_history()
            
            if chat_history:
                for chat_id, timestamp, _ in chat_history[:10]:
                    with st.expander(f"🕒 {timestamp}", expanded=False):
                        c1, c2 = st.columns([1, 1])
                        with c1:
                            if st.button("Load", key=f"load_chat_{chat_id}", use_container_width=True):
                                load_chat(chat_id)
                                st.rerun()
                        with c2:
                            if st.button("🗑️", key=f"delete_chat_{chat_id}", use_container_width=True):
                                delete_chat(chat_id)
                                st.rerun()
            else:
                st.info("No previous conversations")

    # Chat input moved to the bottom (outside columns)
    if prompt := st.chat_input("Type your question here..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

# Main App Page
def main_app_page():
    create_sidebar()
    
    # Main content area based on active tab
    if st.session_state.active_tab == 'dashboard':
        dashboard_tab()
    elif st.session_state.active_tab == 'chat':
        chat_tab()
    elif st.session_state.active_tab == 'transactions':
        transactions_tab()
    elif st.session_state.active_tab == 'loans':
        loans_tab()

# Main app logic
def main():
    st.set_page_config(
        page_title="UNI BankBot - Digital Banking Assistant",
        page_icon="🏦",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    if not st.session_state.logged_in:
        login_registration_page()
    else:
        if st.session_state.page == 'language_selection':
            language_selection_page()
        elif st.session_state.page == 'main':
            main_app_page()

if __name__ == "__main__":
    main()