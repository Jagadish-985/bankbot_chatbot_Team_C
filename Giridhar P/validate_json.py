import json
import sys

try:
    with open(r'c:\Users\paliv\OneDrive\Desktop\Bank Bot\faqs.json', 'r', encoding='utf-8') as f:
        json.load(f)
    print("JSON is valid!")
except json.JSONDecodeError as e:
    print(f"Error: {e}")
    print(f"Line: {e.lineno}")
    print(f"Col: {e.colno}")
    print(f"Message: {e.msg}")
