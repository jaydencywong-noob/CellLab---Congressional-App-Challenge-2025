#!/usr/bin/env python3
"""
Debug script to check what's in the config file
"""

# Direct file reading approach
print("=== Direct file reading ===")
with open('game/config.py', 'r') as f:
    content = f.read()
    
# Look for the first_split entry
start_idx = content.find('"first_split"')
if start_idx != -1:
    # Find the end of this entry (next entry or closing brace)
    end_idx = content.find('",\n    "', start_idx)
    if end_idx == -1:
        end_idx = content.find('\n}', start_idx)
    
    if end_idx != -1:
        entry_content = content[start_idx:end_idx]
        print("Found first_split entry:")
        print(entry_content[:500] + "..." if len(entry_content) > 500 else entry_content)
        print()
        
        if 'url' in entry_content:
            print("✅ URL found in file content")
        else:
            print("❌ No URL found in file content")
    else:
        print("Could not find end of first_split entry")
else:
    print("Could not find first_split entry")

print("\n=== URL check ===")
url_count = content.count('"url":')
print(f"Found {url_count} URL entries in file")

# Try to locate where the DISCOVERIES dict starts and ends
discoveries_start = content.find('DISCOVERIES = {')
if discoveries_start != -1:
    print(f"DISCOVERIES starts at position {discoveries_start}")
    
    # Count braces to find the end
    brace_count = 0
    in_string = False
    escape_next = False
    
    for i, char in enumerate(content[discoveries_start:]):
        if escape_next:
            escape_next = False
            continue
            
        if char == '\\':
            escape_next = True
            continue
            
        if char == '"' and not escape_next:
            in_string = not in_string
            continue
            
        if not in_string:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    discoveries_end = discoveries_start + i + 1
                    break
    
    discoveries_content = content[discoveries_start:discoveries_end]
    url_count_in_discoveries = discoveries_content.count('"url":')
    print(f"Found {url_count_in_discoveries} URL entries in DISCOVERIES dict")
    
    if url_count_in_discoveries > 0:
        print("✅ URLs are present in DISCOVERIES dictionary")
    else:
        print("❌ No URLs found in DISCOVERIES dictionary")
        
    # Show first 1000 chars of DISCOVERIES
    print("\nFirst part of DISCOVERIES:")
    print(discoveries_content[:1000] + "..." if len(discoveries_content) > 1000 else discoveries_content)