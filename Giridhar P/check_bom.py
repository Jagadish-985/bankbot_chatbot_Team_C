with open(r'c:\Users\paliv\OneDrive\Desktop\Bank Bot\faqs.json', 'rb') as f:
    head = f.read(10)
    print(f"File head hex: {head.hex()}")
    print(f"File head raw: {head}")
