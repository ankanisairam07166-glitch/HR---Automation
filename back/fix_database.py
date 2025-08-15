# fix_database.py
import os
import sys
from sqlalchemy import text, inspect
from db import engine, SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_and_add_columns():
    """Check and add missing columns to candidates table"""
    
    required_columns = {
        'job_description': 'TEXT',
        'company_name': 'VARCHAR(200)',
        'knowledge_base_id': 'VARCHAR(200)',
        'interview_kb_id': 'VARCHAR(200)',
        'interview_session_id': 'VARCHAR(200)',
        'interview_time_slot': 'VARCHAR(100)',
        'interview_email_sent': 'INTEGER DEFAULT 0',  # SQLite uses INTEGER for boolean
        'interview_email_sent_date': 'DATETIME',
        'interview_email_attempts': 'INTEGER DEFAULT 0',
        'interview_questions_asked': 'TEXT',
        'interview_answers_given': 'TEXT',
        'interview_total_questions': 'INTEGER DEFAULT 0',
        'interview_answered_questions': 'INTEGER DEFAULT 0'
    }
    
    # Get existing columns
    inspector = inspect(engine)
    existing_columns = [col['name'] for col in inspector.get_columns('candidates')]
    
    logger.info(f"Existing columns: {existing_columns}")
    
    # Add missing columns
    with engine.connect() as conn:
        for column_name, column_type in required_columns.items():
            if column_name not in existing_columns:
                try:
                    query = f"ALTER TABLE candidates ADD COLUMN {column_name} {column_type}"
                    conn.execute(text(query))
                    conn.commit()
                    logger.info(f"✅ Added column: {column_name}")
                except Exception as e:
                    logger.error(f"❌ Failed to add column {column_name}: {e}")
            else:
                logger.info(f"✓ Column already exists: {column_name}")

def verify_database():
    """Verify database after migration"""
    inspector = inspect(engine)
    columns = inspector.get_columns('candidates')
    column_names = [col['name'] for col in columns]
    
    logger.info("\n=== Database Verification ===")
    logger.info(f"Total columns: {len(columns)}")
    logger.info(f"Column names: {column_names}")
    
    # Check for required columns
    required = ['job_description', 'knowledge_base_id', 'interview_session_id']
    missing = [col for col in required if col not in column_names]
    
    if missing:
        logger.error(f"❌ Still missing columns: {missing}")
        return False
    else:
        logger.info("✅ All required columns present!")
        return True

if __name__ == "__main__":
    logger.info("Starting database fix...")
    check_and_add_columns()
    
    logger.info("\nVerifying database...")
    if verify_database():
        logger.info("\n✅ Database fix completed successfully!")
    else:
        logger.error("\n❌ Database fix incomplete. Please check manually.")