from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
import os
from dotenv import load_dotenv

load_dotenv()

# Get database URL from your config
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///recruitment.db')
engine = create_engine(DATABASE_URL)

def add_knowledge_base_columns():
    """Add knowledge_base_id and related columns to candidates table"""
    
    columns_to_add = [
        ("knowledge_base_id", "VARCHAR(255)"),
        ("interview_kb_id", "VARCHAR(255)"),
        ("interview_kb_content", "TEXT"),
        ("interview_expires_at", "DATETIME"),
        ("interview_session_id", "VARCHAR(255)"),
        ("interview_started_at", "DATETIME"),
        ("interview_completed_at", "DATETIME"),
        ("interview_questions_asked", "TEXT"),
        ("interview_answers_given", "TEXT"),
        ("interview_total_questions", "INTEGER DEFAULT 0"),
        ("interview_answered_questions", "INTEGER DEFAULT 0"),
        ("interview_transcript", "TEXT"),
        ("interview_recording_status", "VARCHAR(50)"),
        ("interview_recording_file", "VARCHAR(255)"),
        ("interview_recording_url", "VARCHAR(500)"),
        ("interview_recording_duration", "INTEGER"),
        ("interview_recording_size", "INTEGER"),
        ("interview_recording_format", "VARCHAR(50)"),
        ("interview_ai_score", "FLOAT"),
        ("interview_ai_technical_score", "FLOAT"),
        ("interview_ai_communication_score", "FLOAT"),
        ("interview_ai_problem_solving_score", "FLOAT"),
        ("interview_ai_cultural_fit_score", "FLOAT"),
        ("interview_ai_overall_feedback", "TEXT"),
        ("interview_ai_questions_analysis", "TEXT"),
        ("interview_ai_analysis_status", "VARCHAR(50)"),
        ("interview_final_status", "VARCHAR(50)"),
        ("last_accessed", "DATETIME"),
        ("company_name", "VARCHAR(255)"),
        ("job_description", "TEXT"),
        ("recording_path", "VARCHAR(500)"),
        ("recording_started_at", "DATETIME"),
        ("interview_duration", "INTEGER")
    ]
    
    with engine.connect() as conn:
        for column_name, column_type in columns_to_add:
            try:
                # Check if column exists
                result = conn.execute(text(f"PRAGMA table_info(candidates)"))
                columns = [row[1] for row in result]
                
                if column_name not in columns:
                    # Add the column
                    conn.execute(text(f"ALTER TABLE candidates ADD COLUMN {column_name} {column_type}"))
                    conn.commit()
                    print(f"✅ Added column: {column_name}")
                else:
                    print(f"⏭️  Column already exists: {column_name}")
                    
            except Exception as e:
                print(f"❌ Error adding column {column_name}: {e}")
    
    print("\n✅ Database migration completed!")

if __name__ == "__main__":
    add_knowledge_base_columns()