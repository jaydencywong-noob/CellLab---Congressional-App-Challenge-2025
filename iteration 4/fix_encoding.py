#!/usr/bin/env python3
"""
Fix encoding issues in config.py
"""

# Read the file with different encoding strategies
content = None
for encoding in ['utf-8', 'latin-1', 'cp1252']:
    try:
        with open('game/config.py', 'r', encoding=encoding) as f:
            content = f.read()
        print(f"Successfully read with {encoding}")
        break
    except UnicodeDecodeError:
        continue

if content is None:
    print("Could not read file with any encoding")
    exit(1)

# Count problematic characters before
problem_chars = ['â€™', 'â€"', ''', '"', '"', '—', '–']
problems_found = sum(content.count(char) for char in problem_chars)
print(f"Found {problems_found} problematic characters")

# Replace problematic characters more comprehensively
replacements = {
    'â€™': "'",  # Smart quote to regular apostrophe
    'â€"': "-",  # Em dash to regular dash
    ''': "'",   # Left single quote
    ''': "'",   # Right single quote  
    '"': '"',   # Left double quote
    '"': '"',   # Right double quote
    '—': '-',   # Em dash
    '–': '-',   # En dash
}

for old, new in replacements.items():
    content = content.replace(old, new)

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
    print(f"  Line {e.lineno}: {e.text}")
    
    # Show context around the error
    lines = content.split('\n')
    start = max(0, e.lineno - 3)
    end = min(len(lines), e.lineno + 2)
    print("Context:")
    for i in range(start, end):
        marker = " -> " if i == e.lineno - 1 else "    "
        print(f"{marker}{i+1:3}: {lines[i]}")