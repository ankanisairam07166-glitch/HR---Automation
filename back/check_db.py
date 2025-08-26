# check_db.py
from db import SessionLocal, Candidate, engine
from sqlalchemy import inspect
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database_schema():
    """Check if all interview fields exist in database"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('candidates')]
    
    required_fields = [
        'interview_completed_at',
        'interview_started_at',
        'interview_status',
        'interview_progress_percentage',
        'interview_duration',
        'interview_ai_analysis_status',
        'interview_qa_pairs',
        'interview_token'
    ]
    
    missing_fields = [field for field in required_fields if field not in columns]
    
    if missing_fields:
        logger.warning(f"Missing fields in database: {missing_fields}")
        return False
    else:
        logger.info("All required fields exist in database")
        return True

def check_candidate_by_token(token):
    """Check specific candidate by token"""
    session = SessionLocal()
    try:
        candidate = session.query(Candidate).filter_by(interview_token=token).first()
        
        if not candidate:
            logger.error(f"No candidate found with token: {token}")
            return
        
        logger.info(f"Found candidate: ID={candidate.id}, Name={candidate.name}")
        logger.info(f"Interview completed at: {candidate.interview_completed_at}")
        logger.info(f"Interview started at: {candidate.interview_started_at}")
        logger.info(f"Final status: {candidate.final_status}")
        
        # Check if fields exist
        for field in ['interview_completed_at', 'interview_status', 'interview_duration']:
            has_field = hasattr(candidate, field)
            value = getattr(candidate, field, 'N/A') if has_field else 'Field missing'
            logger.info(f"{field}: {value} (exists: {has_field})")
            
    finally:
        session.close()

if __name__ == "__main__":
    # Check schema
    check_database_schema()
    
    # Check specific candidate
    token = "a4efdef6-d27e-4327-a59f-d4524ebe0af0"
    check_candidate_by_token(token)