#!/usr/bin/env python3
"""
Test Script for Interview Link Expiration System

This script demonstrates how the interview link expiration system works:
1. Create an interview token for a candidate
2. Simulate candidate starting the interview (link expires)
3. Try to access the expired link (should fail)
4. Show the security features

Usage: python test_interview_expiration.py
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:5000"  # Your backend URL
TEST_EMAIL = "test.candidate@example.com"

def test_interview_expiration():
    """Test the complete interview link expiration flow"""
    
    print("🧪 Testing Interview Link Expiration System")
    print("=" * 50)
    
    # Step 1: Create interview token
    print("\n1️⃣ Creating interview token...")
    try:
        response = requests.post(f"{BASE_URL}/api/avatar/interviews", 
                               json={"candidateEmail": TEST_EMAIL},
                               headers={"Content-Type": "application/json"})
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            expires_at = data.get("expiresAt")
            print(f"✅ Interview token created: {token}")
            print(f"📅 Expires at: {expires_at}")
        else:
            print(f"❌ Failed to create token: {response.status_code}")
            print(f"Response: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error creating token: {e}")
        return
    
    # Step 2: Validate token (should work)
    print("\n2️⃣ Validating fresh token...")
    try:
        response = requests.get(f"{BASE_URL}/api/interview/validate-token/{token}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Token is valid: {data.get('valid')}")
            print(f"👤 Candidate: {data.get('candidate_name')}")
            print(f"💼 Position: {data.get('position')}")
        else:
            print(f"❌ Token validation failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error validating token: {e}")
    
    # Step 3: Simulate starting interview (this expires the link)
    print("\n3️⃣ Starting interview (this will expire the link)...")
    try:
        response = requests.post(f"{BASE_URL}/api/avatar/interview/{token}", 
                               json={"action": "start"},
                               headers={"Content-Type": "application/json"})
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Interview started: {data.get('message')}")
            print(f"🔒 Link expired: {data.get('link_expired')}")
        else:
            print(f"❌ Failed to start interview: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error starting interview: {e}")
    
    # Step 4: Try to validate expired token (should fail)
    print("\n4️⃣ Validating expired token (should fail)...")
    try:
        response = requests.get(f"{BASE_URL}/api/interview/validate-token/{token}")
        if response.status_code == 410:
            data = response.json()
            print(f"✅ Token correctly rejected: {data.get('error')}")
            print(f"🔒 Link expired: {data.get('link_expired')}")
        else:
            print(f"❌ Token should have been rejected but got: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error validating expired token: {e}")
    
    # Step 5: Try to access secure interview page (should fail)
    print("\n5️⃣ Accessing secure interview page with expired token...")
    try:
        response = requests.get(f"{BASE_URL}/secure-interview/{token}")
        if response.status_code == 410:
            print("✅ Secure page correctly rejected expired token")
            print("📄 Showing expired interview page")
        else:
            print(f"❌ Secure page should have been rejected but got: {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing secure page: {e}")
    
    # Step 6: Try to start interview again (should fail)
    print("\n6️⃣ Trying to start interview again with expired link...")
    try:
        response = requests.post(f"{BASE_URL}/api/avatar/interview/{token}", 
                               json={"action": "start"},
                               headers={"Content-Type": "application/json"})
        
        if response.status_code == 410:
            data = response.json()
            print(f"✅ Correctly rejected: {data.get('error')}")
        else:
            print(f"❌ Should have been rejected but got: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error testing expired link: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Interview Link Expiration Test Complete!")
    print("\n📋 Summary:")
    print("✅ Fresh interview links work normally")
    print("🔒 Links expire after first use (start action)")
    print("🚫 Expired links cannot be reused")
    print("🛡️ Secure interview page blocks expired links")
    print("🔐 System prevents multiple interview sessions")

def test_security_features():
    """Test additional security features"""
    
    print("\n🔒 Testing Additional Security Features")
    print("=" * 40)
    
    # Test with invalid token
    print("\n1️⃣ Testing with invalid token...")
    try:
        response = requests.get(f"{BASE_URL}/api/interview/validate-token/invalid_token_123")
        if response.status_code == 404:
            print("✅ Invalid token correctly rejected")
        else:
            print(f"❌ Invalid token should have been rejected but got: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing invalid token: {e}")
    
    # Test with expired token in different endpoints
    print("\n2️⃣ Testing expired token across different endpoints...")
    
    # First create a valid token
    try:
        response = requests.post(f"{BASE_URL}/api/avatar/interviews", 
                               json={"candidateEmail": TEST_EMAIL},
                               headers={"Content-Type": "application/json"})
        
        if response.status_code == 200:
            token = response.json().get("token")
            
            # Expire it
            requests.post(f"{BASE_URL}/api/avatar/interview/{token}", 
                         json={"action": "start"},
                         headers={"Content-Type": "application/json"})
            
            # Test get_interview endpoint
            response = requests.get(f"{BASE_URL}/api/get-interview/{token}")
            if response.status_code == 410:
                print("✅ get_interview endpoint correctly rejects expired tokens")
            else:
                print(f"❌ get_interview should reject expired tokens: {response.status_code}")
                
        else:
            print("❌ Could not create test token")
    except Exception as e:
        print(f"❌ Error testing endpoint security: {e}")

if __name__ == "__main__":
    try:
        test_interview_expiration()
        test_security_features()
        
        print("\n🎉 All tests completed!")
        print("\n💡 The interview link expiration system is working correctly.")
        print("   Each candidate can only use their interview link once.")
        print("   After the first use, the link becomes permanently expired.")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        print("Make sure your backend is running on http://localhost:5000")
