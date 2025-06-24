from celery import Celery
from datetime import datetime, timedelta
from db import Candidate, SessionLocal
from email_utils import send_interview_link_email, send_rejection_email

# Initialize Celery
celery = Celery('hr_tasks', broker='redis://localhost:6379/0')

@celery.task
def process_exam_result_task(candidate_email, score, total_questions, time_taken):

    session = SessionLocal()
    candidate = session.query(Candidate).filter_by(email=candidate_email).first()
    if not candidate:
        session.close()
        return "Candidate not found"

    # Calculate exam percentage
    exam_percentage = (score / total_questions * 100) if total_questions else 0

    # Update candidate exam status
    candidate.exam_completed = True
    candidate.exam_completed_date = datetime.now()
    candidate.exam_score = score
    candidate.exam_total_questions = total_questions
    candidate.exam_time_taken = time_taken
    candidate.exam_percentage = exam_percentage

    # Add feedback logic
    if exam_percentage >= 80:
        candidate.exam_feedback = "Excellent performance! You demonstrated strong technical knowledge and problem-solving skills."
    elif exam_percentage >= 70:
        candidate.exam_feedback = "Good performance! You showed solid understanding of the core concepts."
    elif exam_percentage >= 50:
        candidate.exam_feedback = "Fair performance. Some areas need improvement, particularly in advanced concepts."
    else:
        candidate.exam_feedback = "The assessment revealed gaps in fundamental concepts. Consider strengthening your technical foundation."

    # Send interview link only if candidate passed (exam_percentage >= 70)
    if exam_percentage >= 70:
        # Mark status, schedule interview, send link
        candidate.final_status = 'Interview Scheduled'
        candidate.interview_scheduled = True
        candidate.interview_date = datetime.now() + timedelta(days=3)
        candidate.interview_link = send_interview_link_email(candidate)  # Function should return the link sent
    else:
        candidate.final_status = 'Rejected After Exam'
        candidate.interview_scheduled = False
        candidate.interview_date = None
        candidate.interview_link = None
        send_rejection_email(candidate)

    session.commit()
    session.close()
    return f"Processed candidate {candidate_email}: {candidate.final_status}"
