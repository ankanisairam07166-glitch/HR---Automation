# interview_automation.py - Add this file to your backend folder
import os
import time
import threading
import logging
from datetime import datetime, timedelta
import requests
import json
from db import Candidate, SessionLocal
from email_util import send_email
import uuid
from sqlalchemy import and_, or_

logger = logging.getLogger(__name__)

class InterviewAutomationSystem:
    """Automated interview system that runs 24/7"""
    
    def __init__(self):
        self.is_running = False
        self.check_interval = 1800  # 30 minutes in seconds
        self.heygen_api_key = os.getenv('HEYGEN_API_KEY')
        self.heygen_api_url = 'https://api.heygen.com/v1/streaming/knowledge_base/create'
        
    def start(self):
        """Start the automation system"""
        if self.is_running:
            logger.warning("Interview automation system is already running")
            return
            
        self.is_running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info("🚀 Interview automation system started")
        
    def stop(self):
        """Stop the automation system"""
        self.is_running = False
        if hasattr(self, 'thread'):
            self.thread.join()
        logger.info("Interview automation system stopped")
        
    def _run_loop(self):
        """Main loop that runs every 30 minutes"""
        while self.is_running:
            try:
                logger.info("🔄 Running interview automation check...")
                self._process_candidates()
            except Exception as e:
                logger.error(f"Error in interview automation loop: {e}", exc_info=True)
            
            # Wait for 30 minutes
            time.sleep(self.check_interval)
    
    def _process_candidates(self):
        """Process candidates who passed assessment but don't have interview links"""
        session = SessionLocal()
        try:
            # Find candidates who:
            # 1. Completed the exam
            # 2. Passed (score >= 70%)
            # 3. Don't have interview scheduled yet
            # 4. Don't have interview_kb_id (knowledge base not created)
            candidates = session.query(Candidate).filter(
                and_(
                    Candidate.exam_completed == True,
                    Candidate.exam_percentage >= 70,
                    Candidate.interview_scheduled == False,
                    or_(
                        Candidate.interview_kb_id == None,
                        Candidate.interview_kb_id == ''
                    )
                )
            ).all()
            
            logger.info(f"Found {len(candidates)} candidates ready for interview setup")
            
            for candidate in candidates:
                try:
                    self._setup_interview_for_candidate(candidate, session)
                except Exception as e:
                    logger.error(f"Failed to setup interview for candidate {candidate.id}: {e}")
                    continue
                    
            session.commit()
            
        except Exception as e:
            logger.error(f"Error processing candidates: {e}")
            session.rollback()
        finally:
            session.close()
    
    def _setup_interview_for_candidate(self, candidate, session):
        """Setup interview for a single candidate"""
        logger.info(f"Setting up interview for {candidate.name} ({candidate.email})")
        
        # Step 1: Create knowledge base in HeyGen
        kb_id = self._create_knowledge_base(candidate)
        if not kb_id:
            logger.error(f"Failed to create knowledge base for {candidate.name}")
            return
            
        # Step 2: Generate interview link
        interview_token = str(uuid.uuid4())
        interview_link = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/interview/{interview_token}"
        
        # Step 3: Update candidate record
        candidate.interview_kb_id = kb_id
        candidate.interview_token = interview_token
        candidate.interview_link = interview_link
        candidate.interview_scheduled = True
        candidate.interview_date = datetime.now() + timedelta(days=1)  # Schedule for tomorrow
        candidate.final_status = 'Interview Scheduled'
        
        # Step 4: Send email to candidate
        self._send_interview_email(candidate)
        
        logger.info(f"✅ Interview setup complete for {candidate.name}")
        
    def _create_knowledge_base(self, candidate):
        """Create HeyGen knowledge base for the candidate"""
        try:
            # Get job description from candidate's job
            job_desc = self._get_job_description(candidate.job_id, candidate.job_title)
            
            # Prepare knowledge base data
            kb_name = f"Interview - {candidate.name} - {candidate.job_title} - {datetime.now().strftime('%Y-%m-%d')}"
            opening_line = f"Hello {candidate.name}, welcome to your interview for the {candidate.job_title} position."
            
            custom_prompt = self._generate_interview_prompt(
                candidate_name=candidate.name,
                position=candidate.job_title,
                job_description=job_desc,
                company_name=os.getenv('COMPANY_NAME', 'Our Company')
            )
            
            # Prepare useful links (resume if available)
            useful_links = []
            if candidate.resume_path:
                # Convert local resume path to accessible URL
                resume_url = self._get_resume_url(candidate.resume_path)
                if resume_url:
                    useful_links.append(resume_url)
            
            # Create knowledge base via HeyGen API
            headers = {
                'x-api-key': self.heygen_api_key,
                'Content-Type': 'application/json'
            }
            
            payload = {
                'name': kb_name,
                'opening_line': opening_line,
                'custom_prompt': custom_prompt,
                'useful_links': useful_links
            }
            
            response = requests.post(self.heygen_api_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                kb_id = result.get('data', {}).get('knowledge_base_id')
                logger.info(f"Created knowledge base: {kb_id}")
                return kb_id
            else:
                logger.error(f"HeyGen API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating knowledge base: {e}")
            return None
    
    def _get_job_description(self, job_id, job_title):
        """Get job description from BambooHR or use default"""
        # Try to get from BambooHR first
        try:
            API_KEY = os.getenv("BAMBOOHR_API_KEY")
            SUBDOMAIN = os.getenv("BAMBOOHR_SUBDOMAIN")
            
            if API_KEY and SUBDOMAIN:
                auth = (API_KEY, "x")
                headers = {"Accept": "application/json"}
                url = f"https://api.bamboohr.com/api/gateway.php/{SUBDOMAIN}/v1/applicant_tracking/jobs/{job_id}"
                
                resp = requests.get(url, auth=auth, headers=headers, timeout=10)
                if resp.status_code == 200:
                    job_data = resp.json()
                    return job_data.get('description', '')
        except:
            pass
        
        # Return default job description
        return f"""
We are looking for a talented {job_title} to join our team. The ideal candidate will have:
- Strong technical skills relevant to the {job_title} role
- Excellent problem-solving abilities
- Good communication and teamwork skills
- Passion for learning and growth
- Ability to work in a fast-paced environment
"""
    
    def _get_resume_url(self, resume_path):
        """Convert local resume path to accessible URL"""
        # If you have a file server or S3, upload and return URL
        # For now, return None if not implemented
        return None
    
    def _generate_interview_prompt(self, candidate_name, position, job_description, company_name):
        """Generate the interview prompt for HeyGen"""
        return f"""
# Professional Interview Assistant

## CANDIDATE INFORMATION
**Name**: {candidate_name}
**Position**: {position}
**Company**: {company_name}

## JOB DESCRIPTION
{job_description}

## INTERVIEW PROTOCOL

### Interview Structure

#### 1. Opening (2-3 minutes)
"Hello {candidate_name}, I'm your AI interviewer for the {position} position at {company_name}. Congratulations on passing the technical assessment! This interview will help us understand your experience and how you'd contribute to our team. Shall we begin?"

#### 2. Experience Review (10-12 minutes)
- Walk through their career progression
- Discuss relevant projects and achievements
- Understand their technical expertise
- Explore their problem-solving approach

**Key Questions:**
- "Can you walk me through your professional journey and what led you to apply for this {position} role?"
- "What project are you most proud of and why?"
- "How do you stay updated with the latest developments in your field?"

#### 3. Technical Deep Dive (12-15 minutes)
Based on their assessment results and the job requirements:
- Discuss specific technologies mentioned in the job description
- Explore their approach to common challenges in the role
- Assess their ability to explain complex concepts
- Understand their learning methodology

#### 4. Behavioral Assessment (10-12 minutes)
Using the STAR method:
- "Tell me about a time you had to meet a tight deadline"
- "Describe a situation where you disagreed with a team member"
- "Give an example of when you had to learn something completely new"
- "How do you handle feedback and criticism?"

#### 5. Cultural Fit & Motivation (5-7 minutes)
- Why are they interested in {company_name}?
- What are their career goals?
- How do they prefer to work and communicate?
- What questions do they have about the role or company?

#### 6. Closing (2-3 minutes)
- Thank them for their time
- Explain the next steps
- Ask if they have any final questions
- Professional closing

### Assessment Criteria
1. **Technical Competency** (35%)
2. **Communication Skills** (25%)
3. **Problem Solving** (20%)
4. **Cultural Fit** (20%)

### Important Notes
- Be encouraging and supportive
- Allow time for thoughtful responses
- Ask follow-up questions for clarity
- Maintain a professional yet friendly tone
- Focus on potential and growth mindset

Remember: The candidate has already passed the technical assessment, so focus on understanding their experience, work style, and cultural fit.
"""
    
    def _send_interview_email(self, candidate):
        """Send interview invitation email"""
        try:
            subject = f"Interview Invitation - {candidate.job_title} Position"
            
            body_html = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #2c3e50;">Congratulations, {candidate.name}!</h2>
                        
                        <p>We are pleased to inform you that you have successfully passed the technical assessment for the <strong>{candidate.job_title}</strong> position.</p>
                        
                        <p>We would like to invite you to the next stage - an AI-powered interview where you'll have the opportunity to discuss your experience and aspirations.</p>
                        
                        <div style="background-color: #f0f8ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <h3 style="color: #2c3e50; margin-top: 0;">Interview Details:</h3>
                            <p><strong>Position:</strong> {candidate.job_title}</p>
                            <p><strong>Format:</strong> AI-Powered Video Interview</p>
                            <p><strong>Duration:</strong> Approximately 30-45 minutes</p>
                            <p><strong>Available:</strong> Next 7 days</p>
                        </div>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{candidate.interview_link}" style="display: inline-block; padding: 12px 30px; background-color: #3498db; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">Start Your Interview</a>
                        </div>
                        
                        <h3 style="color: #2c3e50;">What to Expect:</h3>
                        <ul>
                            <li>The interview will be conducted by an AI interviewer</li>
                            <li>You'll discuss your experience, skills, and career goals</li>
                            <li>The interview is conversational and designed to help us get to know you better</li>
                            <li>You can take the interview at your convenience within the next 7 days</li>
                        </ul>
                        
                        <h3 style="color: #2c3e50;">Technical Requirements:</h3>
                        <ul>
                            <li>A computer with a webcam and microphone</li>
                            <li>Stable internet connection</li>
                            <li>A quiet environment free from distractions</li>
                            <li>Google Chrome or Microsoft Edge browser</li>
                        </ul>
                        
                        <p style="background-color: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107;">
                            <strong>Important:</strong> This interview link is unique to you and will expire in 7 days. Please complete your interview before then.
                        </p>
                        
                        <p>If you have any questions or technical difficulties, please don't hesitate to reach out to us.</p>
                        
                        <p>We look forward to speaking with you!</p>
                        
                        <p>Best regards,<br>
                        The Recruitment Team<br>
                        {os.getenv('COMPANY_NAME', 'Our Company')}</p>
                    </div>
                </body>
            </html>
            """
            
            from email_util import send_email
            send_email(candidate.email, subject, body_html)
            logger.info(f"Interview email sent to {candidate.email}")
            
        except Exception as e:
            logger.error(f"Failed to send interview email to {candidate.email}: {e}")

# Global instance
interview_automation = InterviewAutomationSystem()

def start_interview_automation():
    """Start the interview automation system"""
    interview_automation.start()

def stop_interview_automation():
    """Stop the interview automation system"""
    interview_automation.stop()