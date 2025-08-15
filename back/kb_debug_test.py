# kb_debug_test.py - Comprehensive debugging script for HeyGen KB issues

import os
import json
import requests
import time
from datetime import datetime
from db import SessionLocal, Candidate
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KnowledgeBaseDebugger:
    def __init__(self):
        self.heygen_api_key = os.getenv('HEYGEN_API_KEY')
        self.session = SessionLocal()
        self.test_results = {}
    
    def run_complete_diagnosis(self, candidate_id=None):
        """Run complete diagnosis of KB creation system"""
        
        print("🔍 HEYGEN KNOWLEDGE BASE DIAGNOSTIC TOOL")
        print("=" * 60)
        
        # Test 1: Environment Configuration
        self.test_environment_setup()
        
        # Test 2: Database Schema
        self.test_database_schema()
        
        # Test 3: HeyGen API Connection
        self.test_heygen_api_connection()
        
        # Test 4: Resume Extraction
        if candidate_id:
            self.test_resume_extraction(candidate_id)
            
            # Test 5: End-to-End KB Creation
            self.test_end_to_end_kb_creation(candidate_id)
        
        # Test 6: Frontend Integration
        self.test_frontend_integration()
        
        # Generate Report
        self.generate_diagnostic_report()
        
        return self.test_results
    
    def test_environment_setup(self):
        """Test environment configuration"""
        print("\n📋 TEST 1: Environment Configuration")
        print("-" * 40)
        
        env_tests = {
            "HEYGEN_API_KEY": {
                "exists": bool(self.heygen_api_key),
                "length": len(self.heygen_api_key) if self.heygen_api_key else 0,
                "format_valid": self.heygen_api_key and len(self.heygen_api_key) > 20 if self.heygen_api_key else False
            },
            "DATABASE_URL": {
                "exists": bool(os.getenv('DATABASE_URL')),
                "value": os.getenv('DATABASE_URL', 'Using default SQLite')[:50] + "..."
            },
            "COMPANY_NAME": {
                "exists": bool(os.getenv('COMPANY_NAME')),
                "value": os.getenv('COMPANY_NAME', 'Not set')
            }
        }
        
        for env_var, tests in env_tests.items():
            status = "✅" if tests.get("exists", False) else "❌"
            print(f"{status} {env_var}: {tests}")
        
        self.test_results["environment"] = env_tests
        
        # Critical issues
        if not env_tests["HEYGEN_API_KEY"]["exists"]:
            print("🚨 CRITICAL: HEYGEN_API_KEY not found!")
            print("   Fix: Add HEYGEN_API_KEY to your .env file")
        elif not env_tests["HEYGEN_API_KEY"]["format_valid"]:
            print("⚠️ WARNING: HEYGEN_API_KEY seems too short or invalid")
    
    def test_database_schema(self):
        """Test database schema for required fields"""
        print("\n📋 TEST 2: Database Schema")
        print("-" * 40)
        
        required_fields = [
            'knowledge_base_id',
            'interview_token', 
            'interview_session_id',
            'company_name',
            'job_description',
            'resume_path'
        ]
        
        try:
            # Get first candidate to test field access
            candidate = self.session.query(Candidate).first()
            
            schema_status = {}
            for field in required_fields:
                try:
                    value = getattr(candidate, field, None)
                    schema_status[field] = {
                        "exists": True,
                        "has_data": value is not None,
                        "sample_value": str(value)[:50] + "..." if value else "NULL"
                    }
                    print(f"✅ {field}: EXISTS (value: {schema_status[field]['sample_value']})")
                except AttributeError:
                    schema_status[field] = {"exists": False}
                    print(f"❌ {field}: MISSING")
            
            self.test_results["database_schema"] = schema_status
            
            # Check candidate count
            total_candidates = self.session.query(Candidate).count()
            print(f"📊 Total candidates in database: {total_candidates}")
            
        except Exception as e:
            print(f"❌ Database schema test failed: {e}")
            self.test_results["database_schema"] = {"error": str(e)}
    
    def test_heygen_api_connection(self):
        """Test HeyGen API connection and endpoints"""
        print("\n📋 TEST 3: HeyGen API Connection")
        print("-" * 40)
        
        if not self.heygen_api_key:
            print("❌ Cannot test API - no API key found")
            self.test_results["heygen_api"] = {"error": "No API key"}
            return
        
        # Test different endpoints
        endpoints = [
            'https://api.heygen.com/v1/streaming_avatar.knowledge_base',
            'https://api.heygen.com/v1/streaming/knowledge_base', 
            'https://api.heygen.com/v1/knowledge_base'
        ]
        
        api_results = {}
        
        for endpoint in endpoints:
            print(f"\n🎯 Testing endpoint: {endpoint}")
            
            try:
                # Create minimal test knowledge base
                test_payload = {
                    'name': f'Test_KB_{int(time.time())}',
                    'description': 'Test knowledge base for API validation',
                    'content': 'Test content: This is a simple test of the knowledge base creation.',
                    'opening_line': 'Hello, this is a test.'
                }
                
                response = requests.post(
                    endpoint,
                    headers={
                        'X-Api-Key': self.heygen_api_key,
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    json=test_payload,
                    timeout=30
                )
                
                api_results[endpoint] = {
                    "status_code": response.status_code,
                    "success": response.ok,
                    "response_size": len(response.text),
                    "headers": dict(response.headers),
                    "response_preview": response.text[:200] + "..." if len(response.text) > 200 else response.text
                }
                
                if response.ok:
                    print(f"✅ SUCCESS: {response.status_code}")
                    try:
                        data = response.json()
                        kb_id = self.extract_kb_id(data)
                        if kb_id:
                            print(f"   📝 Knowledge Base ID: {kb_id}")
                            api_results[endpoint]["kb_id_created"] = kb_id
                        else:
                            print(f"   ⚠️ No KB ID found in response")
                    except json.JSONDecodeError:
                        print(f"   ⚠️ Response is not valid JSON")
                else:
                    print(f"❌ FAILED: {response.status_code}")
                    print(f"   Error: {response.text[:100]}...")
                    
            except requests.exceptions.Timeout:
                print(f"⏰ TIMEOUT")
                api_results[endpoint] = {"error": "timeout"}
            except requests.exceptions.ConnectionError:
                print(f"🔌 CONNECTION ERROR")
                api_results[endpoint] = {"error": "connection_error"}
            except Exception as e:
                print(f"💥 ERROR: {e}")
                api_results[endpoint] = {"error": str(e)}
        
        self.test_results["heygen_api"] = api_results
        
        # Find working endpoint
        working_endpoints = [ep for ep, result in api_results.items() if result.get("success")]
        if working_endpoints:
            print(f"\n✅ Working endpoints found: {len(working_endpoints)}")
            self.test_results["heygen_api"]["working_endpoint"] = working_endpoints[0]
        else:
            print(f"\n❌ No working endpoints found!")
    
    def test_resume_extraction(self, candidate_id):
        """Test resume extraction for a specific candidate"""
        print(f"\n📋 TEST 4: Resume Extraction (Candidate {candidate_id})")
        print("-" * 40)
        
        try:
            candidate = self.session.query(Candidate).filter_by(id=candidate_id).first()
            
            if not candidate:
                print(f"❌ Candidate {candidate_id} not found")
                self.test_results["resume_extraction"] = {"error": "candidate_not_found"}
                return
            
            print(f"👤 Candidate: {candidate.name}")
            print(f"📄 Resume path: {candidate.resume_path}")
            
            extraction_result = {
                "candidate_name": candidate.name,
                "resume_path": candidate.resume_path,
                "file_exists": False,
                "extraction_successful": False,
                "content_length": 0
            }
            
            if candidate.resume_path:
                extraction_result["file_exists"] = os.path.exists(candidate.resume_path)
                
                if extraction_result["file_exists"]:
                    print(f"✅ Resume file exists")
                    
                    # Test extraction
                    from backend import extract_resume_content
                    content = extract_resume_content(candidate.resume_path)
                    
                    extraction_result["extraction_successful"] = len(content) > 0
                    extraction_result["content_length"] = len(content)
                    extraction_result["content_preview"] = content[:300] + "..." if content else "No content"
                    
                    if extraction_result["extraction_successful"]:
                        print(f"✅ Resume extracted: {len(content)} characters")
                        print(f"📝 Preview: {content[:100]}...")
                        
                        # Test skill extraction
                        from backend import extract_skills_from_resume
                        skills = extract_skills_from_resume(content)
                        extraction_result["skills_found"] = skills
                        print(f"🔧 Skills found: {skills}")
                        
                    else:
                        print(f"❌ Resume extraction failed or empty")
                else:
                    print(f"❌ Resume file not found: {candidate.resume_path}")
            else:
                print(f"❌ No resume path in database")
            
            self.test_results["resume_extraction"] = extraction_result
            
        except Exception as e:
            print(f"💥 Resume extraction test failed: {e}")
            self.test_results["resume_extraction"] = {"error": str(e)}
    
    def test_end_to_end_kb_creation(self, candidate_id):
        """Test complete KB creation process"""
        print(f"\n📋 TEST 5: End-to-End KB Creation (Candidate {candidate_id})")
        print("-" * 40)
        
        try:
            candidate = self.session.query(Candidate).filter_by(id=candidate_id).first()
            
            if not candidate:
                print(f"❌ Candidate not found")
                return
            
            # Step 1: Prepare data
            print("🔄 Step 1: Preparing candidate data...")
            
            candidate_data = {
                "candidateName": candidate.name,
                "position": candidate.job_title,
                "company": getattr(candidate, 'company_name', 'Test Company'),
                "token": getattr(candidate, 'interview_token', None)
            }
            
            print(f"   Data prepared: {candidate_data}")
            
            # Step 2: Test KB creation API call
            print("🔄 Step 2: Testing KB creation API...")
            
            if not self.heygen_api_key:
                print("❌ Cannot test - no HeyGen API key")
                return
            
            # Use working endpoint from previous test
            working_endpoint = self.test_results.get("heygen_api", {}).get("working_endpoint")
            if not working_endpoint:
                working_endpoint = 'https://api.heygen.com/v1/streaming/knowledge_base'
            
            # Create KB content
            from backend import generate_interview_questions, extract_resume_content
            
            resume_content = ""
            if candidate.resume_path and os.path.exists(candidate.resume_path):
                resume_content = extract_resume_content(candidate.resume_path)
            
            kb_content = f"""
INTERVIEW CONFIGURATION FOR {candidate.name}
Position: {candidate.job_title}
Company: {candidate_data['company']}

CANDIDATE BACKGROUND:
{resume_content[:1000] + "..." if resume_content else "No resume content"}

INTERVIEW QUESTIONS:
1. Tell me about yourself and your journey to this role.
2. What interests you about this position?
3. Describe a challenging project you've worked on.
4. How do you approach problem-solving?
5. What questions do you have for me?

BEHAVIOR: Be professional, engaging, and thorough in your interview.
"""
            
            kb_payload = {
                'name': f'Test_Interview_{candidate.name}_{int(time.time())}',
                'description': f'Test interview for {candidate.name}',
                'content': kb_content,
                'opening_line': f'Hello {candidate.name}! Welcome to your interview.'
            }
            
            try:
                response = requests.post(
                    working_endpoint,
                    headers={
                        'X-Api-Key': self.heygen_api_key,
                        'Content-Type': 'application/json'
                    },
                    json=kb_payload,
                    timeout=30
                )
                
                if response.ok:
                    print("✅ KB creation successful!")
                    kb_data = response.json()
                    kb_id = self.extract_kb_id(kb_data)
                    
                    if kb_id:
                        print(f"📝 Knowledge Base ID: {kb_id}")
                        
                        # Step 3: Test database storage
                        print("🔄 Step 3: Testing database storage...")
                        candidate.knowledge_base_id = kb_id
                        candidate.interview_created_at = datetime.now()
                        self.session.commit()
                        print("✅ KB ID saved to database")
                        
                        self.test_results["end_to_end"] = {
                            "success": True,
                            "kb_id": kb_id,
                            "endpoint_used": working_endpoint
                        }
                    else:
                        print("❌ KB ID not found in response")
                        self.test_results["end_to_end"] = {"error": "no_kb_id_in_response"}
                else:
                    print(f"❌ KB creation failed: {response.status_code}")
                    print(f"   Error: {response.text}")
                    self.test_results["end_to_end"] = {
                        "error": f"api_error_{response.status_code}",
                        "details": response.text
                    }
                    
            except Exception as e:
                print(f"💥 KB creation failed: {e}")
                self.test_results["end_to_end"] = {"error": str(e)}
                
        except Exception as e:
            print(f"💥 End-to-end test failed: {e}")
            self.test_results["end_to_end"] = {"error": str(e)}
    
    def test_frontend_integration(self):
        """Test frontend integration points"""
        print(f"\n📋 TEST 6: Frontend Integration")
        print("-" * 40)
        
        integration_tests = {}
        
        # Test 1: Backend endpoints
        backend_endpoints = [
            'http://localhost:5000/api/create-knowledge-base',
            'http://localhost:5000/api/get-access-token',
            'http://localhost:5000/api/get-interview/test-token'
        ]
        
        for endpoint in backend_endpoints:
            try:
                # Test with a simple GET/POST
                if 'get-access-token' in endpoint:
                    response = requests.post(endpoint, timeout=5)
                else:
                    response = requests.get(endpoint, timeout=5)
                
                integration_tests[endpoint] = {
                    "reachable": True,
                    "status_code": response.status_code
                }
                
                status = "✅" if response.status_code < 500 else "❌"
                print(f"{status} {endpoint}: {response.status_code}")
                
            except requests.exceptions.ConnectionError:
                integration_tests[endpoint] = {"reachable": False, "error": "connection_refused"}
                print(f"❌ {endpoint}: Connection refused (backend not running?)")
            except Exception as e:
                integration_tests[endpoint] = {"reachable": False, "error": str(e)}
                print(f"❌ {endpoint}: {e}")
        
        # Test 2: Next.js endpoints (if running)
        nextjs_endpoints = [
            'http://localhost:3001/api/create-knowledge-base',
            'http://localhost:3001/api/get-access-token'
        ]
        
        for endpoint in nextjs_endpoints:
            try:
                response = requests.post(endpoint, json={"test": True}, timeout=5)
                integration_tests[endpoint] = {
                    "reachable": True,
                    "status_code": response.status_code
                }
                
                status = "✅" if response.status_code < 500 else "❌"
                print(f"{status} {endpoint}: {response.status_code}")
                
            except requests.exceptions.ConnectionError:
                integration_tests[endpoint] = {"reachable": False, "error": "connection_refused"}
                print(f"❌ {endpoint}: Connection refused (Next.js not running?)")
            except Exception as e:
                integration_tests[endpoint] = {"reachable": False, "error": str(e)}
                print(f"❌ {endpoint}: {e}")
        
        self.test_results["frontend_integration"] = integration_tests
    
    def extract_kb_id(self, heygen_response):
        """Extract knowledge base ID from HeyGen response"""
        possible_paths = [
            heygen_response.get('data', {}).get('knowledge_base_id'),
            heygen_response.get('data', {}).get('knowledgeBaseId'),
            heygen_response.get('data', {}).get('id'),
            heygen_response.get('knowledge_base_id'),
            heygen_response.get('knowledgeBaseId'),
            heygen_response.get('id')
        ]
        
        for path in possible_paths:
            if path and isinstance(path, str):
                return path
        
        return None
    
    def generate_diagnostic_report(self):
        """Generate comprehensive diagnostic report"""
        print("\n" + "=" * 60)
        print("📊 DIAGNOSTIC REPORT")
        print("=" * 60)
        
        # Overall status
        issues = []
        recommendations = []
        
        # Check environment
        if not self.test_results.get("environment", {}).get("HEYGEN_API_KEY", {}).get("exists"):
            issues.append("❌ HeyGen API key not configured")
            recommendations.append("1. Add HEYGEN_API_KEY to your .env file")
        
        # Check database
        db_schema = self.test_results.get("database_schema", {})
        missing_fields = [field for field, status in db_schema.items() 
                         if isinstance(status, dict) and not status.get("exists")]
        if missing_fields:
            issues.append(f"❌ Missing database fields: {missing_fields}")
            recommendations.append("2. Run database migration script")
        
        # Check API
        heygen_api = self.test_results.get("heygen_api", {})
        working_endpoint = heygen_api.get("working_endpoint")
        if not working_endpoint:
            issues.append("❌ No working HeyGen API endpoints")
            recommendations.append("3. Check HeyGen API key and network connection")
        
        # Check resume extraction
        resume_test = self.test_results.get("resume_extraction", {})
        if resume_test and not resume_test.get("extraction_successful"):
            issues.append("❌ Resume extraction failed")
            recommendations.append("4. Check resume file format and extraction libraries")
        
        # Print results
        if not issues:
            print("🎉 ALL TESTS PASSED! Knowledge Base system is ready.")
        else:
            print("⚠️ ISSUES FOUND:")
            for issue in issues:
                print(f"   {issue}")
            
            print("\n🔧 RECOMMENDATIONS:")
            for rec in recommendations:
                print(f"   {rec}")
        
        # Next steps
        print("\n📋 NEXT STEPS:")
        if not issues:
            print("✅ Your system is ready for Knowledge Base creation!")
            print("✅ You can now create interview knowledge bases")
            print("✅ Resume content will be extracted and used")
            print("✅ HeyGen API integration is working")
        else:
            print("1. Fix the issues listed above")
            print("2. Run this diagnostic again to verify fixes")
            print("3. Test with a real candidate interview")
        
        print("\n📞 SUPPORT:")
        print("If you need help:")
        print("- Check HeyGen API documentation")
        print("- Verify your API key permissions")
        print("- Ensure all dependencies are installed")
        print("- Run database migrations")
        
        self.test_results["summary"] = {
            "issues": issues,
            "recommendations": recommendations,
            "overall_status": "ready" if not issues else "needs_fixes"
        }
    
    def __del__(self):
        if hasattr(self, 'session'):
            self.session.close()


def main():
    """Main function to run diagnostics"""
    debugger = KnowledgeBaseDebugger()
    
    # Get candidate ID from user input or use first available
    candidate_id = None
    try:
        session = SessionLocal()
        candidates = session.query(Candidate).limit(5).all()
        
        if candidates:
            print("📋 Available candidates for testing:")
            for i, candidate in enumerate(candidates):
                resume_status = "📄" if candidate.resume_path and os.path.exists(candidate.resume_path) else "❌"
                print(f"   {candidate.id}: {candidate.name} - {candidate.job_title} {resume_status}")
            
            try:
                choice = input("\nEnter candidate ID to test (or press Enter to skip): ").strip()
                if choice.isdigit():
                    candidate_id = int(choice)
            except KeyboardInterrupt:
                print("\nTest cancelled.")
                return
        
        session.close()
    except Exception as e:
        print(f"Could not load candidates: {e}")
    
    # Run diagnostics
    results = debugger.run_complete_diagnosis(candidate_id)
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"kb_diagnostic_report_{timestamp}.json"
    
    try:
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Detailed results saved to: {report_file}")
    except Exception as e:
        print(f"Could not save report: {e}")


if __name__ == "__main__":
    main()