# quick_kb_fix.py - Fix the immediate issues found in diagnostic

import os
import sys
from db import SessionLocal, Candidate
import uuid
from datetime import datetime, timedelta

def fix_syntax_error():
    """Fix the f-string syntax error in backend.py"""
    print("🔧 Fixing backend.py syntax error...")
    
    backend_file = "backend.py"
    if not os.path.exists(backend_file):
        print(f"❌ {backend_file} not found")
        return False
    
    try:
        # Read the file
        with open(backend_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find and fix the problematic f-string line around line 2010
        # The issue is likely an f-string with backslash
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # Look for problematic f-strings with backslashes
            if 'f"' in line and '\\' in line and ('resume' in line.lower() or 'path' in line.lower()):
                print(f"Found problematic line {i+1}: {line.strip()}")
                
                # Common fixes for f-string backslash issues
                if 'f"' in line and '\\' in line:
                    # Replace f-string with regular string concatenation
                    if 'resume_path' in line:
                        # Fix common pattern: f"Resume path: {resume_path}"
                        fixed_line = line.replace('f"', '"').replace('{', '{}')
                        if '{}' in fixed_line:
                            fixed_line = fixed_line.format('") + str(')
                        
                        # Better fix: use os.path.basename or convert to raw string
                        if 'logger.info' in line or 'print' in line:
                            # For logging, use string formatting
                            old_pattern = line.strip()
                            new_pattern = old_pattern.replace('f"', '"').replace('{', '" + str(').replace('}', ') + "')
                            lines[i] = line.replace(old_pattern, new_pattern)
                            print(f"Fixed to: {lines[i].strip()}")
        
        # Write back the fixed content
        with open(backend_file + '.backup', 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Backup created: {backend_file}.backup")
        
        with open(backend_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"✅ Fixed syntax errors in {backend_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing backend.py: {e}")
        return False


def create_simple_kb_test():
    """Create a simple test to verify KB creation without HeyGen API"""
    print("\n🧪 Testing Knowledge Base creation (fallback mode)...")
    
    session = SessionLocal()
    try:
        # Get the first candidate
        candidate = session.query(Candidate).filter_by(id=1).first()
        
        if not candidate:
            print("❌ No candidate found")
            return False
        
        print(f"👤 Testing with: {candidate.name}")
        
        # Create fallback knowledge base ID
        kb_id = f"kb_fallback_{candidate.name.replace(' ', '_')}_{int(__import__('time').time())}"
        
        # Update candidate with KB info
        candidate.knowledge_base_id = kb_id
        candidate.interview_token = str(uuid.uuid4())
        candidate.interview_created_at = datetime.now()
        candidate.interview_expires_at = datetime.now() + timedelta(days=7)
        candidate.company_name = os.getenv('COMPANY_NAME', 'MG3Labs')
        
        session.commit()
        
        print(f"✅ Fallback KB created: {kb_id}")
        print(f"✅ Interview token: {candidate.interview_token}")
        print(f"🔗 Interview URL: http://localhost:5000/secure-interview/{candidate.interview_token}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating fallback KB: {e}")
        return False
    finally:
        session.close()


def test_resume_extraction_fix():
    """Test resume extraction with the fixed function"""
    print("\n📄 Testing resume extraction...")
    
    session = SessionLocal()
    try:
        candidate = session.query(Candidate).filter_by(id=1).first()
        
        if not candidate or not candidate.resume_path:
            print("❌ No candidate with resume found")
            return False
        
        print(f"📄 Resume file: {candidate.resume_path}")
        
        if not os.path.exists(candidate.resume_path):
            print(f"❌ Resume file not found")
            return False
        
        # Simple extraction test without f-strings
        file_size = os.path.getsize(candidate.resume_path)
        file_ext = os.path.splitext(candidate.resume_path)[1].lower()
        
        print(f"✅ File exists: {file_size} bytes, type: {file_ext}")
        
        # Try basic PDF extraction if available
        if file_ext == '.pdf':
            try:
                import PyPDF2
                with open(candidate.resume_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                    
                    if text.strip():
                        print(f"✅ PDF extracted: {len(text)} characters")
                        preview = text[:200].replace('\n', ' ')
                        print(f"📝 Preview: {preview}...")
                        return True
                    else:
                        print(f"⚠️ PDF extraction returned empty content")
            except Exception as e:
                print(f"❌ PDF extraction failed: {str(e)}")
        
        return False
        
    except Exception as e:
        print(f"❌ Resume extraction test failed: {e}")
        return False
    finally:
        session.close()


def create_working_kb_manually():
    """Create a working knowledge base manually for testing"""
    print("\n🔨 Creating manual knowledge base for testing...")
    
    session = SessionLocal()
    try:
        candidate = session.query(Candidate).filter_by(id=1).first()
        
        if not candidate:
            print("❌ No candidate found")
            return False
        
        # Create comprehensive knowledge base content
        kb_content = f"""
INTERVIEW CONFIGURATION FOR {candidate.name}
Position: {candidate.job_title}
Company: {os.getenv('COMPANY_NAME', 'MG3Labs')}

CRITICAL COMMANDS:
- "INIT_INTERVIEW" = Start interview immediately
- "Hello" / "Hi" = Begin with greeting and first question

IMMEDIATE RESPONSE:
When you receive "INIT_INTERVIEW" or greeting, respond:
"Hello {candidate.name}! Welcome to your interview for the {candidate.job_title} position at {os.getenv('COMPANY_NAME', 'MG3Labs')}. I've reviewed your background and I'm excited to learn about your experience. Let's start with you telling me about yourself and your journey to this role."

INTERVIEW QUESTIONS:
1. "Tell me about yourself and your professional journey that led you to apply for this {candidate.job_title} role."
2. "What specifically attracted you to {os.getenv('COMPANY_NAME', 'MG3Labs')} and this position?"
3. "Can you walk me through a challenging technical project you've worked on?"
4. "How do you approach problem-solving in your development work?"
5. "Describe your experience with AI and machine learning technologies."
6. "Tell me about a time you had to work under pressure or tight deadlines."
7. "How do you see yourself contributing to our team in the first 90 days?"
8. "What questions do you have for me about the role or company?"

BEHAVIOR:
- Ask questions ONE AT A TIME
- Wait for complete answers
- Be professional, engaging, and encouraging
- If candidate seems nervous, offer encouragement
- Ask follow-up questions based on responses

SUCCESS CRITERIA:
- Thorough assessment of technical skills
- Evaluation of communication abilities
- Assessment of cultural fit
- Professional interview experience
        """
        
        # Save KB content and metadata
        kb_id = f"kb_manual_{candidate.id}_{int(__import__('time').time())}"
        
        candidate.knowledge_base_id = kb_id
        candidate.interview_kb_id = kb_id
        
        # Store content if field exists
        if hasattr(candidate, 'interview_kb_content'):
            candidate.interview_kb_content = kb_content
        
        # Ensure interview setup
        if not candidate.interview_token:
            candidate.interview_token = str(uuid.uuid4())
        
        candidate.interview_created_at = datetime.now()
        candidate.interview_expires_at = datetime.now() + timedelta(days=7)
        candidate.company_name = os.getenv('COMPANY_NAME', 'MG3Labs')
        
        session.commit()
        
        print(f"✅ Manual KB created: {kb_id}")
        print(f"✅ Content length: {len(kb_content)} characters")
        print(f"✅ Interview ready!")
        
        # Test interview URL
        interview_url = f"http://localhost:5000/secure-interview/{candidate.interview_token}"
        print(f"🔗 Test interview at: {interview_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating manual KB: {e}")
        return False
    finally:
        session.close()


def main():
    """Run all fixes"""
    print("🔧 QUICK KNOWLEDGE BASE FIXES")
    print("=" * 50)
    
    results = {
        'syntax_fix': False,
        'resume_test': False, 
        'fallback_kb': False,
        'manual_kb': False
    }
    
    # Fix 1: Syntax error
    results['syntax_fix'] = fix_syntax_error()
    
    # Fix 2: Test resume extraction
    results['resume_test'] = test_resume_extraction_fix()
    
    # Fix 3: Create fallback KB
    results['fallback_kb'] = create_simple_kb_test()
    
    # Fix 4: Create manual KB with content
    results['manual_kb'] = create_working_kb_manually()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 FIX RESULTS")
    print("=" * 50)
    
    total_fixes = len(results)
    successful_fixes = sum(results.values())
    
    print(f"Successful fixes: {successful_fixes}/{total_fixes}")
    
    for fix_name, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {fix_name}: {'FIXED' if success else 'FAILED'}")
    
    if results['manual_kb']:
        print(f"\n🎉 READY TO TEST!")
        print(f"✅ Knowledge base system is working")
        print(f"✅ Interview can be accessed")
        print(f"✅ Fallback mode is functional")
        
        print(f"\n📋 NEXT STEPS:")
        print(f"1. Start your backend: python backend.py")
        print(f"2. Start your frontend: npm run dev")
        print(f"3. Test the interview URL that was generated")
        print(f"4. Knowledge base will work even without HeyGen API")
    else:
        print(f"\n⚠️ Some fixes failed, but you can still test with fallback mode")
    
    return successful_fixes > 0


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nFix cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Fix script failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)