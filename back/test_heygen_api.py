# test_heygen_api.py - Test current HeyGen API endpoints

import os
import requests
import json

def test_heygen_api_endpoints():
    """Test current HeyGen API endpoints for knowledge base creation"""
    
    api_key = os.getenv('HEYGEN_API_KEY')
    if not api_key:
        print("❌ HEYGEN_API_KEY not found")
        return
    
    print(f"🔑 Testing HeyGen API with key: {api_key[:10]}...")
    
    # Updated list of possible HeyGen endpoints
    endpoints_to_test = [
        # Streaming Avatar endpoints
        'https://api.heygen.com/v1/streaming_avatar/knowledge_base',
        'https://api.heygen.com/v1/streaming.knowledge_base', 
        'https://api.heygen.com/v1/streaming/knowledge_base',
        
        # General knowledge base endpoints
        'https://api.heygen.com/v1/knowledge_base',
        'https://api.heygen.com/v2/knowledge_base',
        
        # Avatar specific endpoints
        'https://api.heygen.com/v1/avatar/knowledge_base',
        'https://api.heygen.com/v2/avatar/knowledge_base',
        
        # Updated endpoints (2024)
        'https://api.heygen.com/v1/template/knowledge_base',
        'https://api.heygen.com/v1/knowledge-base',
        'https://api.heygen.com/v2/knowledge-base'
    ]
    
    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'TalentFlow-AI/1.0'
    }
    
    test_payload = {
        'name': f'Test_KB_{int(__import__("time").time())}',
        'description': 'Test knowledge base for API validation',
        'content': 'Test content: This is a simple test of the knowledge base creation API.',
        'opening_line': 'Hello, this is a test interview.'
    }
    
    working_endpoints = []
    
    for endpoint in endpoints_to_test:
        print(f"\n🎯 Testing: {endpoint}")
        
        try:
            # First try GET to see if endpoint exists
            response = requests.get(endpoint, headers=headers, timeout=10)
            print(f"  GET response: {response.status_code}")
            
            if response.status_code != 404:
                # If GET doesn't return 404, try POST
                response = requests.post(
                    endpoint,
                    headers=headers,
                    json=test_payload,
                    timeout=30
                )
                
                print(f"  POST response: {response.status_code}")
                
                if response.ok:
                    print(f"  ✅ SUCCESS! Working endpoint found")
                    try:
                        data = response.json()
                        print(f"  📦 Response data: {json.dumps(data, indent=2)}")
                        working_endpoints.append(endpoint)
                    except:
                        print(f"  📦 Response (not JSON): {response.text[:200]}")
                        working_endpoints.append(endpoint)
                    break  # Found working endpoint
                else:
                    print(f"  ❌ Error: {response.text[:100]}")
                    if response.status_code == 401:
                        print("  🔑 Authentication issue - check API key")
                    elif response.status_code == 403:
                        print("  🚫 Permission denied - check API key scope")
            else:
                print(f"  ❌ Endpoint not found (404)")
                
        except requests.exceptions.Timeout:
            print(f"  ⏰ Timeout")
        except requests.exceptions.ConnectionError:
            print(f"  🔌 Connection error")
        except Exception as e:
            print(f"  💥 Error: {str(e)}")
    
    print(f"\n🎯 RESULTS:")
    if working_endpoints:
        print(f"✅ Found {len(working_endpoints)} working endpoint(s):")
        for ep in working_endpoints:
            print(f"  - {ep}")
        
        # Test knowledge base creation with working endpoint
        print(f"\n🧪 Testing knowledge base creation...")
        test_kb_creation(working_endpoints[0], api_key)
    else:
        print(f"❌ No working endpoints found!")
        print(f"\n🔧 Possible solutions:")
        print(f"1. Check if your HeyGen API key has knowledge base permissions")
        print(f"2. Verify API key is not expired")
        print(f"3. Check HeyGen documentation for updated endpoints")
        print(f"4. Contact HeyGen support for current API endpoints")


def test_kb_creation(endpoint, api_key):
    """Test actual knowledge base creation"""
    
    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    kb_payload = {
        'name': f'Interview_Test_{int(__import__("time").time())}',
        'description': 'Test interview knowledge base',
        'content': '''
INTERVIEW CONFIGURATION:
- Candidate: Test Candidate
- Position: Test Position
- Company: Test Company

INTERVIEW QUESTIONS:
1. Tell me about yourself
2. What interests you about this position?
3. Describe a challenging project you've worked on
4. How do you approach problem-solving?
5. What questions do you have for me?

BEHAVIOR: Be professional, engaging, and thorough.
        ''',
        'opening_line': 'Hello! Welcome to your test interview. I\'m excited to learn about your experience.'
    }
    
    try:
        response = requests.post(
            endpoint,
            headers=headers,
            json=kb_payload,
            timeout=30
        )
        
        print(f"🏗️ Knowledge base creation response: {response.status_code}")
        
        if response.ok:
            data = response.json()
            print(f"✅ Knowledge base created successfully!")
            print(f"📦 Response: {json.dumps(data, indent=2)}")
            
            # Extract KB ID
            kb_id = extract_kb_id(data)
            if kb_id:
                print(f"🆔 Knowledge Base ID: {kb_id}")
                return kb_id
            else:
                print(f"⚠️ No KB ID found in response")
        else:
            print(f"❌ Knowledge base creation failed: {response.text}")
            
    except Exception as e:
        print(f"💥 KB creation error: {str(e)}")
    
    return None


def extract_kb_id(response_data):
    """Extract knowledge base ID from various response formats"""
    possible_paths = [
        response_data.get('data', {}).get('knowledge_base_id'),
        response_data.get('data', {}).get('knowledgeBaseId'),
        response_data.get('data', {}).get('id'),
        response_data.get('knowledge_base_id'),
        response_data.get('knowledgeBaseId'),
        response_data.get('id'),
        response_data.get('result', {}).get('knowledge_base_id'),
        response_data.get('result', {}).get('id')
    ]
    
    for path in possible_paths:
        if path and isinstance(path, str):
            return path
    
    return None


if __name__ == "__main__":
    test_heygen_api_endpoints()