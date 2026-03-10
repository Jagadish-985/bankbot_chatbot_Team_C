import streamlit as st
from datetime import datetime
import time
import hashlib
import requests
import json
import os

# Page configuration - MUST BE FIRST
st.set_page_config(
    page_title="BankBot AI - Batch 13",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Banking Knowledge Library
KNOWLEDGE_LIBRARY_PATH = "banking_knowledge_library.json"

def load_banking_knowledge():
    """Load the optimized banking knowledge library"""
    try:
        if os.path.exists(KNOWLEDGE_LIBRARY_PATH):
            with open(KNOWLEDGE_LIBRARY_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return None
    except Exception as e:
        return None

# Load knowledge base at startup
BANKING_KNOWLEDGE = load_banking_knowledge()

# Ollama Configuration
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"

# OPTIMIZED Banking System Prompt - Shorter for faster responses
SYSTEM_PROMPT = """You are BankBot, a banking assistant. ONLY answer banking questions.

⚠️ RULES:
1. ONLY banking/financial topics
2. REFUSE non-banking politely: "I only assist with banking queries. Topics: accounts, loans, cards, transfers."

Banking Data:
{}

Keep responses under 100 words. Use bullet points. Be specific with rates/fees."""

def is_banking_related(query):
    """
    Check if the query is related to banking using comprehensive keyword matching.
    Returns True if banking-related, False otherwise.
    """
    # Comprehensive banking keywords
    banking_keywords = [
        # Accounts
        'account', 'savings', 'current', 'balance', 'deposit', 'withdrawal',
        'fixed deposit', 'fd', 'recurring deposit', 'rd', 'demat', 'passbook',
        
        # Transactions
        'transfer', 'payment', 'transaction', 'neft', 'rtgs', 'imps', 'upi',
        'send money', 'receive money', 'remittance', 'wire transfer', 'send', 'pay',
        
        # Cards
        'card', 'debit card', 'credit card', 'atm', 'pin', 'cvv',
        'credit limit', 'card block', 'lost card', 'stolen card', 'contactless',
        
        # Loans
        'loan', 'emi', 'interest', 'borrow', 'credit', 'mortgage',
        'home loan', 'personal loan', 'car loan', 'education loan',
        'business loan', 'overdraft', 'line of credit',
        
        # Banking Services
        'bank', 'banking', 'branch', 'ifsc', 'swift', 'cheque', 'check',
        'passbook', 'statement', 'netbanking', 'mobile banking',
        'internet banking', 'online banking', 'phone banking',
        
        # Investments & Insurance
        'investment', 'mutual fund', 'sip', 'insurance', 'stock',
        'bond', 'portfolio', 'equity', 'dividend',
        
        # Charges & Rates
        'charges', 'fees', 'fee', 'rate', 'interest rate', 'apr', 'processing fee',
        'annual fee', 'service charge', 'penalty', 'cost',
        
        # Customer Service
        'customer care', 'support', 'complaint', 'grievance', 'helpline',
        'customer service', 'query', 'issue', 'help',
        
        # Security & Fraud
        'fraud', 'otp', 'security', 'phishing', 'scam', 'password',
        'authentication', 'verification', 'kyc',
        
        # Financial Terms
        'money', 'finance', 'financial', 'cash', 'rupee', 'currency',
        'dollar', 'inr', 'usd', 'fund', 'wealth', 'amount',
        
        # Actions & Process - CRITICAL FOR FOLLOW-UPS
        'apply', 'applying', 'application', 'open', 'opening', 'close', 'closing',
        'activate', 'deactivate', 'register', 'registration', 'process', 'procedure',
        'steps', 'step', 'how', 'what', 'when', 'where', 'document', 'documents',
        'requirement', 'requirements', 'need', 'needs', 'eligibility', 'eligible'
    ]
    
    query_lower = query.lower()
    
    # Check if query contains any banking keywords
    if any(keyword in query_lower for keyword in banking_keywords):
        return True
    
    # CRITICAL FIX: Allow short follow-up questions
    # These are likely continuations of banking conversations
    short_followups = [
        'yes', 'no', 'ok', 'okay', 'sure', 'please', 'thanks', 'thank you',
        'tell me', 'more', 'details', 'explain', 'continue', 'go on', 'next',
        'interested', 'want', 'like', 'prefer', 'choose', 'select'
    ]
    
    # If query is short (<=5 words) and contains followup words, likely banking context
    if len(query.split()) <= 5:
        if any(word in query_lower for word in short_followups):
            return True  # Allow it through, context memory will handle it
    
    return False

def call_ollama(prompt, conversation_history=None):
    """
    Call Ollama with conversational style, full context memory, and banking restriction
    """
    try:
        # STRICT banking-only check
        if not is_banking_related(prompt):
            return """I apologize, but I can only help with banking and financial questions.

I can assist you with:
• Account services (savings, current, FD)
• Loans (home, personal, car, education)
• Money transfers (NEFT, RTGS, IMPS, UPI)  
• Cards (debit and credit cards)
• Interest rates and charges

Please ask me something about banking! 🏦"""
        
        # Extract relevant knowledge based on query - CHAT-FRIENDLY FORMAT
        knowledge_context = ""
        
        if BANKING_KNOWLEDGE:
            try:
                kb = BANKING_KNOWLEDGE.get('banking_knowledge', {})
                query_lower = prompt.lower()
                
                # ACCOUNTS - conversational data
                if any(w in query_lower for w in ['account', 'savings', 'current', 'open', 'balance', 'minimum']):
                    accounts = kb.get('accounts', {})
                    if 'savings' in query_lower or 'saving' in query_lower:
                        savings = accounts.get('savings', {})
                        knowledge_context += f"\nSavings Account: Interest is {savings.get('interest_rate', '3.5-4%')}. "
                        min_bal = savings.get('min_balance', {})
                        knowledge_context += f"Minimum balance - Urban: {min_bal.get('urban', '₹10k')}, Rural: {min_bal.get('rural', '₹5k')}. "
                        knowledge_context += f"Documents needed: {savings.get('opening_docs', 'PAN, Aadhaar, photo')}."
                    elif 'current' in query_lower:
                        current = accounts.get('current', {})
                        knowledge_context += f"\nCurrent Account: No interest (0%). Minimum balance {current.get('min_balance', '₹25k')}. Perfect for businesses."
                    elif 'fd' in query_lower or 'fixed' in query_lower or 'deposit' in query_lower:
                        fd = accounts.get('fixed_deposit', {})
                        rates = fd.get('rates', {})
                        knowledge_context += f"\nFixed Deposit Rates: 1 year - {rates.get('1_to_2_years', '6.75%')}, "
                        knowledge_context += f"3 years - {rates.get('3_to_5_years', '7.25%')}, "
                        knowledge_context += f"5+ years - {rates.get('above_5_years', '7.50%')}. "
                        knowledge_context += f"Senior citizens get extra {fd.get('senior_citizen_bonus', '0.5%')}!"
                    else:
                        knowledge_context += "\nWe offer Savings (3.5-4% interest), Current (for business), and Fixed Deposit (5.5-7.5% interest) accounts."
                
                # TRANSFERS - conversational
                if any(w in query_lower for w in ['transfer', 'send', 'payment', 'neft', 'rtgs', 'imps', 'upi']):
                    transfers = kb.get('transfers', {})
                    
                    if 'neft' in query_lower:
                        neft = transfers.get('neft', {})
                        knowledge_context += f"\nNEFT: {neft.get('charges', 'Free')}! Takes {neft.get('settlement', '2-3 hours')}. {neft.get('timing', 'Works 24/7')}."
                    
                    elif 'rtgs' in query_lower:
                        rtgs = transfers.get('rtgs', {})
                        charges = rtgs.get('charges', {})
                        knowledge_context += f"\nRTGS: Very fast - {rtgs.get('settlement', '30 minutes')}! "
                        knowledge_context += f"Minimum {rtgs.get('minimum', '₹2L')}. Charges: {charges.get('2_to_5_lakhs', '₹25')} for 2-5L, {charges.get('above_5_lakhs', '₹55')} above 5L."
                    
                    elif 'imps' in query_lower:
                        imps = transfers.get('imps', {})
                        knowledge_context += f"\nIMPS: Instant! {imps.get('settlement', 'Within seconds')}. "
                        knowledge_context += f"Works {imps.get('timing', '24/7')}. Max {imps.get('maximum', '₹5L')} per transaction. Charges ₹5 to ₹25."
                    
                    elif 'upi' in query_lower:
                        upi = transfers.get('upi', {})
                        knowledge_context += f"\nUPI: {upi.get('charges', 'Totally free')}! {upi.get('settlement', 'Instant')}. "
                        knowledge_context += f"Limit {upi.get('limit_per_day', '₹1L')} per day. Easiest way to send money!"
                    
                    else:
                        knowledge_context += "\nTransfer options: NEFT (free, 2-3hr), RTGS (₹25-55, 30min, min ₹2L), IMPS (₹5-25, instant), UPI (free, instant, max ₹1L)."
                
                # LOANS - conversational
                if any(w in query_lower for w in ['loan', 'emi', 'borrow', 'lend', 'mortgage']):
                    loans = kb.get('loans', {})
                    
                    if 'home' in query_lower or 'house' in query_lower:
                        home = loans.get('home_loan', {})
                        knowledge_context += f"\nHome Loan: Interest {home.get('interest_rate', '8.5-9.5%')}. "
                        knowledge_context += f"Max amount {home.get('max_amount', '₹5 crores')}! "
                        knowledge_context += f"Tenure up to {home.get('tenure', '30 years')}. We fund up to 90% of property value."
                    
                    elif 'personal' in query_lower:
                        personal = loans.get('personal_loan', {})
                        knowledge_context += f"\nPersonal Loan: Interest {personal.get('interest_rate', '10.5-18%')}. "
                        knowledge_context += f"Amount {personal.get('min_amount', '₹50k')} to {personal.get('max_amount', '₹25L')}. "
                        knowledge_context += f"Eligibility: {personal.get('eligibility', 'Age 21-60, min salary ₹25k')}."
                    
                    elif 'car' in query_lower or 'auto' in query_lower or 'vehicle' in query_lower:
                        car = loans.get('car_loan', {})
                        knowledge_context += f"\nCar Loan: Interest {car.get('interest_rate', '9-12%')}. "
                        knowledge_context += f"Tenure {car.get('tenure', 'up to 7 years')}. Down payment just {car.get('down_payment', '10%')}!"
                    
                    elif 'education' in query_lower or 'student' in query_lower or 'study' in query_lower:
                        edu = loans.get('education_loan', {})
                        max_amt = edu.get('max_amount', {})
                        knowledge_context += f"\nEducation Loan: India - up to {max_amt.get('in_india', '₹20L')}, "
                        knowledge_context += f"Abroad - up to {max_amt.get('abroad', '₹50L')}! "
                        knowledge_context += f"Start paying after {edu.get('moratorium', 'course + 6 months')}."
                    
                    else:
                        knowledge_context += "\nLoans: Home (8.5-9.5%, max ₹5Cr), Personal (10.5-18%, max ₹25L), Car (9-12%), Education (9.5-12.5%)."
                
                # CARDS - conversational
                if any(w in query_lower for w in ['card', 'debit', 'credit', 'atm']):
                    cards = kb.get('cards', {})
                    
                    if 'debit' in query_lower:
                        if 'platinum' in query_lower:
                            plat = cards.get('debit_platinum', {})
                            knowledge_context += f"\nPlatinum Debit: {plat.get('annual_fee', '₹500')}/year. "
                            knowledge_context += f"Benefits: {plat.get('benefits', 'lounge access, cashback, insurance')}."
                        else:
                            classic = cards.get('debit_classic', {})
                            knowledge_context += f"\nClassic Debit: {classic.get('annual_fee', 'Free 1st year, then ₹200')}. "
                            knowledge_context += f"ATM limit {classic.get('atm_limit', '₹40k')}/day, shopping {classic.get('shopping_limit', '₹2L')}/day."
                    
                    elif 'credit' in query_lower:
                        if 'gold' in query_lower:
                            gold = cards.get('credit_gold', {})
                            knowledge_context += f"\nGold Credit: {gold.get('annual_fee', '₹2,500')}/year (free on ₹3L spend). "
                            knowledge_context += f"Rewards: {gold.get('rewards', '2 points per ₹100')}. Benefits: {gold.get('benefits', 'lounge, travel insurance')}."
                        else:
                            silver = cards.get('credit_silver', {})
                            knowledge_context += f"\nSilver Credit: {silver.get('annual_fee', '₹500')} (free on ₹50k spend). "
                            knowledge_context += f"Limit {silver.get('credit_limit', '₹20k to ₹2L')}. Rewards: {silver.get('rewards', '1 point per ₹100')}."
                    
                    elif 'lost' in query_lower or 'stolen' in query_lower or 'block' in query_lower:
                        lost = cards.get('lost_card', {})
                        knowledge_context += f"\nLost Card: Call {lost.get('helpline', '1800-XXX-CARD')} immediately ({lost.get('available', '24/7')}). "
                        knowledge_context += f"We'll block it instantly. New card in {lost.get('steps', '5-7 days').split('in')[-1]}."
                    
                    elif 'atm' in query_lower:
                        gen = kb.get('general_info', {})
                        atm = gen.get('atm', {})
                        knowledge_context += f"\nATM: First {atm.get('free_withdrawals', '5')} withdrawals/month are free, "
                        knowledge_context += f"then {atm.get('charges_after', '₹20')} per transaction. We have {atm.get('total_atms', '2000+')} ATMs!"
                
                # GENERAL INFO
                if 'interest' in query_lower and 'rate' in query_lower and not knowledge_context:
                    knowledge_context += "\nInterest Rates: Savings 3.5-4%, FD 5.5-7.5%, Home Loan 8.5-9.5%, Personal Loan 10.5-18%."
                
                if any(w in query_lower for w in ['customer care', 'support', 'helpline', 'contact', 'call']):
                    gen = kb.get('general_info', {})
                    care = gen.get('customer_care', {})
                    knowledge_context += f"\nCustomer Care: {care.get('phone', '1800-XXX-XXXX')} - {care.get('timings', '24/7')}. Email: {care.get('email', 'support@bankbot.ai')}."
                
                if 'document' in query_lower or 'open' in query_lower:
                    gen = kb.get('general_info', {})
                    opening = gen.get('account_opening', {})
                    knowledge_context += f"\nDocuments: {opening.get('documents', 'PAN, Aadhaar, photo, address proof')}. Takes {opening.get('time', '24-48 hours')}."
                
            except Exception as e:
                knowledge_context = "\nFull banking services available. Contact 1800-XXX-XXXX for details."
        
        # Build CONVERSATIONAL system prompt
        system_prompt = f"""You are BankBot, a friendly and helpful banking assistant. Talk naturally like a helpful bank representative.

CRITICAL RULES:
1. ONLY answer banking and financial questions
2. Give complete, helpful answers in a CONVERSATIONAL tone
3. Use the data provided below - be SPECIFIC with rates and fees
4. Keep responses under 200 words but make them complete
5. Use bullet points ONLY when listing multiple items
6. Be friendly, use "you" and "your" naturally
7. If someone thanks you, respond warmly
8. IMPORTANT: If the customer asks a follow-up question (like "what are the steps?", "I'm interested", "tell me more"), 
   look at the PREVIOUS conversation to understand what they're asking about. Use context!

BANKING DATA:
{knowledge_context}

CONVERSATION STYLE:
- Talk naturally: "You'll get 6.75% interest" not "The interest rate is 6.75%"
- Be helpful: "That's a great question!" or "Let me help you with that"
- Be specific: Use exact numbers from the data
- Be complete: Answer fully, don't leave info out
- Use context: If they ask "what are the steps?" look at what they asked before
- For follow-ups: Connect to previous topic naturally"""
        
        # Add FULL conversation history for context memory
        full_context = system_prompt + "\n\nConversation so far:"
        
        if conversation_history and len(conversation_history) > 0:
            # Include last 5 messages (was 2) for better memory
            recent = conversation_history[-5:]
            for msg in recent:
                role = "Customer" if msg['role'] == 'user' else "BankBot"
                content = msg['content']
                full_context += f"\n{role}: {content}"
        
        full_context += f"\n\nCustomer: {prompt}\nBankBot:"
        
        # Optimized settings for chat-like responses
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": full_context,
            "stream": False,
            "options": {
                "temperature": 0.6,      # Natural conversation
                "top_p": 0.9,            # Quality responses
                "num_predict": 300,      # Complete answers
                "num_ctx": 2048,         # Good context
                "repeat_penalty": 1.2,   # Avoid repetition
                "stop": ["\nCustomer:", "\n\nCustomer:"]  # Clean stop
            }
        }
        
        response = requests.post(
            OLLAMA_API_URL,
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result.get('response', '').strip()
            
            # Validate response quality
            if len(ai_response) < 15:
                return None  # Too short, fall back
            
            return ai_response
        else:
            return None
            
    except requests.exceptions.ConnectionError:
        return None
    except requests.exceptions.Timeout:
        return None
    except Exception as e:
        print(f"Ollama error: {str(e)}")
        return None

def get_bot_response(user_input, conversation_history=None):
    """
    Get bot response with banking restriction and conversational fallback
    """
    # STRICT banking-only check
    if not is_banking_related(user_input):
        return """I apologize, but I can only help with banking and financial questions.

I can assist you with:
• Account services  
• Loans and EMIs
• Money transfers
• Debit and credit cards
• Interest rates

Please ask me something about banking! 🏦""", "restricted"
    
    # Try Ollama first (with full conversation memory)
    ollama_response = call_ollama(user_input, conversation_history)
    
    if ollama_response:
        return ollama_response, "ollama"
    
    # Fallback to chat-like keyword responses
    user_lower = user_input.lower()
    
    # Interest rates / FD
    if any(w in user_lower for w in ['interest', 'rate', 'fd', 'fixed deposit']):
        return """Sure! Here are our interest rates:

**Savings Account:** 3.5% to 4% per year
**Fixed Deposits:**
• 1 year: 6.75%
• 3 years: 7.25%
• 5+ years: 7.50%

Senior citizens get an extra 0.5%! Which type interests you?""", "keyword"
    
    # Transfers
    elif any(w in user_lower for w in ['transfer', 'send money', 'payment']):
        if 'neft' in user_lower:
            return """NEFT is completely free and works 24/7! Your money reaches in 2-3 hours. There's no limit on the amount you can send.

You'll need the receiver's account number, IFSC code, and name. Want to know about other transfer methods?""", "keyword"
        elif 'rtgs' in user_lower:
            return """RTGS is super fast - money reaches in just 30 minutes! 

Charges: ₹25 for 2-5 lakhs, ₹55 for above 5 lakhs
Minimum: ₹2,00,000
Timing: Mon-Fri 8 AM to 4:30 PM, Sat 8 AM to 1 PM

It's perfect for urgent large transfers!""", "keyword"
        elif 'imps' in user_lower:
            return """IMPS is instant - money reaches in seconds!

Works 24/7 including holidays
Max: ₹5,00,000 per transaction
Charges: ₹5 to ₹25 depending on amount

Great for urgent payments anytime!""", "keyword"
        elif 'upi' in user_lower:
            return """UPI is the easiest way - totally free and instant!

Limit: ₹1,00,000 per day
Just need their UPI ID or phone number
Works 24/7

Super convenient for everyday payments!""", "keyword"
        else:
            return """We have 4 transfer options:

**UPI** - Free, instant, up to ₹1 lakh
**NEFT** - Free, 2-3 hours, no limit
**RTGS** - ₹25-₹55, 30 minutes, min ₹2 lakhs
**IMPS** - ₹5-₹25, instant, max ₹5 lakhs

Which one would work best for you?""", "keyword"
    
    # Loans
    elif any(w in user_lower for w in ['loan', 'borrow', 'emi']):
        if 'home' in user_lower:
            return """Home loans are available at 8.5% to 9.5% per year!

Max amount: ₹5 crores
Tenure: Up to 30 years
We fund up to 90% of property value

For ₹25 lakhs at 9% for 20 years, EMI would be around ₹22,500. Interested in applying?""", "keyword"
        elif 'personal' in user_lower:
            return """Personal loans are quick to get!

Amount: ₹50,000 to ₹25,00,000
Interest: 10.5% to 18% (based on credit score)
Tenure: 1 to 5 years

Eligibility: Age 21-60, minimum salary ₹25,000. What amount are you looking for?""", "keyword"
        elif 'car' in user_lower or 'auto' in user_lower:
            return """Car loans at 9% to 12%!

We finance up to 90% of car value
You just pay 10% down payment
Tenure: Up to 7 years

Makes buying your dream car affordable!""", "keyword"
        elif 'education' in user_lower:
            return """Education loans to help you study!

For studies in India: Up to ₹20 lakhs
For studies abroad: Up to ₹50 lakhs
Interest: 9.5% to 12.5%

Best part - you start paying after course ends plus 6 months!""", "keyword"
        else:
            return """We offer these loans:

**Home Loan:** 8.5-9.5%, up to ₹5 crores
**Personal Loan:** 10.5-18%, up to ₹25 lakhs
**Car Loan:** 9-12%, 90% financing
**Education Loan:** 9.5-12.5%, up to ₹50 lakhs

Which loan are you interested in?""", "keyword"
    
    # Account opening
    elif any(w in user_lower for w in ['open', 'account', 'new account']):
        return """Opening an account is easy!

**Documents needed:**
• PAN Card (mandatory)
• Aadhaar Card
• One passport size photo
• Address proof

Takes just 24-48 hours. You can apply online too!

**Minimum balance:** Urban ₹10,000, Rural ₹5,000

Would you like to start the process?""", "keyword"
    
    # Cards
    elif any(w in user_lower for w in ['card', 'debit', 'credit', 'atm']):
        if 'lost' in user_lower or 'stolen' in user_lower:
            return """If your card is lost or stolen, call 1800-XXX-CARD immediately!

We're available 24/7 and will:
• Block your card instantly
• Issue a replacement in 5-7 days

Don't worry, you won't be liable for any fraudulent transactions if reported within 3 days!""", "keyword"
        elif 'credit' in user_lower:
            return """We have 2 credit cards:

**Silver Card:** ₹500/year (free on ₹50k spending)
• Limit: ₹20,000 to ₹2,00,000
• Rewards: 1 point per ₹100

**Gold Card:** ₹2,500/year (free on ₹3L spending)
• Limit: ₹2,00,000 to ₹10,00,000
• Rewards: 2 points per ₹100
• Airport lounge access!

Which one interests you?""", "keyword"
        else:
            return """We have debit and credit cards!

**Debit Cards:**
• Classic: Free 1st year, then ₹200
• Platinum: ₹500 (with lounge access)

**Credit Cards:**
• Silver: ₹500/year
• Gold: ₹2,500/year (premium benefits)

What would you like to know more about?""", "keyword"
    
    # Greetings
    elif any(w in user_lower for w in ['hello', 'hi', 'hey', 'good morning', 'good evening']):
        return "Hello! 👋 I'm BankBot, your banking assistant. How can I help you today? You can ask me about accounts, loans, transfers, cards, or anything banking related!", "keyword"
    
    # Thanks
    elif any(w in user_lower for w in ['thank', 'thanks', 'appreciate']):
        return "You're very welcome! 😊 Feel free to ask if you have any more banking questions. I'm here to help!", "keyword"
    
    # Default
    else:
        return f"""I'd be happy to help you with that banking question!

I can assist with:
• Account services and interest rates
• Loans (home, personal, car, education)
• Money transfers (NEFT, RTGS, IMPS, UPI)
• Debit and credit cards
• General banking info

Could you please ask me more specifically what you'd like to know?""", "keyword"

# Custom CSS with white background and black text
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');
    
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main background - WHITE */
    .stApp {
        background: #FFFFFF !important;
    }
    
    .block-container {
        padding: 2rem 3rem;
        max-width: 100%;
        background: #FFFFFF;
    }
    
    /* All text BLACK */
    p, span, div, label, h1, h2, h3, h4, h5, h6 {
        color: #000000 !important;
    }
    
    /* Login page styles */
    .login-container {
        max-width: 480px;
        margin: 3rem auto;
        background: #FFFFFF;
        border-radius: 24px;
        padding: 3rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        border: 2px solid #e5e7eb;
        animation: fadeIn 0.6s ease-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .login-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .login-logo {
        width: 80px;
        height: 80px;
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        border-radius: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 40px;
        margin: 0 auto 1.5rem auto;
        box-shadow: 0 8px 24px rgba(59, 130, 246, 0.3);
    }
    
    .login-title {
        font-size: 32px;
        font-weight: 700;
        color: #000000 !important;
        margin-bottom: 0.5rem;
        font-family: 'Space Grotesk', sans-serif;
    }
    
    .login-subtitle {
        font-size: 16px;
        color: #000000 !important;
        margin-bottom: 0.5rem;
    }
    
    .login-batch {
        display: inline-block;
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: #FFFFFF !important;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
        margin-top: 0.5rem;
    }
    
    .demo-credentials {
        background: #FFFFFF;
        border: 2px solid #e5e7eb;
        border-radius: 12px;
        padding: 1rem;
        margin-top: 1.5rem;
        font-size: 13px;
    }
    
    .demo-credentials strong {
        color: #000000 !important;
        display: block;
        margin-bottom: 0.5rem;
    }
    
    .demo-credentials p {
        color: #000000 !important;
        margin: 0.25rem 0;
        font-family: 'Courier New', monospace;
    }
    
    .demo-credentials code {
        background: #f3f4f6;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        color: #000000 !important;
    }
    
    /* Sidebar - WHITE background */
    section[data-testid="stSidebar"] {
        background: #FFFFFF !important;
        box-shadow: 4px 0 20px rgba(0,0,0,0.08);
        border-right: 2px solid #e5e7eb;
    }
    
    section[data-testid="stSidebar"] > div {
        padding-top: 2rem;
        background: #FFFFFF;
    }
    
    /* Chat section */
    .chat-hero {
        text-align: center;
        padding: 2rem 0 3rem 0;
        background: #FFFFFF;
    }
    
    .chat-hero h1 {
        font-size: 36px;
        font-weight: 700;
        color: #000000 !important;
        margin-bottom: 0.5rem;
        font-family: 'Space Grotesk', sans-serif;
    }
    
    .chat-hero p {
        font-size: 18px;
        color: #000000 !important;
    }
    
    /* Robot section */
    .robot-container {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 3rem;
        margin: 3rem 0;
        padding: 2rem;
        background: #FFFFFF;
    }
    
    .robot-visual {
        position: relative;
        width: 260px;
        height: 260px;
    }
    
    .robot-glow {
        position: absolute;
        inset: 0;
        background: radial-gradient(circle, rgba(59, 130, 246, 0.15) 0%, transparent 70%);
        animation: pulse 3s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 0.5; }
        50% { transform: scale(1.1); opacity: 0.8; }
    }
    
    .robot-emoji {
        position: relative;
        font-size: 160px;
        filter: drop-shadow(0 10px 30px rgba(59, 130, 246, 0.2));
        animation: float 4s ease-in-out infinite;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-20px); }
    }
    
    .welcome-bubble {
        background: #FFFFFF;
        padding: 2rem 2.5rem;
        border-radius: 24px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        border: 2px solid #e5e7eb;
        position: relative;
        max-width: 420px;
        animation: slideIn 0.6s ease-out;
    }
    
    @keyframes slideIn {
        from { opacity: 0; transform: translateX(30px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    .welcome-bubble::before {
        content: '';
        position: absolute;
        left: -12px;
        top: 50px;
        width: 0;
        height: 0;
        border-top: 12px solid transparent;
        border-bottom: 12px solid transparent;
        border-right: 12px solid #FFFFFF;
        filter: drop-shadow(-2px 0 0 #e5e7eb);
    }
    
    .welcome-bubble h3 {
        font-size: 22px;
        font-weight: 600;
        color: #000000 !important;
        margin-bottom: 0.5rem;
    }
    
    .welcome-bubble p {
        font-size: 18px;
        color: #000000 !important;
        line-height: 1.6;
    }
    
    /* Chat messages */
    .chat-message {
        margin: 1.5rem 0;
        padding: 1.25rem 1.5rem;
        border-radius: 16px;
        animation: fadeInUp 0.4s ease-out;
        background: #FFFFFF;
        border: 2px solid #e5e7eb;
    }
    
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .chat-message.user {
        background: #FFFFFF;
        margin-left: 20%;
        border: 2px solid #3b82f6;
        box-shadow: 0 2px 12px rgba(59, 130, 246, 0.1);
    }
    
    .chat-message.bot {
        background: #FFFFFF;
        margin-right: 20%;
        border: 2px solid #e5e7eb;
        box-shadow: 0 2px 12px rgba(0,0,0,0.05);
    }
    
    .message-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 0.75rem;
    }
    
    .message-avatar {
        width: 36px;
        height: 36px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
    }
    
    .message-avatar.user {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
    }
    
    .message-avatar.bot {
        background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
    }
    
    .message-name {
        font-weight: 600;
        color: #000000 !important;
        font-size: 14px;
    }
    
    .message-time {
        color: #6b7280 !important;
        font-size: 12px;
        margin-left: auto;
    }
    
    .message-content {
        color: #000000 !important;
        line-height: 1.6;
        font-size: 15px;
    }
    
    /* Streamlit button overrides */
    .stButton button {
        background: #FFFFFF !important;
        color: #000000 !important;
        border: 2px solid #e5e7eb !important;
        border-radius: 14px !important;
        padding: 0.875rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        transition: all 0.3s !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
        font-family: 'Inter', sans-serif !important;
        width: 100%;
    }
    
    .stButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px rgba(59, 130, 246, 0.15) !important;
        border-color: #3b82f6 !important;
        background: #f9fafb !important;
    }
    
    /* Primary button styling */
    div[data-testid="column"] button[kind="primary"],
    button[key*="send"],
    button[key*="login"],
    button[key*="signup"] {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        box-shadow: 0 4px 16px rgba(59, 130, 246, 0.3) !important;
    }
    
    div[data-testid="column"] button[kind="primary"]:hover,
    button[key*="send"]:hover,
    button[key*="login"]:hover,
    button[key*="signup"]:hover {
        box-shadow: 0 8px 24px rgba(59, 130, 246, 0.4) !important;
        transform: translateY(-2px) !important;
    }
    
    /* Text input styling */
    .stTextInput input {
        border: 2px solid #e5e7eb !important;
        border-radius: 12px !important;
        padding: 0.875rem 1rem !important;
        font-size: 15px !important;
        color: #000000 !important;
        background: #FFFFFF !important;
        transition: all 0.3s !important;
    }
    
    .stTextInput input:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
        outline: none !important;
    }
    
    .stTextInput input::placeholder {
        color: #6b7280 !important;
    }
    
    .stTextInput label {
        color: #000000 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* Textarea styling */
    .stTextArea textarea {
        border: 2px solid #e5e7eb !important;
        border-radius: 12px !important;
        padding: 0.875rem 1rem !important;
        font-size: 15px !important;
        color: #000000 !important;
        background: #FFFFFF !important;
        transition: all 0.3s !important;
    }
    
    .stTextArea textarea:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
        outline: none !important;
    }
    
    .stTextArea textarea::placeholder {
        color: #6b7280 !important;
    }
    
    .stTextArea label {
        color: #000000 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* Selectbox styling */
    .stSelectbox select {
        border: 2px solid #e5e7eb !important;
        border-radius: 12px !important;
        padding: 0.875rem 1rem !important;
        font-size: 15px !important;
        color: #000000 !important;
        background: #FFFFFF !important;
        transition: all 0.3s !important;
    }
    
    .stSelectbox select:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
        outline: none !important;
        background: #FFFFFF !important;
    }
    
    .stSelectbox label {
        color: #000000 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        margin-bottom: 0.5rem !important;
    }
    
    .stSelectbox > div > div {
        background: #FFFFFF !important;
        border: 2px solid #e5e7eb !important;
        border-radius: 12px !important;
    }
    
    .stSelectbox option {
        background: #FFFFFF !important;
        color: #000000 !important;
        padding: 0.5rem !important;
    }
    
    /* Streamlit selectbox internal styling */
    [data-baseweb="select"] {
        background: #FFFFFF !important;
    }
    
    [data-baseweb="select"] > div {
        background: #FFFFFF !important;
        border: 2px solid #e5e7eb !important;
        color: #000000 !important;
    }
    
    [data-baseweb="popover"] {
        background: #FFFFFF !important;
    }
    
    [data-baseweb="menu"] {
        background: #FFFFFF !important;
    }
    
    [role="option"] {
        background: #FFFFFF !important;
        color: #000000 !important;
    }
    
    [role="option"]:hover {
        background: #f3f4f6 !important;
        color: #000000 !important;
    }
    
    ul[role="listbox"] {
        background: #FFFFFF !important;
        border: 2px solid #e5e7eb !important;
        border-radius: 12px !important;
    }
    
    ul[role="listbox"] li {
        background: #FFFFFF !important;
        color: #000000 !important;
        padding: 0.75rem 1rem !important;
    }
    
    ul[role="listbox"] li:hover {
        background: #f3f4f6 !important;
    }
    
    /* Number input styling */
    .stNumberInput input {
        border: 2px solid #e5e7eb !important;
        border-radius: 12px !important;
        padding: 0.875rem 1rem !important;
        font-size: 15px !important;
        color: #000000 !important;
        background: #FFFFFF !important;
        transition: all 0.3s !important;
    }
    
    .stNumberInput input:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
        outline: none !important;
    }
    
    .stNumberInput label {
        color: #000000 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        margin-bottom: 0.5rem !important;
    }
    
    .stNumberInput > div > div {
        background: #FFFFFF !important;
        border: 2px solid #e5e7eb !important;
    }
    
    /* File uploader styling */
    .stFileUploader {
        background: #FFFFFF !important;
        border: 2px solid #e5e7eb !important;
        border-radius: 12px !important;
        padding: 1rem !important;
    }
    
    .stFileUploader label {
        color: #000000 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    
    .stFileUploader section {
        background: #FFFFFF !important;
        border: 2px dashed #e5e7eb !important;
    }
    
    .stFileUploader section small {
        color: #6b7280 !important;
    }
    
    /* Date input styling */
    .stDateInput input {
        border: 2px solid #e5e7eb !important;
        border-radius: 12px !important;
        padding: 0.875rem 1rem !important;
        font-size: 15px !important;
        color: #000000 !important;
        background: #FFFFFF !important;
        transition: all 0.3s !important;
    }
    
    .stDateInput input:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
        outline: none !important;
    }
    
    .stDateInput label {
        color: #000000 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* Checkbox styling */
    .stCheckbox label {
        color: #000000 !important;
        font-size: 15px !important;
    }
    
    .stCheckbox span {
        color: #000000 !important;
    }
    
    /* Sidebar styling */
    .sidebar-title {
        padding: 0 1.5rem;
        margin-bottom: 2rem;
    }
    
    .sidebar-title h2 {
        font-size: 22px;
        font-weight: 700;
        color: #000000 !important;
        font-family: 'Space Grotesk', sans-serif;
    }
    
    /* User profile in sidebar */
    .user-profile {
        background: #FFFFFF;
        padding: 1rem 1.25rem;
        border-radius: 14px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        border: 2px solid #e5e7eb;
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    
    .profile-avatar {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        box-shadow: 0 2px 8px rgba(139, 92, 246, 0.3);
    }
    
    .profile-info h4 {
        font-weight: 600;
        color: #000000 !important;
        font-size: 14px;
        margin-bottom: 2px;
    }
    
    .profile-info p {
        font-size: 12px;
        color: #6b7280 !important;
    }
    
    /* Success/Error/Info messages */
    .stSuccess {
        background: #FFFFFF !important;
        border: 2px solid #10b981 !important;
        border-radius: 12px !important;
        padding: 1rem 1.25rem !important;
        color: #000000 !important;
    }
    
    .stError {
        background: #FFFFFF !important;
        border: 2px solid #ef4444 !important;
        border-radius: 12px !important;
        padding: 1rem 1.25rem !important;
        color: #000000 !important;
    }
    
    .stInfo {
        background: #FFFFFF !important;
        border: 2px solid #3b82f6 !important;
        border-radius: 12px !important;
        padding: 1rem 1.25rem !important;
        color: #000000 !important;
    }
    
    .stWarning {
        background: #FFFFFF !important;
        border: 2px solid #f59e0b !important;
        border-radius: 12px !important;
        padding: 1rem 1.25rem !important;
        color: #000000 !important;
    }
    
    /* Tab styling */
    button[data-baseweb="tab"] {
        background: #FFFFFF !important;
        color: #000000 !important;
        border-radius: 10px !important;
        padding: 10px 24px !important;
        font-weight: 500 !important;
        border: 2px solid #e5e7eb !important;
    }
    
    button[data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
        border: none !important;
    }
    
    button[data-baseweb="tab"] p {
        color: #000000 !important;
    }
    
    button[data-baseweb="tab"][aria-selected="true"] p {
        color: #FFFFFF !important;
    }
    
    /* Metric styling */
    [data-testid="stMetricValue"] {
        color: #000000 !important;
        font-size: 28px !important;
        font-weight: 700 !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #000000 !important;
        font-weight: 600 !important;
    }
    
    [data-testid="stMetricDelta"] {
        color: #000000 !important;
    }
    
    /* Ensure all headings are black */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
        color: #000000 !important;
    }
    
    /* List items */
    li {
        color: #000000 !important;
    }
    
    /* HR separator */
    hr {
        border-color: #e5e7eb !important;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'FAQs'
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []
if 'chat_sessions' not in st.session_state:
    st.session_state.chat_sessions = []  # List of all conversation sessions
if 'current_session_id' not in st.session_state:
    st.session_state.current_session_id = None
if 'sidebar_menu' not in st.session_state:
    st.session_state.sidebar_menu = 'FAQs'
if 'users_db' not in st.session_state:
    st.session_state.users_db = {
        "admin": hashlib.sha256("admin123".encode()).hexdigest(),
        "demo": hashlib.sha256("demo123".encode()).hexdigest(),
        "user": hashlib.sha256("user123".encode()).hexdigest(),
    }

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def login_page():
    """Display login/signup page"""
    st.markdown("""
        <div class="login-container">
            <div class="login-header">
                <div class="login-logo">🏦</div>
                <h1 class="login-title">BankBot AI</h1>
                <p class="login-subtitle">Your 24/7 Banking Assistant</p>
                <span class="login-batch">Batch 13</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Create tabs for Login and Signup
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
    
    with tab1:
        st.markdown("### Welcome Back!")
        st.markdown("Please enter your credentials to continue")
        
        login_username = st.text_input("Username", placeholder="Enter your username", key="login_username")
        login_password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚀 Login", key="login_btn", use_container_width=True, type="primary"):
                if login_username and login_password:
                    hashed_pw = hash_password(login_password)
                    if login_username in st.session_state.users_db and st.session_state.users_db[login_username] == hashed_pw:
                        st.session_state.authenticated = True
                        st.session_state.username = login_username
                        st.success(f"✅ Welcome back, {login_username}!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
                else:
                    st.warning("⚠️ Please enter both username and password")
        
        with col2:
            if st.button("👤 Guest Login", key="guest_login", use_container_width=True):
                st.session_state.authenticated = True
                st.session_state.username = "Guest"
                st.success("✅ Logged in as Guest!")
                time.sleep(1)
                st.rerun()
        
        st.markdown("""
            <div class="demo-credentials">
                <strong>🔑 Demo Credentials:</strong>
                <p>Username: <code>demo</code> | Password: <code>demo123</code></p>
                <p>Username: <code>admin</code> | Password: <code>admin123</code></p>
                <p>Username: <code>user</code> | Password: <code>user123</code></p>
            </div>
        """, unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### Create New Account")
        st.markdown("Join BankBot AI for seamless banking assistance")
        
        signup_username = st.text_input("Choose Username", placeholder="Enter username", key="signup_username")
        signup_email = st.text_input("Email Address", placeholder="Enter your email", key="signup_email")
        signup_password = st.text_input("Choose Password", type="password", placeholder="Create a password", key="signup_password")
        signup_confirm = st.text_input("Confirm Password", type="password", placeholder="Re-enter password", key="signup_confirm")
        
        if st.button("✨ Create Account", key="signup_btn", use_container_width=True, type="primary"):
            if signup_username and signup_email and signup_password and signup_confirm:
                if signup_username in st.session_state.users_db:
                    st.error("❌ Username already exists. Please choose another.")
                elif signup_password != signup_confirm:
                    st.error("❌ Passwords don't match!")
                elif len(signup_password) < 6:
                    st.error("❌ Password must be at least 6 characters long")
                else:
                    st.session_state.users_db[signup_username] = hash_password(signup_password)
                    st.success(f"✅ Account created successfully! Welcome, {signup_username}!")
                    time.sleep(1)
                    st.session_state.authenticated = True
                    st.session_state.username = signup_username
                    st.rerun()
            else:
                st.warning("⚠️ Please fill in all fields")

def main_app():
    """Main application after login"""
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"""
            <div class="sidebar-title">
                <h2>🏦 BankBot AI</h2>
            </div>
        """, unsafe_allow_html=True)
        
        menu_items = [
            ("🏠", "Dashboard"),
            ("💼", "Accounts"),
            ("💸", "Transfer"),
            ("💬", "FAQs"),
            ("📜", "Chat History"),
            ("🎧", "Support"),
        ]
        
        for icon, label in menu_items:
            if st.button(f"{icon}  {label}", key=f"menu_{label}", use_container_width=True):
                st.session_state.sidebar_menu = label
                st.session_state.current_page = label
                st.rerun()
        
        st.markdown("<br>" * 2, unsafe_allow_html=True)
        
        # Ollama Status Indicator
        try:
            test_response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if test_response.status_code == 200:
                st.success("🤖 AI Mode: Active (Ollama)")
            else:
                st.warning("⚠️ AI Mode: Fallback")
        except:
            st.warning("⚠️ AI Mode: Fallback")
        
        # Add flexible spacing that pushes profile and logout to bottom
        st.markdown("<br>" * 3, unsafe_allow_html=True)
        
        # User profile - positioned above logout
        st.markdown(f"""
            <div class="user-profile">
                <div class="profile-avatar">👤</div>
                <div class="profile-info">
                    <h4>{st.session_state.username}</h4>
                    <p>{st.session_state.username.lower()}@bankbot.ai</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Logout button - positioned at bottom
        if st.button("🚪 Logout", key="logout_btn", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = ""
            st.session_state.chat_messages = []
            st.success("👋 Logged out successfully!")
            time.sleep(1)
            st.rerun()
    
    # Main content - removed top header and navigation tabs
    
    # Page content
    if st.session_state.current_page == "FAQs":
        st.markdown("""
            <div class="chat-hero">
                <h1>Ask our Banking AI Chatbot</h1>
                <p>How can I assist you today?</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
            <div class="robot-container">
                <div class="robot-visual">
                    <div class="robot-glow"></div>
                    <div class="robot-emoji">🤖</div>
                </div>
                <div class="welcome-bubble">
                    <h3>Hello!</h3>
                    <p>How can I help you today? 👋</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Action cards
        actions = [
            ("🔑", "Forgotten my PIN"),
            ("💳", "Check Account Balance"),
            ("⚠️", "Report a Lost Card"),
            ("💵", "How to Deposit a Check?"),
            ("🚨", "Block My Card"),
            ("↩️", "Chargeback Request"),
        ]
        
        cols = st.columns(3)
        for idx, (icon, text) in enumerate(actions):
            with cols[idx % 3]:
                if st.button(f"{icon} {text}", key=f"action_{idx}", use_container_width=True):
                    st.session_state.chat_messages.append({
                        "role": "user",
                        "content": text,
                        "timestamp": datetime.now().strftime("%I:%M %p")
                    })
                    
                    responses = {
                        "Forgotten my PIN": "No problem! I can help you reset your PIN. You can reset it via our mobile app, at any ATM, or by calling our 24/7 helpline at 1-800-BANK-PIN. Which method would you prefer?",
                        "Check Account Balance": "I'd be happy to help you check your account balance. Please log in to your secure portal, or check via our mobile app. Your current balance will be displayed immediately. Would you like me to guide you through the process?",
                        "Report a Lost Card": "I'm sorry to hear that! For your security, I'll help you block your card immediately. Please call our emergency hotline at 1-800-CARD-LOST or use the 'Block Card' feature in our mobile app. Have you noticed any unauthorized transactions?",
                        "How to Deposit a Check?": "You can deposit checks in three convenient ways: 1) Using our mobile app (take a photo of the check), 2) At any of our ATMs with deposit functionality, or 3) At any branch location. Which method works best for you?",
                        "Block My Card": "I'll help you block your card immediately for security. Please confirm your card details, and I'll process the block. You can also do this instantly via our mobile app. Would you like to order a replacement card as well?",
                        "Chargeback Request": "I can help you file a chargeback request. Please provide the transaction details including date, amount, and merchant name. You can also submit the request through our mobile app under 'Dispute Transaction'. Do you have the transaction information ready?"
                    }
                    
                    bot_response = responses.get(text, f"I understand you need help with '{text}'. Let me connect you with the right resources.")
                    
                    st.session_state.chat_messages.append({
                        "role": "bot",
                        "content": bot_response,
                        "timestamp": datetime.now().strftime("%I:%M %p")
                    })
                    st.success(f"✅ Added to chat: {text}")
                    time.sleep(0.5)
                    st.rerun()
        
        # Quick Questions
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Quick Questions")
        
        questions = [
            "What are your interest rates?",
            "How to open an account?",
            "What are the loan options?",
            "Are there any fees?",
            "How to update my info?",
            "Transfer limits and fees?",
        ]
        
        q_cols = st.columns(3)
        for idx, question in enumerate(questions):
            with q_cols[idx % 3]:
                if st.button(f"{question} →", key=f"q_{idx}", use_container_width=True):
                    st.session_state.chat_messages.append({
                        "role": "user",
                        "content": question,
                        "timestamp": datetime.now().strftime("%I:%M %p")
                    })
                    
                    quick_responses = {
                        "What are your interest rates?": "Our current interest rates vary by account type:\n\n💰 Savings Accounts: 3.5%-4.0% APY\n📈 Fixed Deposits: 5.5%-7.0% APY (depending on tenure)\n💼 Current Accounts: Non-interest bearing\n\nWould you like detailed information on any specific account type?",
                        "How to open an account?": "Opening an account is easy! You'll need:\n\n✅ Valid government ID\n✅ Proof of address\n✅ PAN card\n✅ Initial deposit (₹500-₹10,000 depending on account type)\n\nYou can apply online in 10 minutes or visit any branch. Shall I guide you through the online process?",
                        "What are the loan options?": "We offer various loan products:\n\n🏠 Personal Loans (up to ₹25 lakhs)\n🏡 Home Loans (up to 90% property value)\n🚗 Auto Loans\n📚 Education Loans\n💼 Business Loans\n\nInterest rates start from 8.5% p.a. Which loan type interests you?",
                        "Are there any fees?": "Here's a quick overview of fees:\n\n💳 Account maintenance: ₹0-₹500/year\n🏧 ATM withdrawals: First 5 free, then ₹20/transaction\n💳 Debit card: ₹0-₹500/year\n💳 Credit card: ₹500-₹5000/year\n\nWould you like details on any specific fee?",
                        "How to update my info?": "You can update your information through:\n\n📱 Mobile Banking App (for phone/email)\n💻 Internet Banking portal\n🏦 Visit nearest branch with ID proof\n\nWhat information do you need to update?",
                        "Transfer limits and fees?": "Transfer limits:\n\n💸 NEFT/RTGS: No limit\n⚡ IMPS: ₹5 lakhs per transaction\n📲 UPI: ₹1 lakh per transaction\n\nFees:\n✅ NEFT: Free\n💰 RTGS: ₹25-₹55\n⚡ IMPS: ₹5-₹15\n\nNeed help with a transfer?"
                    }
                    
                    bot_response = quick_responses.get(question, f"Great question! Let me help you with '{question}'.")
                    
                    st.session_state.chat_messages.append({
                        "role": "bot",
                        "content": bot_response,
                        "timestamp": datetime.now().strftime("%I:%M %p")
                    })
                    st.success(f"✅ Added to chat: {question}")
                    time.sleep(0.5)
                    st.rerun()
        
        # Display chat messages
        if st.session_state.chat_messages:
            st.markdown("---")
            st.markdown("### 💬 Your Conversation")
            
            for msg in st.session_state.chat_messages:
                if msg["role"] == "user":
                    st.markdown(f"""
                        <div class="chat-message user">
                            <div class="message-header">
                                <div class="message-avatar user">👤</div>
                                <span class="message-name">You</span>
                                <span class="message-time">{msg["timestamp"]}</span>
                            </div>
                            <div class="message-content">{msg["content"]}</div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div class="chat-message bot">
                            <div class="message-header">
                                <div class="message-avatar bot">🤖</div>
                                <span class="message-name">BankBot</span>
                                <span class="message-time">{msg["timestamp"]}</span>
                            </div>
                            <div class="message-content">{msg["content"]}</div>
                        </div>
                    """, unsafe_allow_html=True)
        
        # Chat input
        st.markdown("---")
        col1, col2 = st.columns([5, 1])
        
        with col1:
            user_input = st.text_input(
                "Type your message",
                placeholder="Type your question here...",
                label_visibility="collapsed",
                key=f"chat_input_{len(st.session_state.chat_messages)}"  # Dynamic key to clear input
            )
        
        with col2:
            send_btn = st.button("Send ✈️", key="send", use_container_width=True, type="primary")
        
        if send_btn and user_input:
            # Add user message
            st.session_state.chat_messages.append({
                "role": "user",
                "content": user_input,
                "timestamp": datetime.now().strftime("%I:%M %p")
            })
            
            # Show typing indicator
            with st.spinner("🤖 BankBot is thinking..."):
                # Get AI response using Ollama or fallback
                bot_response, response_type = get_bot_response(
                    user_input, 
                    st.session_state.chat_messages
                )
            
            # Add bot message with response type indicator
            st.session_state.chat_messages.append({
                "role": "bot",
                "content": bot_response,
                "timestamp": datetime.now().strftime("%I:%M %p"),
                "type": response_type  # "ollama" or "keyword"
            })
            
            # Show indicator if using fallback
            if response_type == "keyword":
                st.info("💡 Tip: Start Ollama for AI-powered responses! Currently using fallback mode.")
            
            st.rerun()
    
    elif st.session_state.current_page == "Chat History":
        st.markdown("""
            <div class="chat-hero">
                <h1>📜 Chat History</h1>
                <p>Your conversation sessions</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Action buttons
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col1:
            if st.button("➕ Start New Conversation", key="new_conv", use_container_width=True, type="primary"):
                # Save current session if it has messages
                if st.session_state.chat_messages:
                    session_title = "New Conversation"
                    if len(st.session_state.chat_messages) > 0:
                        # Use first user message as title
                        first_msg = next((m['content'] for m in st.session_state.chat_messages if m['role'] == 'user'), 'New Chat')
                        session_title = first_msg[:50] + "..." if len(first_msg) > 50 else first_msg
                    
                    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    st.session_state.chat_sessions.append({
                        'id': session_id,
                        'title': session_title,
                        'messages': st.session_state.chat_messages.copy(),
                        'created_at': datetime.now().strftime("%B %d, %Y at %I:%M %p"),
                        'message_count': len(st.session_state.chat_messages)
                    })
                
                # Start new session
                st.session_state.chat_messages = []
                st.session_state.current_session_id = None
                st.session_state.current_page = "FAQs"
                st.success("✅ New conversation started!")
                time.sleep(0.5)
                st.rerun()
        
        with col3:
            if st.button("🗑️ Clear All History", key="clear_all_history", use_container_width=True):
                st.session_state.chat_sessions = []
                st.session_state.chat_messages = []
                st.success("✅ All chat history cleared!")
                time.sleep(1)
                st.rerun()
        
        st.markdown("---")
        
        # Current active session
        if st.session_state.chat_messages:
            st.markdown("### 💬 Current Active Session")
            
            # Get session title
            first_msg = next((m['content'] for m in st.session_state.chat_messages if m['role'] == 'user'), 'Ongoing Chat')
            session_title = first_msg[:60] + "..." if len(first_msg) > 60 else first_msg
            
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); padding: 1.5rem; border-radius: 16px; border: 2px solid #3b82f6; margin-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h4 style="color: #000000; margin: 0 0 0.5rem 0;">🟢 {session_title}</h4>
                            <p style="color: #000000; margin: 0; font-size: 14px;">💬 {len(st.session_state.chat_messages)} messages • Active now</p>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📖 View Messages", key="view_current", use_container_width=True):
                    st.session_state.current_page = "FAQs"
                    st.rerun()
            with col2:
                if st.button("💾 Save & Start New", key="save_current", use_container_width=True):
                    # Save current session
                    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    st.session_state.chat_sessions.append({
                        'id': session_id,
                        'title': session_title,
                        'messages': st.session_state.chat_messages.copy(),
                        'created_at': datetime.now().strftime("%B %d, %Y at %I:%M %p"),
                        'message_count': len(st.session_state.chat_messages)
                    })
                    st.session_state.chat_messages = []
                    st.session_state.current_session_id = None
                    st.success("✅ Session saved! Starting new conversation...")
                    time.sleep(1)
                    st.rerun()
            
            st.markdown("---")
        
        # Past sessions
        if st.session_state.chat_sessions:
            st.markdown(f"### 📚 Past Conversations ({len(st.session_state.chat_sessions)})")
            
            # Sort sessions by creation time (newest first)
            sorted_sessions = sorted(st.session_state.chat_sessions, 
                                    key=lambda x: x['created_at'], 
                                    reverse=True)
            
            for idx, session in enumerate(sorted_sessions):
                # Create session card
                st.markdown(f"""
                    <div style="background: white; padding: 1.5rem; border-radius: 16px; border: 2px solid #e5e7eb; margin-bottom: 1rem; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.75rem;">
                            <div style="flex: 1;">
                                <h4 style="color: #000000; margin: 0 0 0.5rem 0; font-size: 16px;">💬 {session['title']}</h4>
                                <p style="color: #6b7280; margin: 0; font-size: 13px;">
                                    📅 {session['created_at']} • 💬 {session['message_count']} messages
                                </p>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Action buttons for each session
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button(f"📖 View", key=f"view_{session['id']}", use_container_width=True):
                        # Load this session
                        st.session_state.chat_messages = session['messages'].copy()
                        st.session_state.current_session_id = session['id']
                        st.session_state.current_page = "FAQs"
                        st.info(f"✅ Loaded: {session['title']}")
                        time.sleep(0.5)
                        st.rerun()
                
                with col2:
                    if st.button(f"📥 Export", key=f"export_{session['id']}", use_container_width=True):
                        # Create export text
                        export_text = f"# {session['title']}\n\n"
                        export_text += f"Date: {session['created_at']}\n"
                        export_text += f"Messages: {session['message_count']}\n\n"
                        export_text += "---\n\n"
                        
                        for msg in session['messages']:
                            role = "You" if msg['role'] == 'user' else "BankBot"
                            export_text += f"**{role}** ({msg['timestamp']})\n"
                            export_text += f"{msg['content']}\n\n"
                        
                        st.download_button(
                            label="💾 Download",
                            data=export_text,
                            file_name=f"conversation_{session['id']}.txt",
                            mime="text/plain",
                            key=f"download_{session['id']}"
                        )
                
                with col3:
                    if st.button(f"🗑️ Delete", key=f"delete_{session['id']}", use_container_width=True):
                        # Remove session
                        st.session_state.chat_sessions = [
                            s for s in st.session_state.chat_sessions 
                            if s['id'] != session['id']
                        ]
                        st.success(f"✅ Deleted: {session['title']}")
                        time.sleep(0.5)
                        st.rerun()
                
                st.markdown("<br>", unsafe_allow_html=True)
        
        else:
            st.info("📭 No saved conversations yet. Start chatting to create your first session!")
            
            if st.button("💬 Start First Conversation", key="first_conv", use_container_width=False):
                st.session_state.current_page = "FAQs"
                st.rerun()
    
    elif st.session_state.current_page == "Dashboard":
        st.markdown("""
            <div class="chat-hero">
                <h1>📊 Dashboard</h1>
                <p>Your BankBot Analytics Overview</p>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        user_messages = len([m for m in st.session_state.chat_messages if m["role"] == "user"])
        bot_messages = len([m for m in st.session_state.chat_messages if m["role"] == "bot"])
        total_messages = len(st.session_state.chat_messages)
        
        with col1:
            st.metric(
                label="💬 Total Conversations",
                value=user_messages,
                delta="Active"
            )
        
        with col2:
            st.metric(
                label="📨 Total Messages",
                value=total_messages,
                delta=f"+{total_messages}"
            )
        
        with col3:
            st.metric(
                label="✅ Queries Resolved",
                value=bot_messages,
                delta="100%"
            )
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🌟 Popular Topics")
            topics = [
                "💳 Account Services",
                "🔒 Security & PIN Management",
                "💰 Loans & Interest Rates",
                "📱 Digital Banking",
                "💸 Transfers & Payments",
                "📞 Customer Support"
            ]
            for topic in topics:
                st.markdown(f"- {topic}")
        
        with col2:
            st.markdown("### 📊 Quick Stats")
            st.info(f"👤 **User:** {st.session_state.username}")
            st.success("✅ **System Status:** All services operational")
            st.info("🤖 **BankBot:** Ready to assist 24/7")
            st.success(f"⏰ **Session Time:** {datetime.now().strftime('%I:%M %p')}")
        
        st.markdown("---")
        st.markdown("### 🚀 Quick Actions")
        
        cols = st.columns(4)
        quick_actions = [
            ("💬", "Start New Chat", "FAQs"),
            ("📜", "View History", "Chat History"),
            ("🎧", "Get Support", "Support"),
            ("💼", "My Accounts", "Accounts")
        ]
        
        for idx, (icon, text, page) in enumerate(quick_actions):
            with cols[idx]:
                if st.button(f"{icon}\n\n{text}", key=f"quick_{idx}", use_container_width=True):
                    st.session_state.current_page = page
                    st.rerun()
    
    elif st.session_state.current_page == "Accounts":
        st.markdown("""
            <div class="chat-hero">
                <h1>💼 My Accounts</h1>
                <p>Manage your bank accounts and view details</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Account Summary Cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
                <div style="background: white; padding: 1.5rem; border-radius: 16px; border: 2px solid #e5e7eb; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                    <h3 style="color: #000000; margin-bottom: 1rem;">💳 Savings Account</h3>
                    <p style="color: #6b7280; font-size: 14px;">Account No: XXXX 1234</p>
                    <h2 style="color: #10b981; margin: 1rem 0;">₹1,24,500.00</h2>
                    <p style="color: #6b7280; font-size: 13px;">Available Balance</p>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
                <div style="background: white; padding: 1.5rem; border-radius: 16px; border: 2px solid #e5e7eb; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                    <h3 style="color: #000000; margin-bottom: 1rem;">🏦 Current Account</h3>
                    <p style="color: #6b7280; font-size: 14px;">Account No: XXXX 5678</p>
                    <h2 style="color: #3b82f6; margin: 1rem 0;">₹45,750.00</h2>
                    <p style="color: #6b7280; font-size: 13px;">Available Balance</p>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
                <div style="background: white; padding: 1.5rem; border-radius: 16px; border: 2px solid #e5e7eb; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                    <h3 style="color: #000000; margin-bottom: 1rem;">📈 Fixed Deposit</h3>
                    <p style="color: #6b7280; font-size: 14px;">FD No: XXXX 9012</p>
                    <h2 style="color: #f59e0b; margin: 1rem 0;">₹5,00,000.00</h2>
                    <p style="color: #6b7280; font-size: 13px;">Maturity: Dec 2026</p>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Account Actions
        st.markdown("### 🔧 Account Actions")
        
        cols = st.columns(4)
        
        account_actions = [
            ("📊", "View Statement"),
            ("📥", "Download Passbook"),
            ("🔄", "Recent Transactions"),
            ("⚙️", "Account Settings")
        ]
        
        for idx, (icon, action) in enumerate(account_actions):
            with cols[idx]:
                if st.button(f"{icon}\n\n{action}", key=f"acc_action_{idx}", use_container_width=True):
                    st.success(f"✅ {action} feature coming soon!")
        
        st.markdown("---")
        
        # Recent Transactions
        st.markdown("### 📝 Recent Transactions")
        
        transactions = [
            ("🛒", "Amazon Purchase", "-₹2,450.00", "Feb 15, 2026", "Debit"),
            ("💰", "Salary Credited", "+₹65,000.00", "Feb 14, 2026", "Credit"),
            ("🍕", "Swiggy Order", "-₹850.00", "Feb 13, 2026", "Debit"),
            ("⚡", "Electricity Bill", "-₹1,200.00", "Feb 12, 2026", "Debit"),
            ("📱", "Mobile Recharge", "-₹399.00", "Feb 11, 2026", "Debit"),
        ]
        
        for emoji, desc, amount, date, type_tx in transactions:
            color = "#10b981" if type_tx == "Credit" else "#ef4444"
            st.markdown(f"""
                <div style="background: white; padding: 1rem 1.5rem; margin: 0.5rem 0; border-radius: 12px; border: 2px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center;">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <span style="font-size: 24px;">{emoji}</span>
                        <div>
                            <p style="color: #000000; font-weight: 600; margin: 0;">{desc}</p>
                            <p style="color: #6b7280; font-size: 13px; margin: 0;">{date}</p>
                        </div>
                    </div>
                    <p style="color: {color}; font-weight: 700; font-size: 18px; margin: 0;">{amount}</p>
                </div>
            """, unsafe_allow_html=True)
    
    elif st.session_state.current_page == "Transfer":
        st.markdown("""
            <div class="chat-hero">
                <h1>💸 Transfer Money</h1>
                <p>Send money quickly and securely</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Transfer Options
        st.markdown("### 💳 Choose Transfer Method")
        
        cols = st.columns(4)
        
        transfer_methods = [
            ("💰", "UPI Transfer", "Instant & Free", "#10b981"),
            ("🏦", "NEFT", "Free Transfer", "#3b82f6"),
            ("⚡", "RTGS", "₹25-₹55 Fee", "#f59e0b"),
            ("📲", "IMPS", "₹5-₹15 Fee", "#8b5cf6")
        ]
        
        for idx, (emoji, method, desc, color) in enumerate(transfer_methods):
            with cols[idx]:
                st.markdown(f"""
                    <div style="background: white; padding: 1.5rem; border-radius: 16px; border: 2px solid #e5e7eb; text-align: center; cursor: pointer; transition: all 0.3s;">
                        <div style="font-size: 40px; margin-bottom: 0.5rem;">{emoji}</div>
                        <h4 style="color: #000000; margin: 0.5rem 0;">{method}</h4>
                        <p style="color: {color}; font-size: 13px; margin: 0;">{desc}</p>
                    </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Transfer Form
        st.markdown("### 📤 Quick Transfer")
        
        col1, col2 = st.columns(2)
        
        with col1:
            from_account = st.selectbox(
                "From Account",
                ["Savings Account (XXXX 1234) - ₹1,24,500", "Current Account (XXXX 5678) - ₹45,750"]
            )
            
            beneficiary = st.selectbox(
                "To Beneficiary",
                ["Add New Beneficiary", "John Smith - 1234567890", "Jane Doe - 9876543210", "ABC Company - 5555555555"]
            )
            
            amount = st.number_input("Amount (₹)", min_value=1, max_value=100000, value=1000, step=100)
        
        with col2:
            transfer_type = st.selectbox(
                "Transfer Type",
                ["UPI (Instant & Free)", "NEFT (Free)", "RTGS (₹25-₹55)", "IMPS (₹5-₹15)"]
            )
            
            remarks = st.text_input("Remarks (Optional)", placeholder="Enter transfer purpose")
            
            schedule = st.checkbox("Schedule for later")
            
            if schedule:
                transfer_date = st.date_input("Transfer Date")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col2:
            if st.button("💸 Transfer Now", key="transfer_now", use_container_width=True, type="primary"):
                st.success(f"✅ Transfer of ₹{amount:,.2f} initiated successfully!")
                st.info("📧 You will receive a confirmation SMS and email shortly.")
        
        st.markdown("---")
        
        # Transfer Limits
        st.markdown("### 📊 Daily Transfer Limits")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
                <div style="background: white; padding: 1.5rem; border-radius: 12px; border: 2px solid #e5e7eb;">
                    <h4 style="color: #000000; margin-bottom: 1rem;">💰 UPI Limits</h4>
                    <p style="color: #000000;">• Per Transaction: ₹1,00,000</p>
                    <p style="color: #000000;">• Daily Limit: ₹1,00,000</p>
                    <p style="color: #000000;">• Monthly Limit: ₹30,00,000</p>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
                <div style="background: white; padding: 1.5rem; border-radius: 12px; border: 2px solid #e5e7eb;">
                    <h4 style="color: #000000; margin-bottom: 1rem;">🏦 NEFT/RTGS Limits</h4>
                    <p style="color: #000000;">• NEFT: No upper limit</p>
                    <p style="color: #000000;">• RTGS: Minimum ₹2,00,000</p>
                    <p style="color: #000000;">• IMPS: ₹5,00,000 per transaction</p>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Recent Beneficiaries
        st.markdown("### 👥 Recent Beneficiaries")
        
        beneficiaries = [
            ("👤", "John Smith", "9876543210", "₹5,000"),
            ("👤", "Jane Doe", "8765432109", "₹2,500"),
            ("🏢", "ABC Company", "7654321098", "₹10,000"),
            ("👤", "Bob Wilson", "6543210987", "₹1,200")
        ]
        
        cols = st.columns(4)
        
        for idx, (icon, name, number, last_amt) in enumerate(beneficiaries):
            with cols[idx]:
                if st.button(f"{icon}\n\n{name}\n{number}\n\nLast: {last_amt}", key=f"benef_{idx}", use_container_width=True):
                    st.info(f"✅ Selected beneficiary: {name}")
    
    elif st.session_state.current_page == "Support":
        st.markdown("""
            <div class="chat-hero">
                <h1>🎧 Customer Support</h1>
                <p>We're here to help you 24/7</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Contact Methods
        st.markdown("### 📞 Contact Us")
        
        cols = st.columns(4)
        
        contact_methods = [
            ("📞", "Call Us", "1800-XXX-XXXX", "24/7 Available"),
            ("📧", "Email", "support@bankbot.ai", "Reply in 24hrs"),
            ("💬", "Live Chat", "Chat with Agent", "9 AM - 9 PM"),
            ("🌐", "Visit Branch", "Find Nearest", "500+ Branches")
        ]
        
        for idx, (emoji, method, detail, timing) in enumerate(contact_methods):
            with cols[idx]:
                st.markdown(f"""
                    <div style="background: white; padding: 1.5rem; border-radius: 16px; border: 2px solid #e5e7eb; text-align: center;">
                        <div style="font-size: 40px; margin-bottom: 0.5rem;">{emoji}</div>
                        <h4 style="color: #000000; margin: 0.5rem 0;">{method}</h4>
                        <p style="color: #3b82f6; font-size: 14px; font-weight: 600; margin: 0.25rem 0;">{detail}</p>
                        <p style="color: #6b7280; font-size: 12px; margin: 0;">{timing}</p>
                    </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Raise a Ticket
        st.markdown("### 🎫 Raise a Support Ticket")
        
        col1, col2 = st.columns(2)
        
        with col1:
            ticket_category = st.selectbox(
                "Issue Category",
                ["Account Related", "Card Services", "Online Banking", "Loan Enquiry", "Complaint", "Other"]
            )
            
            priority = st.selectbox(
                "Priority",
                ["Low", "Medium", "High", "Urgent"]
            )
        
        with col2:
            subject = st.text_input("Subject", placeholder="Brief description of your issue")
            
            contact_method = st.selectbox(
                "Preferred Contact Method",
                ["Email", "Phone Call", "SMS", "WhatsApp"]
            )
        
        description = st.text_area(
            "Describe Your Issue",
            placeholder="Please provide detailed information about your issue...",
            height=150
        )
        
        upload_file = st.file_uploader("Attach Documents (Optional)", type=["pdf", "jpg", "png"])
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col2:
            if st.button("🎫 Submit Ticket", key="submit_ticket", use_container_width=True, type="primary"):
                if subject and description:
                    ticket_id = f"TKT{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    st.success(f"✅ Ticket submitted successfully!")
                    st.info(f"📋 Your Ticket ID: **{ticket_id}**")
                    st.info("📧 You will receive updates via email and SMS")
                else:
                    st.warning("⚠️ Please fill in subject and description")
        
        st.markdown("---")
        
        # FAQs
        st.markdown("### ❓ Frequently Asked Questions")
        
        faqs = [
            ("How do I reset my internet banking password?", 
             "You can reset your password by clicking 'Forgot Password' on the login page. Enter your User ID and registered mobile number to receive an OTP. Use the OTP to create a new password."),
            
            ("What should I do if my debit card is lost or stolen?", 
             "Immediately call our 24/7 helpline at 1800-XXX-XXXX to block your card. You can also use the 'Block Card' feature in our mobile app. A replacement card will be issued within 5-7 business days."),
            
            ("How can I update my mobile number?", 
             "Visit your nearest branch with valid ID proof and a written request. Alternatively, if you have internet banking, you can update your mobile number through the profile settings after OTP verification."),
            
            ("What are the charges for cheque book?", 
             "The first cheque book (25 leaves) is free. Additional cheque books cost ₹50 for 25 leaves. You can request a cheque book through internet banking, mobile app, or at any branch."),
            
            ("How long does NEFT transfer take?", 
             "NEFT transfers are processed in hourly batches from 8 AM to 7 PM on working days. Typically, the beneficiary receives the amount within 2-3 hours. NEFT is free of charge for retail customers.")
        ]
        
        for question, answer in faqs:
            with st.expander(f"❓ {question}"):
                st.markdown(f"**Answer:** {answer}")
        
        st.markdown("---")
        
        # Service Status
        st.markdown("### 🔔 Service Status")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.success("✅ **Internet Banking:** Operational")
            st.success("✅ **Mobile App:** Operational")
        
        with col2:
            st.success("✅ **UPI Services:** Operational")
            st.success("✅ **Card Services:** Operational")
        
        with col3:
            st.success("✅ **ATM Network:** Operational")
            st.success("✅ **Branch Services:** Operational")
        
        st.markdown("---")
        
        # Emergency Contacts
        st.markdown("### 🚨 Emergency Contacts")
        
        st.markdown("""
            <div style="background: white; padding: 1.5rem; border-radius: 12px; border: 2px solid #ef4444;">
                <h4 style="color: #000000; margin-bottom: 1rem;">Emergency Helpline Numbers</h4>
                <p style="color: #000000;">• <strong>Lost/Stolen Card:</strong> 1800-XXX-CARD (24/7)</p>
                <p style="color: #000000;">• <strong>Fraudulent Transaction:</strong> 1800-XXX-FRAUD (24/7)</p>
                <p style="color: #000000;">• <strong>Account Blocking:</strong> 1800-XXX-BLOCK (24/7)</p>
                <p style="color: #000000;">• <strong>General Support:</strong> 1800-XXX-HELP (24/7)</p>
                <p style="color: #000000;">• <strong>International Helpline:</strong> +91-XX-XXXX-XXXX</p>
            </div>
        """, unsafe_allow_html=True)
    
    else:
        st.markdown(f"""
            <div class="chat-hero">
                <h1>{st.session_state.current_page}</h1>
                <p>This section is under development</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.info(f"🚧 The {st.session_state.current_page} section is coming soon!")
        
        if st.button("← Back to FAQs", key="back_to_faqs"):
            st.session_state.current_page = "FAQs"
            st.rerun()

# Main app logic
if not st.session_state.authenticated:
    login_page()
else:
    main_app()