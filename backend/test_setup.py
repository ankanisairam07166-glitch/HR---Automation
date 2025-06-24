# test_setup.py - Run this to test your setup

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_backend():
    print("🧪 Testing TalentFlow AI Backend...")
    print("-" * 50)
    
    # Test 1: Health check
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check: OK")
            print(f"   Response: {response.json()}")
        else:
            print("❌ Health check failed")
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        print("   Make sure backend is running on port 5000")
        return False
    
    # Test 2: Get jobs
    try:
        response = requests.get(f"{BASE_URL}/api/jobs")
        if response.status_code == 200:
            jobs = response.json()
            print(f"✅ Jobs endpoint: OK - Found {len(jobs)} jobs")
            for job in jobs[:3]:  # Show first 3 jobs
                print(f"   - {job['title']} (ID: {job['id']})")
        else:
            print("❌ Jobs endpoint failed")
    except Exception as e:
        print(f"❌ Error getting jobs: {e}")
    
    # Test 3: Get candidates
    try:
        response = requests.get(f"{BASE_URL}/api/candidates")
        if response.status_code == 200:
            candidates = response.json()
            print(f"✅ Candidates endpoint: OK - Found {len(candidates)} candidates")
        else:
            print("❌ Candidates endpoint failed")
    except Exception as e:
        print(f"❌ Error getting candidates: {e}")
    
    # Test 4: Test pipeline
    try:
        print("\n🚀 Testing pipeline creation...")
        pipeline_data = {
            "job_id": "1001",
            "job_title": "Test Software Engineer",
            "job_desc": "This is a test job description"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/run_full_pipeline",
            json=pipeline_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Pipeline started successfully!")
            print(f"   Response: {response.json()}")
            
            print("\n⏳ Waiting 5 seconds for pipeline to process...")
            time.sleep(5)
            
            # Check if candidates were created
            response = requests.get(f"{BASE_URL}/api/candidates?job_id=1001")
            candidates = response.json()
            print(f"✅ Found {len(candidates)} candidates for job 1001")
            
        else:
            print(f"❌ Pipeline failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing pipeline: {e}")
    
    print("\n" + "-" * 50)
    print("🎉 Testing complete!")
    return True

if __name__ == "__main__":
    test_backend()