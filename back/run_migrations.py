# run_migrations.py
from db import engine, add_column_if_not_exists, init_db, run_migrations
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_interview_migrations():
    """Apply missing interview-related columns"""
    
    print("🔄 Starting database migrations...")
    
    # Initialize tables if they don't exist
    init_db()
    
    # Run standard migrations
    run_migrations()
    
    # Add specific interview-related columns that might be missing
    interview_columns = [
        ('candidates', 'knowledge_base_id', 'VARCHAR(200)'),
        ('candidates', 'interview_session_id', 'VARCHAR(200)'),
        ('candidates', 'interview_recording_status', 'VARCHAR(50)'),
        ('candidates', 'interview_recording_format', 'VARCHAR(50)'),
        ('candidates', 'interview_questions_asked', 'TEXT'),
        ('candidates', 'interview_answers_given', 'TEXT'),
        ('candidates', 'interview_total_questions', 'INTEGER DEFAULT 0'),
        ('candidates', 'interview_answered_questions', 'INTEGER DEFAULT 0'),
        ('candidates', 'company_name', 'VARCHAR(200)'),
        ('candidates', 'job_description', 'TEXT'),
    ]
    
    for table, column, col_type in interview_columns:
        try:
            add_column_if_not_exists(table, column, col_type)
            print(f"✅ Added/verified column: {table}.{column}")
        except Exception as e:
            print(f"❌ Failed to add {column}: {e}")
    
    print("✅ Migrations completed!")

if __name__ == "__main__":
    apply_interview_migrations()