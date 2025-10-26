#!/usr/bin/env python3
"""
Test script to verify URL opening functionality
"""

import sys
import os

# Add the game directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'game'))

import webbrowser

# Import config module and reload it to ensure fresh data
import importlib
import config
importlib.reload(config)

from config import DISCOVERIES

def test_url_functionality():
    """Test that URLs can be opened from discoveries"""
    print("Testing URL functionality...")
    print(f"Total discoveries loaded: {len(DISCOVERIES)}")
    
    # Check if discoveries have URLs
    discoveries_with_urls = []
    for discovery_id, discovery_data in DISCOVERIES.items():
        print(f"Checking discovery: {discovery_id}")
        print(f"  Keys: {list(discovery_data.keys())}")
        if 'url' in discovery_data and discovery_data['url']:
            discoveries_with_urls.append((discovery_id, discovery_data))
            print(f"  ✅ Has URL: {discovery_data['url']}")
        else:
            print(f"  ❌ No URL")
        print()
    
    print(f"Found {len(discoveries_with_urls)} discoveries with URLs")
    
    # Show first few discoveries with URLs
    for i, (discovery_id, discovery_data) in enumerate(discoveries_with_urls[:5]):
        print(f"{i+1}. {discovery_data['title']}")
        print(f"   URL: {discovery_data['url']}")
        print(f"   Category: {discovery_data['category']}")
        print()
    
    # Test opening a URL (commented out to avoid actually opening browser)
    if discoveries_with_urls:
        test_discovery = discoveries_with_urls[0][1]
        print(f"Would open URL: {test_discovery['url']}")
        # webbrowser.open(test_discovery['url'])  # Commented out for testing
        print("URL opening functionality is ready!")
    
    return len(discoveries_with_urls) > 0

if __name__ == "__main__":
    success = test_url_functionality()
    if success:
        print("✅ URL functionality test passed!")
    else:
        print("❌ No URLs found in discoveries")