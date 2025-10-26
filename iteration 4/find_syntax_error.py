#!/usr/bin/env python3
"""
Find exact syntax error in config.py
"""

import ast

with open('game/config.py', 'r') as f:
    content = f.read()

# Try to parse and get detailed error info
try:
    ast.parse(content)
    print("✅ No syntax errors found")
except SyntaxError as e:
    print(f"❌ Syntax error at line {e.lineno}, col {e.offset}")
    print(f"  Text: {e.text}")
    print(f"  Error: {e.msg}")
    
    # Show context
    lines = content.split('\n')
    start = max(0, e.lineno - 5)
    end = min(len(lines), e.lineno + 5)
    print("\nContext:")
    for i in range(start, end):
        marker = " -> " if i == e.lineno - 1 else "    "
        line_content = lines[i] if i < len(lines) else "<EOF>"
        print(f"{marker}{i+1:4}: {line_content}")
        
        # Show character details for the error line
        if i == e.lineno - 1:
            print(f"      Chars: {[ord(c) for c in line_content[:min(50, len(line_content))]]}")
            if e.offset:
                print(f"      Error at position {e.offset}: '{line_content[e.offset-1:e.offset+5]}'")