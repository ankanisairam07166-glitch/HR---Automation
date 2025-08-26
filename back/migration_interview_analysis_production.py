# migration_interview_analysis_production.py
import logging
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError
from db import engine, SessionLocal
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SafeMigration:
    """Production-safe database migration"""
    
    @staticmethod
    def column_exists(table_name: str, column_name: str) -> bool:
        """Check if column exists in table"""
        try:
            inspector = inspect(engine)
            columns = [col['name'] for col in inspector.get_columns(table_name)]
            return column_name in columns
        except Exception as e:
            logger.error(f"Error checking column existence: {e}")
            return False
    
    @staticmethod
    def add_column_safely(table_name: str, column_name: str, column_type: str):
        """Add column with retry logic and proper error handling"""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                if SafeMigration.column_exists(table_name, column_name):
                    logger.info(f"Column {column_name} already exists")
                    return True
                
                with engine.begin() as conn:
                    # Use proper SQL based on database type
                    if 'sqlite' in str(engine.url):
                        sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                    else:  # PostgreSQL, MySQL
                        sql = f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {column_name} {column_type}"
                    
                    conn.execute(text(sql))
                    logger.info(f"✅ Added column {column_name} to {table_name}")
                    return True
                    
            except SQLAlchemyError as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.error(f"Failed to add column {column_name} after {max_retries} attempts")
                    return False
    
    @staticmethod
    def run_production_migration():
        """Run all migrations with transaction safety"""
        migrations = [
            # Core analysis columns
            ('candidates', 'interview_ai_analysis_status', 'VARCHAR(50)'),
            ('candidates', 'interview_analysis_triggered', 'BOOLEAN DEFAULT 0'),
            ('candidates', 'interview_analysis_started_at', 'TIMESTAMP'),
            ('candidates', 'interview_analysis_completed_at', 'TIMESTAMP'),
            ('candidates', 'interview_auto_score_triggered', 'BOOLEAN DEFAULT 0'),
            ('candidates', 'interview_auto_score_completed_at', 'TIMESTAMP'),
            
            # Enhanced tracking
            ('candidates', 'interview_qa_sequence', 'TEXT'),
            ('candidates', 'interview_current_question_id', 'VARCHAR(100)'),
            ('candidates', 'interview_waiting_for_answer', 'BOOLEAN DEFAULT 0'),
            ('candidates', 'interview_connection_quality', 'VARCHAR(50)'),
            ('candidates', 'interview_qa_pairs', 'TEXT'),
            
            # Scoring fields
            ('candidates', 'interview_confidence_score', 'FLOAT'),
            ('candidates', 'interview_scoring_method', 'VARCHAR(50)'),
            ('candidates', 'interview_strengths', 'TEXT'),
            ('candidates', 'interview_weaknesses', 'TEXT'),
            ('candidates', 'interview_recommendations', 'TEXT'),
            
            # Progress tracking
            ('candidates', 'interview_progress_percentage', 'FLOAT DEFAULT 0'),
            ('candidates', 'interview_last_activity', 'TIMESTAMP'),
            ('candidates', 'interview_duration', 'INTEGER'),
            ('candidates', 'interview_conversation', 'TEXT'),
            
            # Final status
            ('candidates', 'interview_final_status', 'VARCHAR(100)'),
            ('candidates', 'interview_ai_overall_feedback', 'TEXT'),
            
            # Additional scores if missing
            ('candidates', 'interview_ai_score', 'FLOAT'),
            ('candidates', 'interview_ai_technical_score', 'FLOAT'),
            ('candidates', 'interview_ai_communication_score', 'FLOAT'),
            ('candidates', 'interview_ai_problem_solving_score', 'FLOAT'),
            ('candidates', 'interview_ai_cultural_fit_score', 'FLOAT'),
        ]
        
        success_count = 0
        failed_columns = []
        
        for table, column, col_type in migrations:
            if SafeMigration.add_column_safely(table, column, col_type):
                success_count += 1
            else:
                failed_columns.append(f"{table}.{column}")
        
        logger.info(f"""
        Migration Summary:
        - Total columns: {len(migrations)}
        - Successful: {success_count}
        - Failed: {len(failed_columns)}
        """)
        
        if failed_columns:
            logger.warning(f"Failed columns: {', '.join(failed_columns)}")
        
        return len(failed_columns) == 0

if __name__ == "__main__":
    print("🚀 Running production-safe interview analysis migration...")
    success = SafeMigration.run_production_migration()
    print("✅ Migration completed!" if success else "⚠️ Migration completed with warnings")