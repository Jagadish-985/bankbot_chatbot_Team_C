with open(r'c:\Users\paliv\OneDrive\Desktop\Bank Bot\faqs.json', 'r', encoding='utf-8') as f:
    content = f.read()
    for i, char in enumerate(content):
        if ord(char) > 127:
            print(f"Non-ASCII char at index {i}: {char} (ord: {ord(char)})")
        # Check for zero width space or other control chars
        if ord(char) < 32 and char not in '\r\n\t':
            print(f"Control char at index {i}: ord {ord(char)}")
