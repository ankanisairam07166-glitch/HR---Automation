# testlify_integration.py - Real-time Testlify API Integration

import os
import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from db import Candidate, SessionLocal
from email_util import send_interview_link_email, send_rejection_email
import json

logger = logging.getLogger(__name__)

class TestlifyIntegration:
    """Handle real-time integration with Testlify API"""
    
    def __init__(self):
        self.api_key = os.getenv('TESTLIFY_API_KEY')
        self.api_base_url = os.getenv('TESTLIFY_API_URL', 'https://api.testlify.com/v1')
        self.webhook_secret = os.getenv('TESTLIFY_WEBHOOK_SECRET')
        
        if not self.api_key:
            logger.warning("TESTLIFY_API_KEY not set - API polling disabled")
    
    async def poll_candidate_progress(self, assessment_id: str) -> List[Dict]:
        """Poll Testlify API for candidate progress"""
        if not self.api_key:
            return []
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/assessments/{assessment_id}/candidates"
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('candidates', [])
                    else:
                        logger.error(f"Testlify API error: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error polling Testlify: {e}")
            return []
    
    async def get_assessment_results(self, assessment_id: str, candidate_email: str) -> Optional[Dict]:
        """Get detailed assessment results for a candidate"""
        if not self.api_key:
            return None
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/assessments/{assessment_id}/candidates/{candidate_email}/results"
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Failed to get results for {candidate_email}: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error getting assessment results: {e}")
            return None
    
    def validate_webhook_signature(self, request_data: bytes, signature: str) -> bool:
        """Validate webhook signature from Testlify"""
        if not self.webhook_secret:
            logger.warning("TESTLIFY_WEBHOOK_SECRET not set - skipping validation")
            return True
        
        import hmac
        import hashlib
        
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            request_data,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
    async def sync_all_assessments(self):
        """Sync all active assessments with Testlify"""
        session = SessionLocal()
        try:
            # Get all candidates with pending assessments
            pending_candidates = session.query(Candidate).filter(
                Candidate.exam_link_sent == True,
                Candidate.exam_completed == False,
                Candidate.assessment_invite_link.isnot(None)
            ).all()
            
            logger.info(f"Syncing {len(pending_candidates)} pending assessments")
            
            # Group by assessment ID (extract from invite link)
            assessments = {}
            for candidate in pending_candidates:
                # Extract assessment ID from invite link
                # Example: https://candidate.testlify.com/auth/signup?key=abc123
                if 'key=' in candidate.assessment_invite_link:
                    assessment_id = candidate.assessment_invite_link.split('key=')[1].split('&')[0]
                    if assessment_id not in assessments:
                        assessments[assessment_id] = []
                    assessments[assessment_id].append(candidate)
            
            # Poll each assessment
            for assessment_id, candidates in assessments.items():
                progress_data = await self.poll_candidate_progress(assessment_id)
                
                for candidate in candidates:
                    # Find matching progress data
                    candidate_progress = next(
                        (p for p in progress_data if p.get('email') == candidate.email),
                        None
                    )
                    
                    if candidate_progress:
                        await self.update_candidate_progress(candidate, candidate_progress)
            
            session.commit()
            logger.info("Assessment sync completed")
            
        except Exception as e:
            logger.error(f"Error syncing assessments: {e}")
            session.rollback()
        finally:
            session.close()
    
    async def update_candidate_progress(self, candidate: Candidate, progress_data: Dict):
        """Update candidate record with latest progress"""
        try:
            status = progress_data.get('status', '').lower()
            
            if status == 'started' and not candidate.exam_started:
                candidate.exam_started = True
                candidate.exam_started_date = datetime.now()
                candidate.link_clicked = True
                candidate.link_clicked_date = datetime.now()
                logger.info(f"Updated {candidate.email}: Assessment started")
            
            elif status == 'completed' and not candidate.exam_completed:
                candidate.exam_completed = True
                candidate.exam_completed_date = datetime.now()
                
                # Get detailed results
                assessment_id = progress_data.get('assessment_id')
                if assessment_id:
                    results = await self.get_assessment_results(assessment_id, candidate.email)
                    
                    if results:
                        candidate.exam_score = results.get('correct_answers', 0)
                        candidate.exam_total_questions = results.get('total_questions', 0)
                        candidate.exam_percentage = results.get('percentage', 0)
                        candidate.exam_time_taken = results.get('time_taken_minutes', 0)
                        
                        # Process based on score
                        if candidate.exam_percentage >= 70:
                            candidate.final_status = 'Interview Scheduled'
                            candidate.interview_scheduled = True
                            candidate.interview_date = datetime.now() + timedelta(days=3)
                            
                            # Send interview invitation
                            interview_link = send_interview_link_email(candidate)
                            candidate.interview_link = interview_link
                            logger.info(f"Scheduled interview for {candidate.email}")
                        else:
                            candidate.final_status = 'Rejected After Exam'
                            send_rejection_email(candidate)
                            logger.info(f"Sent rejection to {candidate.email}")
                
                logger.info(f"Updated {candidate.email}: Assessment completed ({candidate.exam_percentage}%)")
                
        except Exception as e:
            logger.error(f"Error updating candidate progress: {e}")


class TestlifyPollingService:
    """Background service to poll Testlify for updates"""
    
    def __init__(self, poll_interval_seconds=300):  # Poll every 5 minutes
        self.poll_interval = poll_interval_seconds
        self.integration = TestlifyIntegration()
        self.running = False
    
    async def start(self):
        """Start the polling service"""
        self.running = True
        logger.info(f"Starting Testlify polling service (interval: {self.poll_interval}s)")
        
        while self.running:
            try:
                await self.integration.sync_all_assessments()
            except Exception as e:
                logger.error(f"Polling error: {e}")
            
            await asyncio.sleep(self.poll_interval)
    
    def stop(self):
        """Stop the polling service"""
        self.running = False
        logger.info("Stopping Testlify polling service")


# Webhook processor for real-time updates
async def process_testlify_webhook(webhook_data: Dict) -> Dict:
    """Process incoming Testlify webhook"""
    integration = TestlifyIntegration()
    
    event_type = webhook_data.get('event_type')
    candidate_email = webhook_data.get('candidate', {}).get('email')
    
    if not candidate_email:
        return {"error": "Missing candidate email"}
    
    session = SessionLocal()
    try:
        candidate = session.query(Candidate).filter_by(email=candidate_email).first()
        
        if not candidate:
            return {"error": "Candidate not found"}
        
        if event_type == 'assessment.started':
            candidate.exam_started = True
            candidate.exam_started_date = datetime.now()
            candidate.link_clicked = True
            candidate.link_clicked_date = datetime.now()
            
        elif event_type == 'assessment.completed':
            candidate.exam_completed = True
            candidate.exam_completed_date = datetime.now()
            
            # Extract score data
            score_data = webhook_data.get('score', {})
            candidate.exam_score = score_data.get('correct_answers', 0)
            candidate.exam_total_questions = score_data.get('total_questions', 0)
            candidate.exam_percentage = score_data.get('percentage', 0)
            candidate.exam_time_taken = score_data.get('time_taken_minutes', 0)
            
            # Add detailed feedback based on performance
            if candidate.exam_percentage >= 90:
                candidate.exam_feedback = "Outstanding performance! You demonstrated exceptional knowledge and problem-solving skills."
            elif candidate.exam_percentage >= 80:
                candidate.exam_feedback = "Excellent performance! You showed strong technical competence and understanding."
            elif candidate.exam_percentage >= 70:
                candidate.exam_feedback = "Good performance! You demonstrated solid understanding of key concepts."
            elif candidate.exam_percentage >= 60:
                candidate.exam_feedback = "Fair performance. Some areas showed promise, but there's room for improvement."
            else:
                candidate.exam_feedback = "The assessment revealed opportunities for growth in fundamental concepts."
            
            # Decision making
            if candidate.exam_percentage >= 70:
                candidate.final_status = 'Interview Scheduled'
                candidate.interview_scheduled = True
                candidate.interview_date = datetime.now() + timedelta(days=3)
                
                # Send interview email
                interview_link = send_interview_link_email(candidate)
                candidate.interview_link = interview_link
            else:
                candidate.final_status = 'Rejected After Exam'
                send_rejection_email(candidate)
        
        elif event_type == 'assessment.abandoned':
            # Candidate started but didn't complete
            if not candidate.exam_completed:
                candidate.final_status = 'Assessment Abandoned'
        
        session.commit()
        return {"success": True, "candidate": candidate.email, "event": event_type}
        
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        session.rollback()
        return {"error": str(e)}
    finally:
        session.close()


# Utility function to extract assessment ID from invite link
def extract_assessment_id(invite_link: str) -> Optional[str]:
    """Extract assessment ID from Testlify invite link"""
    try:
        if 'key=' in invite_link:
            return invite_link.split('key=')[1].split('&')[0]
        elif '/assessment/' in invite_link:
            return invite_link.split('/assessment/')[1].split('/')[0]
        return None
    except:
        return None


# Function to start polling in background (call from main app)
def start_testlify_polling():
    """Start the Testlify polling service in background"""
    polling_service = TestlifyPollingService()
    
    # Run in background thread
    import threading
    
    def run_polling():
        asyncio.new_event_loop().run_until_complete(polling_service.start())
    
    polling_thread = threading.Thread(target=run_polling, daemon=True)
    polling_thread.start()
    
    return polling_service


if __name__ == "__main__":
    # Test the integration
    logging.basicConfig(level=logging.INFO)
    
    async def test():
        integration = TestlifyIntegration()
        await integration.sync_all_assessments()
    
    asyncio.run(test())