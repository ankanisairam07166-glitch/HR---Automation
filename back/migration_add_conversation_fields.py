# migration_add_conversation_fields.py
from db import engine, SessionLocal
from sqlalchemy import text

def add_conversation_columns():
    """Add conversation tracking columns"""
    
    columns_to_add = [
        ('interview_qa_pairs', 'TEXT'),
        ('interview_conversation', 'TEXT'),
        ('interview_voice_transcripts', 'TEXT'),
        ('interview_progress_percentage', 'FLOAT DEFAULT 0.0'),
        ('interview_last_activity', 'DATETIME')
    ]
    
    with engine.connect() as conn:
        for column_name, column_type in columns_to_add:
            try:
                conn.execute(text(f"""
                    ALTER TABLE candidates 
                    ADD COLUMN {column_name} {column_type}
                """))
                print(f"Added column: {column_name}")
            except Exception as e:
                print(f"Column {column_name} might already exist: {e}")
        conn.commit()

if __name__ == "__main__":
    add_conversation_columns()
    print("Migration completed!")