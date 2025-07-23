#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.auth_service import AuthService
import logging

logging.basicConfig(level=logging.INFO)

# Use the authorization code from the browser callback
auth_code = "M.C521_SN1.2.U.ea467d8d-a713-181d-f2c2-14f96e3598c5"

auth = AuthService()

print("Testing Microsoft authentication with provided code...")

try:
    # Exchange code for Microsoft token
    ms_token = auth._get_microsoft_token(auth_code)
    print(f"✓ Microsoft token obtained successfully")
    
    # Complete the full authentication chain
    result = auth._complete_minecraft_auth(ms_token)
    
    if result:
        print("✓ Full authentication successful!")
        
        # Show the profile info
        profile = auth.get_profile()
        if profile:
            print(f"✓ Authenticated as: {profile.get('name', 'Unknown')}")
            print(f"✓ UUID: {profile.get('id', 'Unknown')}")
        
        # Test if we can get auth info for game launch
        auth_info = auth.get_auth_info()
        if auth_info:
            print(f"✓ Ready for game launch!")
            print(f"  Username: {auth_info['username']}")
            print(f"  Access Token: {auth_info['access_token'][:20]}...")
        
    else:
        print("✗ Authentication failed during Minecraft token exchange")
        
except Exception as e:
    print(f"✗ Authentication failed: {e}")
    import traceback
    traceback.print_exc()
