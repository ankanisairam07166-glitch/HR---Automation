# db.py - Updated database model with ALL required fields including job_id and job_title

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()

Base = declarative_base()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
class Candidate(Base):
    __tablename__ = 'candidates'

    id = Column(Integer, primary_key=True)

    # Job Information - ADD THESE MISSING FIELDS
    job_id = Column(String(100))  # The job ID from BambooHR
    job_title = Column(String(200))  # The job title

    # Basic Information
    name = Column(String(200))
    email = Column(String(200), unique=True)
    linkedin = Column(String(500))
    github = Column(String(500))
    resume_path = Column(String(500))

    # Resume Processing
    processed_date = Column(DateTime, default=datetime.now)
    ats_score = Column(Float, default=0.0)
    status = Column(String(50))  # Shortlisted/Rejected
    score_reasoning = Column(Text)
    decision_reason = Column(Text)

    # Email Notification
    notification_sent = Column(Boolean, default=False)

    # Assessment Link Tracking - NEW FIELDS
    assessment_invite_link = Column(String(500))  # The Testlify invite link
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
    exam_total_questions = Column(Integer, default=12)
    exam_correct_answers = Column(Integer, default=0)
    exam_percentage = Column(Float, default=0.0)
    exam_time_taken = Column(Integer)  # in minutes
    exam_feedback = Column(Text)

    # Interview Stage
    interview_scheduled = Column(Boolean, default=False)
    interview_date = Column(DateTime)
    interview_link = Column(String(500))

    # Final Status
    final_status = Column(String(100))  # Interview Scheduled/Rejected After Exam

    # Additional fields for compatibility
    testlify_link = Column(String(500))  # Alternative name for assessment_invite_link
    attendance_deadline = Column(String(100))
    attended_assessment = Column(Boolean, default=False)
    attended_at = Column(DateTime)
    exam_expired = Column(Boolean, default=False)


# Database connection
DB_PATH = os.path.join(BASE_DIR, "hr_frontend.db")
engine = create_engine(
  f"sqlite:///{DB_PATH}",
  connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(engine)