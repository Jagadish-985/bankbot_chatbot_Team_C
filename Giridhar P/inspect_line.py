with open(r'c:\Users\paliv\OneDrive\Desktop\Bank Bot\faqs.json', 'rb') as f:
    lines = f.readlines()
    if len(lines) >= 16:
        line16 = lines[15]
        print(f"Line 16 raw: {line16}")
        print(f"Line 16 hex: {line16.hex()}")
    else:
        print(f"File only has {len(lines)} lines")
