# migrate_add_interview_fields.py
# Run this script to add missing columns to your existing database

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
import os
from dotenv import load_dotenv

load_dotenv()

# Get your database URL
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///recruitment.db')

def add_column_if_not_exists(engine, table_name, column_name, column_type):
    """Add a column to a table if it doesn't already exist"""
    try:
        # Check if column exists
        with engine.connect() as conn:
            # For SQLite
            if 'sqlite' in DATABASE_URL:
                result = conn.execute(text(f"PRAGMA table_info({table_name})"))
                columns = [row[1] for row in result]
                if column_name in columns:
                    print(f"✓ Column {column_name} already exists")
                    return
            # For PostgreSQL
            elif 'postgresql' in DATABASE_URL:
                result = conn.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='{table_name}' AND column_name='{column_name}'
                """))
                if result.fetchone():
                    print(f"✓ Column {column_name} already exists")
                    return
            # For MySQL
            elif 'mysql' in DATABASE_URL:
                result = conn.execute(text(f"""
                    SELECT COLUMN_NAME 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = '{table_name}' AND COLUMN_NAME = '{column_name}'
                """))
                if result.fetchone():
                    print(f"✓ Column {column_name} already exists")
                    return
            
            # Add the column
            conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"))
            conn.commit()
            print(f"✅ Added column {column_name}")
            
    except OperationalError as e:
        if "duplicate column" in str(e).lower():
            print(f"✓ Column {column_name} already exists")
        else:
            print(f"❌ Error adding column {column_name}: {e}")

def migrate_database():
    """Add all missing interview-related columns"""
    engine = create_engine(DATABASE_URL)
    
    print("🔄 Starting database migration...")
    
    # Define columns to add with their types
    columns_to_add = [
        # Knowledge Base fields
        ('knowledge_base_id', 'VARCHAR(100)'),
        ('interview_kb_id', 'VARCHAR(100)'),
        ('interview_kb_content', 'TEXT'),
        ('interview_kb_metadata', 'TEXT'),  # JSON stored as TEXT
        
        # Interview session fields
        ('interview_token', 'VARCHAR(100)'),
        ('interview_link', 'VARCHAR(500)'),
        ('interview_session_id', 'VARCHAR(100)'),
        ('interview_time_slot', 'VARCHAR(50)'),
        ('interview_created_at', 'TIMESTAMP'),
        ('interview_started_at', 'TIMESTAMP'),
        ('interview_completed_at', 'TIMESTAMP'),
        ('interview_expires_at', 'TIMESTAMP'),
        ('interview_duration', 'INTEGER'),
        
        # Q&A tracking fields
        ('interview_questions_asked', 'TEXT'),
        ('interview_answers_given', 'TEXT'),
        ('interview_total_questions', 'INTEGER DEFAULT 0'),
        ('interview_answered_questions', 'INTEGER DEFAULT 0'),
        ('interview_transcript', 'TEXT'),
        
        # Recording fields
        ('interview_recording_status', 'VARCHAR(50)'),
        ('interview_recording_file', 'VARCHAR(500)'),
        ('interview_recording_url', 'VARCHAR(500)'),
        ('interview_recording_duration', 'INTEGER'),
        ('interview_recording_size', 'INTEGER'),
        ('interview_recording_format', 'VARCHAR(20)'),
        ('interview_recording_quality', 'VARCHAR(20)'),
        ('recording_path', 'VARCHAR(500)'),
        ('recording_started_at', 'TIMESTAMP'),
        
        # AI Analysis fields
        ('interview_ai_analysis_status', 'VARCHAR(50)'),
        ('interview_ai_score', 'FLOAT'),
        ('interview_ai_technical_score', 'FLOAT'),
        ('interview_ai_communication_score', 'FLOAT'),
        ('interview_ai_problem_solving_score', 'FLOAT'),
        ('interview_ai_cultural_fit_score', 'FLOAT'),
        ('interview_ai_overall_feedback', 'TEXT'),
        ('interview_ai_questions_analysis', 'TEXT'),
        
        # Additional fields
        ('interview_final_status', 'VARCHAR(50)'),
        ('job_description', 'TEXT'),
        ('resume_link', 'VARCHAR(500)'),
        ('resume_text', 'TEXT'),
        ('last_accessed', 'TIMESTAMP'),
        ('reminder_sent', 'BOOLEAN DEFAULT FALSE'),
        ('reminder_sent_date', 'TIMESTAMP'),
        ('company_name', 'VARCHAR(200)'),
        ('interview_auto_score_triggered', 'BOOLEAN DEFAULT FALSE')
        ('interview_analysis_started_at', 'TIMESTAMP'),
        ('interview_analysis_completed_at', 'TIMESTAMP'),
    ]
    
    # Add each column
    for column_name, column_type in columns_to_add:
        add_column_if_not_exists(engine, 'candidates', column_name, column_type)
    
    print("✅ Database migration completed!")

if __name__ == "__main__":
    migrate_database()