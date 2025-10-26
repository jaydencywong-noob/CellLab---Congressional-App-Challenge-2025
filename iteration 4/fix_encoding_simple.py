#!/usr/bin/env python3
"""
Fix encoding issues in config.py - simpler version
"""

# Read the file
with open('game/config.py', 'rb') as f:
    content = f.read()

# Convert to string and fix common issues
content = content.decode('utf-8', errors='replace')

# Replace the most common problematic sequences
content = content.replace('\u2019', "'")  # Right single quotation mark
content = content.replace('\u2014', "-")  # Em dash
content = content.replace('\u201c', '"')  # Left double quotation mark
content = content.replace('\u201d', '"')  # Right double quotation mark
content = content.replace('\u2013', '-')  # En dash

# Replace the garbled sequences
content = content.replace('â€™', "'")
content = content.replace('â€"', "-")
content = content.replace('â€œ', '"')
content = content.replace('â€\x9d', '"')

# Write back
with open('game/config.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed encoding issues in config.py")

# Test syntax
import ast
try:
    ast.parse(content)
    print("✅ Config syntax is now valid")
except SyntaxError as e:
    print(f"❌ Still have syntax error: {e}")
    print(f"  Line {e.lineno}")
    
    # Show problematic line
    lines = content.split('\n')
    if e.lineno <= len(lines):
        print(f"  Problematic line: {lines[e.lineno-1]}")
        print(f"  Character codes: {[ord(c) for c in lines[e.lineno-1][:50]]}")