# db.py - Production Ready Database Model with all enhancements

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, Index, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool
from datetime import datetime
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

# Define base directory properly
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

Base = declarative_base()

class Candidate(Base):
    __tablename__ = 'candidates'
    
    # Add indexes for better performance
    __table_args__ = (
        Index('idx_job_id', 'job_id'),
        Index('idx_email', 'email'),
        Index('idx_status', 'status'),
        Index('idx_exam_completed', 'exam_completed'),
        Index('idx_processed_date', 'processed_date'),
        UniqueConstraint('email', 'job_id', name='unique_email_job'),
    )

    id = Column(Integer, primary_key=True)

    # Job Information
    job_id = Column(String(100), nullable=False)
    job_title = Column(String(200), nullable=False)

    # Basic Information
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=False)
    linkedin = Column(String(500))
    github = Column(String(500))
    resume_path = Column(String(500))
    phone = Column(String(50))  # Added phone number

    # Resume Processing
    processed_date = Column(DateTime, default=datetime.now, nullable=False)
    ats_score = Column(Float, default=0.0)
    status = Column(String(50))  # Shortlisted/Rejected
    score_reasoning = Column(Text)
    decision_reason = Column(Text)

    # Email Notification
    notification_sent = Column(Boolean, default=False)
    notification_sent_date = Column(DateTime)
    reminder_sent = Column(Boolean, default=False)  # Added for reminder tracking
    reminder_sent_date = Column(DateTime)

    # Assessment Link Tracking
    assessment_invite_link = Column(String(500))
    assessment_id = Column(String(100))  # Added to track specific assessment
    link_clicked = Column(Boolean, default=False)
    link_clicked_date = Column(DateTime)
    
    # Exam Details
    exam_link_sent = Column(Boolean, default=False)
    exam_link_sent_date = Column(DateTime)
    exam_started = Column(Boolean, default=False)
    exam_started_date = Column(DateTime)
    exam_completed = Column(Boolean, default=False)
    exam_completed_date = Column(DateTime)

    # Exam Results
    exam_score = Column(Integer, default=0)
    exam_total_questions = Column(Integer, default=0)
    exam_correct_answers = Column(Integer, default=0)
    exam_percentage = Column(Float, default=0.0)
    exam_time_taken = Column(Integer)  # in minutes
    exam_feedback = Column(Text)
    
    # Detailed exam metrics (new)
    exam_sections_scores = Column(Text)  # JSON string of section-wise scores
    exam_difficulty_level = Column(String(50))  # Easy/Medium/Hard
    exam_cheating_flag = Column(Boolean, default=False)  # If any cheating detected

    # Interview Stage
    interview_scheduled = Column(Boolean, default=False)
    interview_date = Column(DateTime)
    interview_link = Column(String(500))
    interview_type = Column(String(50))  # Technical/HR/Cultural
    interview_feedback = Column(Text)
    interview_score = Column(Float)
    interviewer_name = Column(String(200))

    # Final Status
    final_status = Column(String(100))  # Interview Scheduled/Rejected After Exam/Hired/On Hold
    rejection_reason = Column(Text)  # Specific rejection reason
    
    # Offer Stage (new)
    offer_extended = Column(Boolean, default=False)
    offer_extended_date = Column(DateTime)
    offer_accepted = Column(Boolean, default=False)
    offer_accepted_date = Column(DateTime)
    joining_date = Column(DateTime)
    offered_salary = Column(Float)
    
    # Analytics fields (new)
    source = Column(String(100))  # LinkedIn/Indeed/Referral etc
    recruiter_notes = Column(Text)
    tags = Column(Text)  # JSON array of tags
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # Legacy fields for compatibility
    testlify_link = Column(String(500))  # Alternative name for assessment_invite_link
    attendance_deadline = Column(String(100))
    attended_assessment = Column(Boolean, default=False)
    attended_at = Column(DateTime)
    exam_expired = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<Candidate(id={self.id}, name='{self.name}', email='{self.email}', job_id='{self.job_id}')>"
    
    def to_dict(self):
        """Convert candidate to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'job_id': self.job_id,
            'job_title': self.job_title,
            'status': self.status,
            'ats_score': self.ats_score,
            'final_status': self.final_status,
            'exam_completed': self.exam_completed,
            'exam_percentage': self.exam_percentage,
            'interview_scheduled': self.interview_scheduled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PipelineRun(Base):
    """Track pipeline execution history"""
    __tablename__ = 'pipeline_runs'
    
    id = Column(Integer, primary_key=True)
    job_id = Column(String(100), nullable=False)
    job_title = Column(String(200))
    started_at = Column(DateTime, default=datetime.now, nullable=False)
    completed_at = Column(DateTime)
    status = Column(String(50))  # running/completed/failed
    total_candidates = Column(Integer, default=0)
    shortlisted_count = Column(Integer, default=0)
    error_message = Column(Text)
    steps_completed = Column(Text)  # JSON array of completed steps
    
    # Indexes
    __table_args__ = (
        Index('idx_pipeline_job_id', 'job_id'),
        Index('idx_pipeline_status', 'status'),
    )


class EmailLog(Base):
    """Track all email communications"""
    __tablename__ = 'email_logs'
    
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, nullable=False)
    email_type = Column(String(50))  # assessment_invite/reminder/interview/rejection
    sent_at = Column(DateTime, default=datetime.now, nullable=False)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    email_content = Column(Text)
    
    # Indexes
    __table_args__ = (
        Index('idx_email_candidate', 'candidate_id'),
        Index('idx_email_type', 'email_type'),
    )


# Database configuration with production settings
def get_database_url():
    """Get database URL from environment or use default SQLite"""
    db_url = os.getenv('DATABASE_URL')
    
    if db_url:
        # Handle Heroku-style postgres:// URLs
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        return db_url
    
    # Default to SQLite for development
    db_path = os.path.join(BASE_DIR, "hr_frontend.db")
    return f"sqlite:///{db_path}"


# Create engine with connection pooling for production
engine = create_engine(
    get_database_url(),
    # Connection pool settings for production
    poolclass=QueuePool,
    pool_size=10,
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_pre_ping=True,  # Verify connections before using
    # SQLite specific settings
    connect_args={"check_same_thread": False} if get_database_url().startswith('sqlite') else {},
    # Enable SQL logging in development
    echo=os.getenv('FLASK_ENV') == 'development'
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # Prevent lazy loading issues
)

# Database initialization
def init_db():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Migration helper functions
def add_column_if_not_exists(table_name, column_name, column_type):
    """Add column to existing table if it doesn't exist"""
    from sqlalchemy import inspect, text
    
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    
    if column_name not in columns:
        with engine.connect() as conn:
            if get_database_url().startswith('sqlite'):
                # SQLite ALTER TABLE syntax
                conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"))
            else:
                # PostgreSQL/MySQL syntax
                conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"))
            conn.commit()
        logger.info(f"Added column {column_name} to {table_name}")


def run_migrations():
    """Run database migrations for existing databases"""
    try:
        # Add new columns if they don't exist
        migrations = [
            ('candidates', 'phone', 'VARCHAR(50)'),
            ('candidates', 'assessment_id', 'VARCHAR(100)'),
            ('candidates', 'reminder_sent', 'BOOLEAN DEFAULT FALSE'),
            ('candidates', 'reminder_sent_date', 'DATETIME'),
            ('candidates', 'exam_sections_scores', 'TEXT'),
            ('candidates', 'exam_difficulty_level', 'VARCHAR(50)'),
            ('candidates', 'exam_cheating_flag', 'BOOLEAN DEFAULT FALSE'),
            ('candidates', 'interview_type', 'VARCHAR(50)'),
            ('candidates', 'interview_feedback', 'TEXT'),
            ('candidates', 'interview_score', 'FLOAT'),
            ('candidates', 'interviewer_name', 'VARCHAR(200)'),
            ('candidates', 'rejection_reason', 'TEXT'),
            ('candidates', 'offer_extended', 'BOOLEAN DEFAULT FALSE'),
            ('candidates', 'offer_extended_date', 'DATETIME'),
            ('candidates', 'offer_accepted', 'BOOLEAN DEFAULT FALSE'),
            ('candidates', 'offer_accepted_date', 'DATETIME'),
            ('candidates', 'joining_date', 'DATETIME'),
            ('candidates', 'offered_salary', 'FLOAT'),
            ('candidates', 'source', 'VARCHAR(100)'),
            ('candidates', 'recruiter_notes', 'TEXT'),
            ('candidates', 'tags', 'TEXT'),
            ('candidates', 'created_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP'),
            ('candidates', 'updated_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP'),
        ]
        
        for table, column, col_type in migrations:
            try:
                add_column_if_not_exists(table, column, col_type)
            except Exception as e:
                logger.warning(f"Migration for {table}.{column} failed: {e}")
        
        logger.info("Database migrations completed")
        
    except Exception as e:
        logger.error(f"Migration error: {e}")


# Initialize database on import
if __name__ == "__main__":
    init_db()
    run_migrations()
    print(f"Database initialized at: {get_database_url()}")
