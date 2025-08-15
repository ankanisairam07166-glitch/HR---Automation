#!/usr/bin/env python3
"""
Test script to verify the interview link generation process
Checks if candidates who passed assessments (>=70%) get proper interview links
"""

import requests
import json
from datetime import datetime

# Configuration
BACKEND_URL = "http://127.0.0.1:5000"

def test_interview_process():
    """Test the interview link generation process"""
    print("🔍 Testing Interview Link Generation Process")
    print("=" * 50)
    
    # Step 1: Get all candidates
    print("\n1️⃣ Fetching candidates from database...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/candidates")
        if response.status_code != 200:
            print(f"❌ Failed to fetch candidates: {response.status_code}")
            return
        
        candidates = response.json()
        print(f"✅ Found {len(candidates)} candidates")
        
    except Exception as e:
        print(f"❌ Error fetching candidates: {e}")
        return
    
    # Step 2: Analyze candidates by assessment status
    print("\n2️⃣ Analyzing candidate assessment status...")
    
    completed_assessments = []
    passed_assessments = []
    interview_scheduled = []
    missing_interviews = []
    
    for candidate in candidates:
        if candidate.get('exam_completed'):
            completed_assessments.append(candidate)
            
            percentage = candidate.get('exam_percentage')
            if percentage and percentage >= 70:
                passed_assessments.append(candidate)
                
                if candidate.get('interview_scheduled'):
                    interview_scheduled.append(candidate)
                else:
                    missing_interviews.append(candidate)
    
    print(f"📊 Assessment Analysis:")
    print(f"   • Total candidates: {len(candidates)}")
    print(f"   • Completed assessments: {len(completed_assessments)}")
    print(f"   • Passed assessments (≥70%): {len(passed_assessments)}")
    print(f"   • Interview scheduled: {len(interview_scheduled)}")
    print(f"   • Missing interviews: {len(missing_interviews)}")
    
    # Step 3: Check specific candidates who should have interviews
    if missing_interviews:
        print(f"\n3️⃣ Checking candidates who passed but don't have interviews...")
        
        for candidate in missing_interviews[:3]:  # Check first 3
            print(f"\n🔍 Candidate: {candidate['name']} ({candidate['email']})")
            print(f"   • Score: {candidate.get('exam_percentage', 'N/A')}%")
            print(f"   • Job: {candidate.get('job_title', 'N/A')}")
            print(f"   • Assessment completed: {candidate.get('exam_completed', False)}")
            print(f"   • Interview scheduled: {candidate.get('interview_scheduled', False)}")
            
            # Test the verification endpoint
            try:
                verify_response = requests.get(f"{BACKEND_URL}/api/verify-interview-process/{candidate['id']}")
                if verify_response.status_code == 200:
                    verify_data = verify_response.json()
                    print(f"   • Should schedule interview: {verify_data.get('should_schedule_interview', False)}")
                    print(f"   • Process ready: {verify_data.get('process_ready', False)}")
                    
                    if verify_data.get('should_schedule_interview'):
                        print(f"   ⚠️  This candidate should have an interview scheduled!")
                else:
                    print(f"   ❌ Verification failed: {verify_response.status_code}")
            except Exception as e:
                print(f"   ❌ Verification error: {e}")
    
    # Step 4: Test interview scheduling for a candidate who passed
    if missing_interviews:
        print(f"\n4️⃣ Testing interview scheduling...")
        test_candidate = missing_interviews[0]
        
        print(f"🎯 Testing with candidate: {test_candidate['name']}")
        
        # Test scheduling an interview
        try:
            schedule_data = {
                "candidate_id": test_candidate['id'],
                "email": test_candidate['email'],
                "date": (datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)).isoformat(),
                "time_slot": "10:00 AM"
            }
            
            schedule_response = requests.post(
                f"{BACKEND_URL}/api/schedule-interview",
                json=schedule_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if schedule_response.status_code == 200:
                result = schedule_response.json()
                print(f"✅ Interview scheduled successfully!")
                print(f"   • Interview link: {result.get('interview_link', 'N/A')}")
                print(f"   • Email sent: {result.get('email_sent', False)}")
                
                # Test the interview link
                if result.get('interview_link'):
                    print(f"\n5️⃣ Testing interview link...")
                    try:
                        interview_response = requests.get(result['interview_link'])
                        if interview_response.status_code == 200:
                            print(f"✅ Interview link works! Status: {interview_response.status_code}")
                        else:
                            print(f"⚠️  Interview link returned status: {interview_response.status_code}")
                    except Exception as e:
                        print(f"❌ Interview link test failed: {e}")
                
            else:
                print(f"❌ Failed to schedule interview: {schedule_response.status_code}")
                print(f"   Response: {schedule_response.text}")
                
        except Exception as e:
            print(f"❌ Error scheduling interview: {e}")
    
    # Step 5: Summary and recommendations
    print(f"\n📋 Summary & Recommendations:")
    print("=" * 50)
    
    if len(missing_interviews) > 0:
        print(f"⚠️  Found {len(missing_interviews)} candidates who passed assessments but don't have interviews scheduled.")
        print("   This indicates the automated interview scheduling process may not be working correctly.")
        print("\n🔧 Recommended fixes:")
        print("   1. Check the assessment results scraping process")
        print("   2. Verify the interview automation system is running")
        print("   3. Ensure the 70% threshold is being applied correctly")
        print("   4. Check database for any failed interview scheduling attempts")
    else:
        print("✅ All candidates who passed assessments have interviews scheduled.")
    
    if len(interview_scheduled) > 0:
        print(f"\n✅ {len(interview_scheduled)} candidates have interviews scheduled correctly.")
        
        # Check if interview links are working
        working_links = 0
        for candidate in interview_scheduled[:3]:  # Test first 3
            if candidate.get('interview_link'):
                try:
                    response = requests.get(candidate['interview_link'])
                    if response.status_code == 200:
                        working_links += 1
                except:
                    pass
        
        print(f"   • Interview links tested: {min(3, len(interview_scheduled))}")
        print(f"   • Working links: {working_links}")

if __name__ == "__main__":
    test_interview_process() 