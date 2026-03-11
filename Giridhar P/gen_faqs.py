import json
import random

faqs = [
    {"question": "💰Check Account Balance", "answer": "You can view your current account balance securely from your Dashboard widget. Your balance is updated in real-time."},
    {"question": "💵View Recent Transactions", "answer": "Navigate to the 'Transactions' tab to see a full chronological history of your credits and debits."},
    {"question": "🏠Loan Information", "answer": "We currently offer Personal, Home, Car, Education, and Business loans. You can track your active loans in the Loan Tracking tab."},
    {"question": "🏠Apply for New Loan", "answer": "Go to the 'Loan Tracking' tab and use the Application Form at the bottom. Provide the type, amount, and tenure to begin."},
    {"question": "💵%Interest Rates", "answer": "Our interest rates vary by loan type, starting as low as 8.5% p.a. for home loans. Use the loan calculator to see specific rates."},
    {"question": "💸Transfer Money", "answer": "The immediate money transfer feature via NEFT/IMPS/RTGS is currently under development and will be available shortly."},
    {"question": "How do I check my account balance?", "answer": "You can view your current balance in the 'Dashboard' tab or in the sidebar under 'Account Details'. It is updated in real-time."},
    {"question": "Where can I see my recent transactions?", "answer": "Go to the 'Transactions' tab to see your full history, or check the 'Recent Transactions' section on your Dashboard."},
    {"question": "What is my account number?", "answer": "Your 10-digit account number is displayed in the sidebar under 'Account Details' for quick reference."},
    {"question": "How do I logout?", "answer": "Click the 'Logout' button at the bottom of the sidebar. Your chat history will be automatically saved before you exit."},
    {"question": "Can I change my preferred language?", "answer": "Yes, you can choose from various Indian languages like Hindi, Bengali, Telugu, and more during the initial login process."},
    {"question": "How do I view my previous chats?", "answer": "In the 'Chat Assistant' tab, look for the 'Previous Chats' section on the right side to load or delete your past conversations."}
]

topics = ['savings account', 'current account', 'credit card', 'debit card', 'fixed deposit', 'recurring deposit', 'mutual funds', 'life insurance', 'health insurance', 'car loan', 'home loan', 'personal loan', 'education loan', 'gold loan', 'mobile banking', 'internet banking', 'ATM', 'branch', 'cheque book', 'demand draft', 'NEFT', 'RTGS', 'IMPS', 'UPI']
actions = ['How do I apply for a', 'What are the benefits of a', 'How do I close my', 'What are the fees for a', 'How do I track my', 'Can I upgrade my', 'What is the limit on a', 'How to report a lost', 'Are there any hidden charges for a', 'How do I update my details for a']
answers = [
    'You can manage this easily by visiting the respective section in your account dashboard online.',
    'For details regarding this, please visit your nearest bank branch or check our official schedule of charges.',
    'This feature is directly integrated into our mobile application under the Services tab.',
    'Applications and tracking can be done exclusively through the New Requests panel in your account.',
    'There are no hidden charges. All fees are transparently listed in your account agreement.',
    'You can initiate this process by contacting our 24/7 designated customer service hotline.',
    'Please ensure your KYC is fully updated before attempting this request.',
    'This service is typically processed within 2-3 business days upon submission of the request.',
    'The limits and benefits vary depending on your specific account tier. Check your profile settings for your applicable tier.',
    'To proceed with this, you may require a verified email address and active mobile number for OTP confirmation.'
]

for topic in topics:
    for action in actions:
        if len(faqs) > 120:
            break
        q = f"{action} {topic}?"
        a = answers[random.randint(0, len(answers)-1)]
        faqs.append({"question": q, "answer": f"Regarding your query about the {topic}: {a}"})

with open('faqs.json', 'w', encoding='utf-8') as f:
    json.dump(faqs, f, indent=4)
