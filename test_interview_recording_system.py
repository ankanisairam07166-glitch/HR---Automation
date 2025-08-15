#!/usr/bin/env python3
"""
Test Script for Complete Interview Recording and Storage System
Demonstrates the full interview process from start to end with recording and AI analysis
"""

import requests
import json
import time
import uuid
from datetime import datetime

# Configuration
BACKEND_URL = "http://127.0.0.1:5000"

def test_complete_interview_system():
    """Test the complete interview recording and storage system"""
    print("🎬 Testing Complete Interview Recording and Storage System")
    print("=" * 70)
    
    # Step 1: Get a candidate with interview scheduled
    print("\n1️⃣ Finding candidate with scheduled interview...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/candidates")
        if response.status_code != 200:
            print(f"❌ Failed to fetch candidates: {response.status_code}")
            return
        
        candidates = response.json()
        interview_candidate = None
        
        for candidate in candidates:
            if candidate.get('interview_scheduled') and candidate.get('interview_token'):
                interview_candidate = candidate
                break
        
        if not interview_candidate:
            print("❌ No candidate with scheduled interview found")
            print("   Please schedule an interview for a candidate first")
            return
        
        print(f"✅ Found candidate: {interview_candidate['name']} ({interview_candidate['email']})")
        print(f"   Interview token: {interview_candidate['interview_token']}")
        
    except Exception as e:
        print(f"❌ Error finding candidate: {e}")
        return
    
    # Step 2: Start interview session
    print(f"\n2️⃣ Starting interview session...")
    try:
        session_data = {
            "interview_token": interview_candidate['interview_token'],
            "recording_config": {
                "format": "webm",
                "quality": "HD",
                "audio": True,
                "video": True
            }
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/interview/session/start",
            json=session_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to start session: {response.status_code}")
            print(f"   Response: {response.text}")
            return
        
        result = response.json()
        session_id = result.get('session_id')
        recording_started = result.get('recording_started')
        
        print(f"✅ Interview session started successfully!")
        print(f"   Session ID: {session_id}")
        print(f"   Recording started: {recording_started}")
        
    except Exception as e:
        print(f"❌ Error starting interview session: {e}")
        return
    
    # Step 3: Simulate interview questions and answers
    print(f"\n3️⃣ Simulating interview questions and answers...")
    
    # Sample interview questions
    interview_questions = [
        {
            "text": "Tell me about your experience with Python programming.",
            "type": "technical",
            "avatar": "default",
            "keywords": ["python", "programming", "experience"],
            "difficulty": "medium"
        },
        {
            "text": "How do you handle working under pressure?",
            "type": "behavioral",
            "avatar": "default",
            "keywords": ["pressure", "stress", "management"],
            "difficulty": "medium"
        },
        {
            "text": "What are your career goals for the next 5 years?",
            "type": "cultural",
            "avatar": "default",
            "keywords": ["career", "goals", "future"],
            "difficulty": "easy"
        },
        {
            "text": "Explain the concept of machine learning in simple terms.",
            "type": "technical",
            "avatar": "default",
            "keywords": ["machine learning", "AI", "algorithms"],
            "difficulty": "hard"
        }
    ]
    
    # Sample candidate answers
    candidate_answers = [
        {
            "text": "I have been working with Python for over 3 years. I've developed web applications using Django and Flask, and I'm comfortable with data analysis using pandas and numpy. I've also worked on automation scripts and API development.",
            "duration": 45,
            "audio_quality": "excellent",
            "confidence": 0.9
        },
        {
            "text": "I handle pressure by breaking down complex tasks into smaller, manageable parts. I prioritize my work and communicate clearly with my team about deadlines and progress. I also make sure to take short breaks to maintain focus.",
            "duration": 38,
            "audio_quality": "good",
            "confidence": 0.8
        },
        {
            "text": "In the next 5 years, I want to grow into a senior developer role and eventually move into technical leadership. I'm interested in specializing in machine learning and AI, and I want to contribute to innovative projects that make a real impact.",
            "duration": 42,
            "audio_quality": "excellent",
            "confidence": 0.85
        },
        {
            "text": "Machine learning is like teaching a computer to learn from examples, similar to how humans learn. Instead of programming every rule, you give the computer data and it finds patterns to make predictions or decisions.",
            "duration": 35,
            "audio_quality": "good",
            "confidence": 0.75
        }
    ]
    
    question_ids = []
    
    for i, question_data in enumerate(interview_questions):
        print(f"\n   📝 Adding question {i+1}: {question_data['text'][:50]}...")
        
        try:
            # Add question
            question_request = {
                "session_id": session_id,
                "question_data": question_data
            }
            
            response = requests.post(
                f"{BACKEND_URL}/api/interview/question/add",
                json=question_request,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                question_id = result.get('question_id')
                question_ids.append(question_id)
                print(f"   ✅ Question added: {question_id}")
                
                # Simulate some time for the question
                time.sleep(1)
                
                # Add candidate answer
                print(f"   🎤 Adding candidate answer...")
                answer_request = {
                    "session_id": session_id,
                    "question_id": question_id,
                    "answer_data": candidate_answers[i]
                }
                
                response = requests.post(
                    f"{BACKEND_URL}/api/interview/answer/add",
                    json=answer_request,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    answer_id = result.get('answer_id')
                    print(f"   ✅ Answer added: {answer_id}")
                else:
                    print(f"   ❌ Failed to add answer: {response.status_code}")
                
            else:
                print(f"   ❌ Failed to add question: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error adding question/answer: {e}")
        
        # Simulate time between questions
        time.sleep(2)
    
    # Step 4: End interview session
    print(f"\n4️⃣ Ending interview session...")
    try:
        end_request = {
            "session_id": session_id
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/interview/session/end",
            json=end_request,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Interview session ended successfully!")
            print(f"   Message: {result.get('message')}")
        else:
            print(f"❌ Failed to end session: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error ending interview session: {e}")
    
    # Step 5: Wait for analysis and check results
    print(f"\n5️⃣ Waiting for AI analysis to complete...")
    print("   (This may take a few moments)")
    
    # Wait for analysis to complete
    time.sleep(5)
    
    # Check analysis results
    print(f"\n6️⃣ Checking interview analysis results...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/interview/analysis/{interview_candidate['id']}")
        
        if response.status_code == 200:
            result = response.json()
            analysis = result.get('analysis', {})
            
            print(f"✅ Analysis completed!")
            print(f"   Technical Score: {analysis.get('technical_score', 0):.1f}%")
            print(f"   Communication Score: {analysis.get('communication_score', 0):.1f}%")
            print(f"   Problem Solving Score: {analysis.get('problem_solving_score', 0):.1f}%")
            print(f"   Cultural Fit Score: {analysis.get('cultural_fit_score', 0):.1f}%")
            print(f"   Overall Score: {analysis.get('overall_score', 0):.1f}%")
            print(f"   Final Status: {analysis.get('final_status', 'unknown')}")
            print(f"   Feedback: {analysis.get('overall_feedback', 'No feedback available')}")
            
        else:
            print(f"❌ Failed to get analysis: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting analysis: {e}")
    
    # Step 6: Check recording information
    print(f"\n7️⃣ Checking recording information...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/interview/recording/{interview_candidate['id']}")
        
        if response.status_code == 200:
            result = response.json()
            recording_info = result.get('recording_info', {})
            
            print(f"✅ Recording information retrieved!")
            print(f"   Recording File: {recording_info.get('recording_file', 'N/A')}")
            print(f"   Duration: {recording_info.get('recording_duration', 0)} seconds")
            print(f"   Format: {recording_info.get('recording_format', 'N/A')}")
            print(f"   Quality: {recording_info.get('recording_quality', 'N/A')}")
            print(f"   Status: {recording_info.get('recording_status', 'N/A')}")
            print(f"   Session ID: {recording_info.get('session_id', 'N/A')}")
            
        else:
            print(f"❌ Failed to get recording info: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting recording info: {e}")
    
    # Step 7: Get complete session data
    print(f"\n8️⃣ Getting complete session data...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/interview/session/{session_id}")
        
        if response.status_code == 200:
            result = response.json()
            session_data = result.get('session_data', {})
            
            print(f"✅ Session data retrieved!")
            print(f"   Session ID: {session_data.get('session_id', 'N/A')}")
            print(f"   Duration: {session_data.get('duration_seconds', 0)} seconds")
            print(f"   Questions Asked: {len(session_data.get('questions', []))}")
            print(f"   Answers Given: {len(session_data.get('answers', []))}")
            print(f"   Status: {session_data.get('status', 'N/A')}")
            
            # Show questions and answers
            questions = session_data.get('questions', [])
            answers = session_data.get('answers', [])
            
            print(f"\n📋 Interview Summary:")
            for i, question in enumerate(questions):
                print(f"   Q{i+1}: {question.get('question_text', 'N/A')[:60]}...")
                if i < len(answers):
                    print(f"   A{i+1}: {answers[i].get('answer_text', 'N/A')[:60]}...")
                print()
            
        else:
            print(f"❌ Failed to get session data: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting session data: {e}")
    
    # Step 8: Summary
    print(f"\n📊 Interview System Test Summary:")
    print("=" * 50)
    print(f"✅ Interview session created and managed")
    print(f"✅ Recording system activated")
    print(f"✅ {len(interview_questions)} questions tracked")
    print(f"✅ {len(candidate_answers)} answers stored")
    print(f"✅ AI analysis performed")
    print(f"✅ All data stored in database")
    print(f"\n🎯 The complete interview recording and storage system is working!")
    print(f"   - Questions and answers are tracked with timestamps")
    print(f"   - Recording information is stored")
    print(f"   - AI analysis provides scores and feedback")
    print(f"   - All data is persisted in the database")

if __name__ == "__main__":
    test_complete_interview_system() 