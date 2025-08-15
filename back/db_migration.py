# db_migration.py - Run this to add all missing database fields

from sqlalchemy import text
from db import engine, SessionLocal
import logging

logger = logging.getLogger(__name__)

def add_knowledge_base_fields():
    """Add all necessary knowledge base and interview fields to the candidates table"""
    
    # Define all the fields we need for proper KB integration
    kb_fields = [
        # Core Knowledge Base Fields
        ('knowledge_base_id', 'VARCHAR(200)'),
        ('interview_kb_id', 'VARCHAR(200)'),
        ('interview_kb_content', 'TEXT'),
        ('interview_kb_metadata', 'TEXT'),
        
        # Interview Session Management
        ('interview_token', 'VARCHAR(255) UNIQUE'),
        ('interview_session_id', 'VARCHAR(200)'),
        ('interview_created_at', 'DATETIME'),
        ('interview_expires_at', 'DATETIME'),
        ('interview_started_at', 'DATETIME'),
        ('interview_completed_at', 'DATETIME'),
        
        # Company and Job Information
        ('company_name', 'VARCHAR(200)'),
        ('job_description', 'TEXT'),
        
        # Interview Content Tracking
        ('interview_transcript', 'TEXT'),
        ('interview_questions_asked', 'TEXT'),
        ('interview_answers_given', 'TEXT'),
        ('interview_total_questions', 'INTEGER DEFAULT 0'),
        ('interview_answered_questions', 'INTEGER DEFAULT 0'),
        
        # Interview Recording
        ('interview_recording_file', 'VARCHAR(500)'),
        ('interview_recording_url', 'VARCHAR(500)'),
        ('interview_recording_duration', 'INTEGER'),
        ('interview_recording_size', 'INTEGER'),
        ('interview_recording_format', 'VARCHAR(50)'),
        ('interview_recording_status', 'VARCHAR(50)'),
        
        # AI Analysis Results
        ('interview_ai_summary', 'TEXT'),
        ('interview_ai_score', 'FLOAT'),
        ('interview_ai_technical_score', 'FLOAT'),
        ('interview_ai_communication_score', 'FLOAT'),
        ('interview_ai_problem_solving_score', 'FLOAT'),
        ('interview_ai_cultural_fit_score', 'FLOAT'),
        ('interview_ai_overall_feedback', 'TEXT'),
        ('interview_ai_questions_analysis', 'TEXT'),
        ('interview_ai_analysis_status', 'VARCHAR(50)'),
        
        # Interview Management
        ('interview_final_status', 'VARCHAR(50)'),
        ('interview_time_slot', 'VARCHAR(100)'),
        ('interview_email_sent', 'BOOLEAN DEFAULT FALSE'),
        ('interview_email_sent_date', 'DATETIME'),
        ('interview_email_attempts', 'INTEGER DEFAULT 0'),
        
        # Session Metadata
        ('interview_browser_info', 'VARCHAR(500)'),
        ('interview_network_quality', 'VARCHAR(100)'),
        ('interview_technical_issues', 'TEXT'),
        ('interview_session_logs', 'TEXT'),
        ('interview_avatar_used', 'VARCHAR(100)'),
        ('interview_avatar_settings', 'TEXT'),
        
        # Processing Status
        ('interview_processing_status', 'VARCHAR(50)'),
        ('interview_duration', 'INTEGER'),
        ('interview_status', 'VARCHAR(50)'),
        
        # Additional Resume/Candidate Fields
        ('phone', 'VARCHAR(50)'),
        ('source', 'VARCHAR(100)'),
        ('recruiter_notes', 'TEXT'),
        ('tags', 'TEXT'),
        
        # Assessment Enhancement
        ('assessment_id', 'VARCHAR(100)'),
        ('reminder_sent', 'BOOLEAN DEFAULT FALSE'),
        ('reminder_sent_date', 'DATETIME'),
        ('exam_sections_scores', 'TEXT'),
        ('exam_difficulty_level', 'VARCHAR(50)'),
        ('exam_cheating_flag', 'BOOLEAN DEFAULT FALSE'),
        
        # Timestamps
        ('created_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP'),
        ('updated_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP'),
    ]
    
    successful_additions = []
    failed_additions = []
    
    with engine.connect() as conn:
        # Check if we're using SQLite or PostgreSQL
        try:
            result = conn.execute(text("SELECT sqlite_version()"))
            db_type = 'sqlite'
        except:
            db_type = 'postgresql'
        
        for field_name, field_type in kb_fields:
            try:
                # Check if column already exists
                if db_type == 'sqlite':
                    check_query = text("""
                        SELECT COUNT(*) as count 
                        FROM pragma_table_info('candidates') 
                        WHERE name = :column_name
                    """)
                else:
                    check_query = text("""
                        SELECT COUNT(*) as count 
                        FROM information_schema.columns 
                        WHERE table_name = 'candidates' 
                        AND column_name = :column_name
                    """)
                
                result = conn.execute(check_query, {"column_name": field_name})
                exists = result.fetchone()[0] > 0
                
                if not exists:
                    # Add the column
                    if db_type == 'sqlite':
                        alter_query = text(f"ALTER TABLE candidates ADD COLUMN {field_name} {field_type}")
                    else:
                        alter_query = text(f"ALTER TABLE candidates ADD COLUMN {field_name} {field_type}")
                    
                    conn.execute(alter_query)
                    conn.commit()
                    successful_additions.append(field_name)
                    logger.info(f"✅ Added column: {field_name}")
                else:
                    logger.info(f"⏭️ Column already exists: {field_name}")
                    
            except Exception as e:
                failed_additions.append((field_name, str(e)))
                logger.error(f"❌ Failed to add {field_name}: {e}")
    
    # Create indexes for better performance
    create_indexes(engine)
    
    return {
        "successful_additions": successful_additions,
        "failed_additions": failed_additions,
        "total_attempted": len(kb_fields)
    }


def create_indexes(engine):
    """Create indexes for better query performance"""
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_interview_token ON candidates(interview_token)",
        "CREATE INDEX IF NOT EXISTS idx_interview_session_id ON candidates(interview_session_id)",
        "CREATE INDEX IF NOT EXISTS idx_knowledge_base_id ON candidates(knowledge_base_id)",
        "CREATE INDEX IF NOT EXISTS idx_interview_scheduled ON candidates(interview_scheduled)",
        "CREATE INDEX IF NOT EXISTS idx_interview_completed ON candidates(interview_completed_at)",
        "CREATE INDEX IF NOT EXISTS idx_email_job ON candidates(email, job_id)",
        "CREATE INDEX IF NOT EXISTS idx_status ON candidates(status)",
        "CREATE INDEX IF NOT EXISTS idx_final_status ON candidates(final_status)",
        "CREATE INDEX IF NOT EXISTS idx_exam_completed ON candidates(exam_completed)",
        "CREATE INDEX IF NOT EXISTS idx_processed_date ON candidates(processed_date)",
    ]
    
    with engine.connect() as conn:
        for index_sql in indexes:
            try:
                conn.execute(text(index_sql))
                conn.commit()
                logger.info(f"✅ Created index: {index_sql.split()[-3]}")
            except Exception as e:
                # Index might already exist, that's okay
                logger.info(f"⏭️ Index creation skipped (may already exist): {e}")


def verify_database_schema():
    """Verify that all necessary fields exist in the database"""
    
    required_fields = [
        'knowledge_base_id',
        'interview_token',
        'interview_session_id',
        'interview_kb_content',
        'company_name',
        'job_description',
        'interview_created_at',
        'interview_ai_score'
    ]
    
    with engine.connect() as conn:
        try:
            # Check SQLite
            result = conn.execute(text("SELECT sqlite_version()"))
            check_query = text("SELECT name FROM pragma_table_info('candidates')")
            result = conn.execute(check_query)
            existing_columns = [row[0] for row in result.fetchall()]
        except:
            # Check PostgreSQL
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'candidates'
            """)
            result = conn.execute(check_query)
            existing_columns = [row[0] for row in result.fetchall()]
    
    missing_fields = [field for field in required_fields if field not in existing_columns]
    
    return {
        "total_columns": len(existing_columns),
        "required_fields": required_fields,
        "missing_fields": missing_fields,
        "schema_complete": len(missing_fields) == 0,
        "all_columns": sorted(existing_columns)
    }


def run_full_migration():
    """Run complete migration and verification"""
    
    print("🚀 Starting Knowledge Base Database Migration...")
    print("=" * 50)
    
    # Step 1: Add missing fields
    print("📝 Adding missing database fields...")
    migration_result = add_knowledge_base_fields()
    
    print(f"✅ Successfully added: {len(migration_result['successful_additions'])} fields")
    if migration_result['successful_additions']:
        for field in migration_result['successful_additions']:
            print(f"   - {field}")
    
    if migration_result['failed_additions']:
        print(f"❌ Failed to add: {len(migration_result['failed_additions'])} fields")
        for field, error in migration_result['failed_additions']:
            print(f"   - {field}: {error}")
    
    # Step 2: Verify schema
    print("\n🔍 Verifying database schema...")
    verification = verify_database_schema()
    
    print(f"📊 Total columns in candidates table: {verification['total_columns']}")
    
    if verification['schema_complete']:
        print("✅ All required fields are present!")
    else:
        print(f"⚠️ Missing fields: {verification['missing_fields']}")
    
    # Step 3: Test database connection
    print("\n🧪 Testing database operations...")
    try:
        session = SessionLocal()
        from db import Candidate
        
        # Test query
        count = session.query(Candidate).count()
        print(f"✅ Database connection successful. Found {count} candidates.")
        
        # Test that we can access new fields
        first_candidate = session.query(Candidate).first()
        if first_candidate:
            # Test accessing new fields
            kb_id = getattr(first_candidate, 'knowledge_base_id', 'Field accessible')
            token = getattr(first_candidate, 'interview_token', 'Field accessible')
            print(f"✅ New fields accessible on candidate records")
        
        session.close()
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
    
    print("\n🎉 Migration completed!")
    print("=" * 50)
    
    return {
        "migration_result": migration_result,
        "verification": verification,
        "success": verification['schema_complete']
    }


if __name__ == "__main__":
    # Run the migration
    result = run_full_migration()
    
    if result['success']:
        print("\n🚀 Ready for Knowledge Base Integration!")
        print("You can now:")
        print("1. Create HeyGen knowledge bases")
        print("2. Store candidate resume content")
        print("3. Track interview sessions")
        print("4. Record AI analysis results")
    else:
        print("\n⚠️ Migration incomplete. Please check the errors above.")