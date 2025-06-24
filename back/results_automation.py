# results_automation.py - Automated results checking and processing

import asyncio
import schedule
import time
import logging
import requests
from datetime import datetime, timedelta
from db import Candidate, SessionLocal
from sqlalchemy import and_
from testlify_results_scraper import scrape_all_pending_assessments
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/results_automation.log'),
        logging.StreamHandler()
    ]
)

class ResultsAutomation:
    """Automated results checking and processing"""
    
    def __init__(self):
        self.backend_url = os.getenv('BACKEND_URL', 'http://localhost:5000')
        self.check_interval_minutes = int(os.getenv('RESULTS_CHECK_INTERVAL', '30'))  # Default: 30 minutes
        self.max_assessment_age_hours = int(os.getenv('MAX_ASSESSMENT_AGE_HOURS', '72'))  # 3 days
    
    async def check_and_process_results(self):
        """Main function to check and process assessment results"""
        try:
            logging.info("🔍 Starting automated results check...")
            
            # Get candidates who need result checking
            candidates_to_check = self.get_candidates_needing_check()
            
            if not candidates_to_check:
                logging.info("No candidates need result checking at this time")
                return
            
            logging.info(f"Found {len(candidates_to_check)} candidates needing result check")
            
            # Group by assessment/job title
            assessments_to_check = self.group_candidates_by_assessment(candidates_to_check)
            
            # Process each assessment
            results_summary = {}
            for assessment_name, candidates in assessments_to_check.items():
                try:
                    logging.info(f"Checking results for assessment: {assessment_name}")
                    results = await self.check_assessment_results(assessment_name)
                    results_summary[assessment_name] = len(results)
                    
                    # Small delay between assessments
                    await asyncio.sleep(5)
                    
                except Exception as e:
                    logging.error(f"Error checking {assessment_name}: {e}")
                    results_summary[assessment_name] = f"Error: {str(e)}"
            
            logging.info(f"✅ Results check completed. Summary: {results_summary}")
            
        except Exception as e:
            logging.error(f"Error in automated results check: {e}")
    
    def get_candidates_needing_check(self):
        """Get candidates who need their results checked"""
        session = SessionLocal()
        try:
            # Find candidates who:
            # 1. Have been sent assessment links
            # 2. Haven't completed the exam yet
            # 3. Assessment was sent within the last X hours (not too old)
            cutoff_time = datetime.now() - timedelta(hours=self.max_assessment_age_hours)
            
            candidates = session.query(Candidate).filter(
                and_(
                    Candidate.exam_link_sent == True,
                    Candidate.exam_completed == False,
                    Candidate.exam_link_sent_date > cutoff_time,
                    Candidate.assessment_invite_link.isnot(None)
                )
            ).all()
            
            return candidates
            
        finally:
            session.close()
    
    def group_candidates_by_assessment(self, candidates):
        """Group candidates by their assessment/job title"""
        assessments = {}
        for candidate in candidates:
            assessment_name = candidate.job_title
            if assessment_name:
                if assessment_name not in assessments:
                    assessments[assessment_name] = []
                assessments[assessment_name].append(candidate)
        return assessments
    
    async def check_assessment_results(self, assessment_name: str):
        """Check results for a specific assessment"""
        try:
            # Import the scraper function
            from testlify_results_scraper import scrape_assessment_results_by_name
            
            # Run the scraping
            results = await scrape_assessment_results_by_name(assessment_name)
            
            logging.info(f"Found {len(results)} results for {assessment_name}")
            return results
            
        except Exception as e:
            logging.error(f"Error checking results for {assessment_name}: {e}")
            return []
    
    def send_backend_notification(self, endpoint: str, data: dict):
        """Send notification to backend API"""
        try:
            url = f"{self.backend_url}/api/{endpoint}"
            response = requests.post(url, json=data, timeout=30)
            
            if response.status_code == 200:
                logging.info(f"Successfully notified backend: {endpoint}")
            else:
                logging.warning(f"Backend notification failed: {response.status_code}")
                
        except Exception as e:
            logging.error(f"Error sending backend notification: {e}")
    
    async def emergency_result_check(self, candidate_email: str):
        """Emergency check for a specific candidate"""
        try:
            session = SessionLocal()
            candidate = session.query(Candidate).filter_by(email=candidate_email).first()
            session.close()
            
            if not candidate:
                logging.error(f"Candidate {candidate_email} not found")
                return False
            
            if candidate.job_title:
                results = await self.check_assessment_results(candidate.job_title)
                
                # Look for this specific candidate in results
                for result in results:
                    if result.get('email') == candidate_email:
                        logging.info(f"Found emergency result for {candidate_email}: {result.get('status')}")
                        return True
            
            return False
            
        except Exception as e:
            logging.error(f"Error in emergency result check: {e}")
            return False


# Scheduled functions
def run_automated_check():
    """Run automated check (called by scheduler)"""
    try:
        automation = ResultsAutomation()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(automation.check_and_process_results())
        loop.close()
    except Exception as e:
        logging.error(f"Error in scheduled check: {e}")


def run_daily_cleanup():
    """Daily cleanup of old data"""
    try:
        logging.info("🧹 Running daily cleanup...")
        
        session = SessionLocal()
        try:
            # Mark very old pending assessments as expired
            expire_cutoff = datetime.now() - timedelta(days=7)  # 7 days old
            
            expired_candidates = session.query(Candidate).filter(
                and_(
                    Candidate.exam_link_sent == True,
                    Candidate.exam_completed == False,
                    Candidate.exam_link_sent_date < expire_cutoff
                )
            ).all()
            
            for candidate in expired_candidates:
                candidate.final_status = 'Assessment Expired'
                logging.info(f"Marked assessment as expired for {candidate.email}")
            
            session.commit()
            logging.info(f"Cleanup completed. Expired {len(expired_candidates)} old assessments.")
            
        finally:
            session.close()
            
    except Exception as e:
        logging.error(f"Error in daily cleanup: {e}")


def setup_scheduler():
    """Setup the scheduled tasks"""
    automation = ResultsAutomation()
    
    # Schedule regular results checking
    schedule.every(automation.check_interval_minutes).minutes.do(run_automated_check)
    
    # Schedule daily cleanup at 2 AM
    schedule.every().day.at("02:00").do(run_daily_cleanup)
    
    # Schedule a more thorough check every 4 hours
    schedule.every(4).hours.do(run_automated_check)
    
    logging.info(f"Scheduler setup complete:")
    logging.info(f"- Results check every {automation.check_interval_minutes} minutes")
    logging.info(f"- Thorough check every 4 hours")
    logging.info(f"- Daily cleanup at 2:00 AM")


def run_scheduler():
    """Run the scheduler (main loop)"""
    print("🤖 Starting Results Automation Scheduler...")
    print("=" * 50)
    
    setup_scheduler()
    
    print("✅ Scheduler is running. Press Ctrl+C to stop.")
    print(f"Next check in {ResultsAutomation().check_interval_minutes} minutes...")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        print("\n🛑 Scheduler stopped by user")
    except Exception as e:
        logging.error(f"Scheduler error: {e}")
        print(f"❌ Scheduler error: {e}")


# Manual trigger functions
async def manual_check_all():
    """Manually trigger check for all pending assessments"""
    automation = ResultsAutomation()
    await automation.check_and_process_results()


async def manual_check_assessment(assessment_name: str):
    """Manually check specific assessment"""
    automation = ResultsAutomation()
    results = await automation.check_assessment_results(assessment_name)
    print(f"Found {len(results)} results for {assessment_name}")
    return results


async def manual_check_candidate(candidate_email: str):
    """Manually check specific candidate"""
    automation = ResultsAutomation()
    found = await automation.emergency_result_check(candidate_email)
    print(f"Emergency check for {candidate_email}: {'Found' if found else 'Not found'}")
    return found


# CLI interface
def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python results_automation.py scheduler    # Run scheduler")
        print("  python results_automation.py check-all    # Manual check all")
        print("  python results_automation.py check-assessment 'Assessment Name'")
        print("  python results_automation.py check-candidate email@example.com")
        return
    
    command = sys.argv[1]
    
    if command == "scheduler":
        run_scheduler()
    
    elif command == "check-all":
        asyncio.run(manual_check_all())
    
    elif command == "check-assessment" and len(sys.argv) > 2:
        assessment_name = sys.argv[2]
        asyncio.run(manual_check_assessment(assessment_name))
    
    elif command == "check-candidate" and len(sys.argv) > 2:
        candidate_email = sys.argv[2]
        asyncio.run(manual_check_candidate(candidate_email))
    
    else:
        print("Invalid command or missing arguments!")


if __name__ == "__main__":
    main()