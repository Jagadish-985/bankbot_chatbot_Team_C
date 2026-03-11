with open(r'c:\Users\paliv\OneDrive\Desktop\Bank Bot\faqs.json', 'rb') as f:
    lines = f.readlines()
    if len(lines) >= 15:
        line15 = lines[14]
        print(f"Line 15 raw: {line15}")
        print(f"Line 15 hex: {line15.hex()}")
    else:
        print(f"File only has {len(lines)} lines")
