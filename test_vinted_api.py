#!/usr/bin/env python
"""Test script for Vinted API token acquisition"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vinted_koopjes.settings')
django.setup()

from watches.services import vinted_api

def test_token_acquisition():
    """Test if we can acquire a Vinted access token"""
    print("🧪 Testing Vinted API token acquisition...")
    
    try:
        # Force refresh to test the acquisition process
        token = vinted_api.get_access_token(force_refresh=True)
        print(f"✅ Successfully acquired token: {token[:20]}...")
        return True
    except Exception as e:
        print(f"❌ Failed to acquire token: {e}")
        return False

def test_api_request():
    """Test a simple API request"""
    print("🧪 Testing Vinted API request...")
    
    try:
        # Try a simple search
        items = vinted_api.search_items({'search_text': 'test', 'per_page': 1})
        print(f"✅ Successfully made API request, got {len(items)} items")
        return True
    except Exception as e:
        print(f"❌ Failed to make API request: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Vinted API tests...\n")
    
    token_success = test_token_acquisition()
    print()
    
    if token_success:
        api_success = test_api_request()
        print()
        
        if api_success:
            print("🎉 All tests passed! Vinted API is working correctly.")
            sys.exit(0)
        else:
            print("⚠️ Token acquisition works but API requests fail.")
            sys.exit(1)
    else:
        print("💥 Token acquisition failed. Check network and browser setup.")
        sys.exit(1)