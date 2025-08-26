#!/usr/bin/env python3
"""
Safe database migration script for interview tracking fields
Run this before starting the application or integrate into your app initialization
"""

import logging
import sys
import os
from datetime import datetime

# Add the app directory to Python path if running standalone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def safe_add_interview_tracking_fields():
    """Safely add interview tracking fields without breaking existing data"""
    
    # Import after path setup
    try:
        from db import engine, SessionLocal, add_column_if_not_exists, Base
        from sqlalchemy import inspect, text
    except ImportError as e:
        print(f"Error importing database modules: {e}")
        print("Make sure you're running this from the correct directory")
        return False
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info("Starting interview tracking fields migration...")
    
    required_fields = [
        # Core tracking fields
        ('candidates', 'interview_session_id', 'VARCHAR(200)', None),
        ('candidates', 'interview_progress_percentage', 'FLOAT', 0.0),
        ('candidates', 'interview_last_activity', 'DATETIME', None),
        
        # Link tracking
        ('candidates', 'link_clicked', 'BOOLEAN', False),
        ('candidates', 'link_clicked_date', 'DATETIME', None),
        ('candidates', 'interview_link_clicked', 'BOOLEAN', False),
        ('candidates', 'interview_link_clicked_at', 'DATETIME', None),
        ('candidates', 'interview_browser_info', 'VARCHAR(500)', None),
        
        # Q&A tracking
        ('candidates', 'interview_total_questions', 'INTEGER', 0),
        ('candidates', 'interview_answered_questions', 'INTEGER', 0),
        ('candidates', 'interview_questions_asked', 'TEXT', '[]'),
        ('candidates', 'interview_answers_given', 'TEXT', '[]'),
        ('candidates', 'interview_qa_pairs', 'TEXT', '[]'),
        ('candidates', 'interview_transcript', 'TEXT', ''),
        ('candidates', 'interview_conversation', 'TEXT', '[]'),
        
        # Status fields
        ('candidates', 'interview_started_at', 'DATETIME', None),
        ('candidates', 'interview_completed_at', 'DATETIME', None),
        ('candidates', 'interview_status', 'VARCHAR(50)', None),
        ('candidates', 'last_accessed', 'DATETIME', None),
        
        # Recording fields (often missing)
        ('candidates', 'interview_recording_status', 'VARCHAR(50)', None),
        ('candidates', 'interview_recording_file', 'VARCHAR(500)', None),
        ('candidates', 'interview_recording_url', 'VARCHAR(500)', None),
        ('candidates', 'interview_recording_duration', 'INTEGER', None),
        
        # Additional tracking
        ('candidates', 'interview_duration', 'INTEGER', None),
        ('candidates', 'interview_ai_analysis_status', 'VARCHAR(50)', 'pending'),
        ('candidates', 'interview_final_status', 'VARCHAR(100)', None),
    ]
    
    success_count = 0
    error_count = 0
    skipped_count = 0
    
    # Create inspector
    inspector = inspect(engine)
    
    # Check if candidates table exists
    if 'candidates' not in inspector.get_table_names():
        logger.error("Candidates table does not exist! Run database initialization first.")
        return False
    
    # Get existing columns
    existing_columns = [col['name'] for col in inspector.get_columns('candidates')]
    logger.info(f"Found {len(existing_columns)} existing columns in candidates table")
    
    for table, column, col_type, default in required_fields:
        try:
            if column not in existing_columns:
                # Build the ALTER TABLE statement based on database type
                db_url = str(engine.url)
                
                if 'sqlite' in db_url:
                    # SQLite syntax
                    if default is not None:
                        if isinstance(default, bool):
                            default_clause = f" DEFAULT {1 if default else 0}"
                        elif isinstance(default, (int, float)):
                            default_clause = f" DEFAULT {default}"
                        elif isinstance(default, str):
                            default_clause = f" DEFAULT '{default}'"
                        else:
                            default_clause = ""
                    else:
                        default_clause = ""
                    
                    alter_sql = f"ALTER TABLE {table} ADD COLUMN {column} {col_type}{default_clause}"
                    
                elif 'postgresql' in db_url or 'postgres' in db_url:
                    # PostgreSQL syntax
                    if default is not None:
                        if isinstance(default, bool):
                            default_clause = f" DEFAULT {default}"
                        elif isinstance(default, (int, float)):
                            default_clause = f" DEFAULT {default}"
                        elif isinstance(default, str):
                            default_clause = f" DEFAULT '{default}'"
                        else:
                            default_clause = ""
                    else:
                        default_clause = ""
                    
                    alter_sql = f"ALTER TABLE {table} ADD COLUMN {column} {col_type}{default_clause}"
                    
                elif 'mysql' in db_url:
                    # MySQL syntax
                    if default is not None:
                        if isinstance(default, bool):
                            default_clause = f" DEFAULT {1 if default else 0}"
                        elif isinstance(default, (int, float)):
                            default_clause = f" DEFAULT {default}"
                        elif isinstance(default, str):
                            default_clause = f" DEFAULT '{default}'"
                        else:
                            default_clause = ""
                    else:
                        default_clause = ""
                    
                    alter_sql = f"ALTER TABLE {table} ADD COLUMN {column} {col_type}{default_clause}"
                    
                else:
                    # Generic SQL
                    alter_sql = f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"
                
                # Execute the ALTER TABLE statement
                with engine.connect() as conn:
                    conn.execute(text(alter_sql))
                    conn.commit()
                
                success_count += 1
                logger.info(f"✅ Added column {table}.{column}")
                
            else:
                skipped_count += 1
                logger.debug(f"⏭️  Column {table}.{column} already exists")
                
        except Exception as e:
            error_count += 1
            logger.error(f"❌ Failed to add column {table}.{column}: {e}")
    
    logger.info(f"""
Migration Summary:
-----------------
✅ Columns added: {success_count}
⏭️  Columns skipped (already exist): {skipped_count}
❌ Errors: {error_count}
Total processed: {len(required_fields)}
""")
    
    # Verify critical fields
    logger.info("Verifying critical fields...")
    critical_fields = [
        'interview_session_id',
        'interview_progress_percentage',
        'interview_questions_asked',
        'interview_answers_given',
        'interview_qa_pairs'
    ]
    
    try:
        session = SessionLocal()
        
        # Build a test query to verify fields exist
        field_list = ', '.join(critical_fields)
        test_query = text(f"SELECT {field_list} FROM candidates LIMIT 1")
        
        result = session.execute(test_query)
        # Just fetch to ensure query works
        result.fetchone()
        
        session.close()
        logger.info("✅ Critical fields verified successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Critical fields verification failed: {e}")
        logger.error("Some interview tracking features may not work properly")
        return False


def verify_migration_status():
    """Check the current migration status"""
    try:
        from db import engine, SessionLocal
        from sqlalchemy import inspect
        
        inspector = inspect(engine)
        existing_columns = [col['name'] for col in inspector.get_columns('candidates')]
        
        required_tracking_fields = [
            'interview_session_id',
            'interview_progress_percentage',
            'interview_questions_asked',
            'interview_answers_given',
            'interview_qa_pairs',
            'interview_transcript',
            'interview_started_at',
            'interview_completed_at'
        ]
        
        missing_fields = [f for f in required_tracking_fields if f not in existing_columns]
        
        if missing_fields:
            print(f"Missing fields: {missing_fields}")
            return False
        else:
            print("All interview tracking fields are present")
            return True
            
    except Exception as e:
        print(f"Error checking migration status: {e}")
        return False


# Corrected main block
if __name__ == "__main__":
    print("Interview Tracking Fields Migration")
    print("==================================")
    
    # Check if we should just verify or actually migrate
    if len(sys.argv) > 1 and sys.argv[1] == '--verify':
        print("\nVerifying migration status...")
        if verify_migration_status():
            print("✅ Migration verification passed")
            sys.exit(0)
        else:
            print("❌ Migration verification failed")
            sys.exit(1)
    else:
        print("\nRunning migration...")
        if safe_add_interview_tracking_fields():
            print("\n✅ Migration completed successfully")
            sys.exit(0)
        else:
            print("\n❌ Migration failed")
            sys.exit(1)