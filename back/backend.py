

# # from flask import Flask, request, jsonify, redirect, render_template_string, send_from_directory
# # from flask_cors import CORS
# # from datetime import datetime, timedelta
# # from db import Candidate, SessionLocal
# # import threading
# # import asyncio
# # import time
# # import traceback
# # import os
# # import json
# # from sqlalchemy import func, and_
# # import requests
# # import logging
# # from logging.handlers import RotatingFileHandler
# # from functools import wraps
# # from tenacity import retry, stop_after_attempt, wait_exponential
# # import sys

# # # Import your existing modules
# # try:
# #     from scraper import scrape_job
# #     from latest import create_assessment
# #     from test_link import get_invite_link
# #     from clint_recruitment_system import run_recruitment_with_invite_link
# #     from email_util import send_assessment_email, send_assessment_reminder, send_interview_confirmation_email
# # except ImportError as e:
# #     logging.error(f"Critical module import failed: {e}")
# #     raise

# # # Add after existing imports
# # try:
# #     from testlify_results_scraper import scrape_all_pending_assessments,scrape_assessment_results_by_name
# # except ImportError as e:
# #     logging.warning(f"Testlify scraper not available: {e}")

# # # Setup proper logging
# # def setup_logging():
# #     """Configure logging for production"""
# #     if not os.path.exists('logs'):
# #         os.makedirs('logs')
    
# #     # Create formatter
# #     formatter = logging.Formatter(
# #         '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
# #     )
    
# #     # File handler
# #     file_handler = RotatingFileHandler(
# #         'logs/talentflow.log',
# #         maxBytes=10485760,  # 10MB
# #         backupCount=10,
# #         encoding='utf-8'
# #     )
# #     file_handler.setFormatter(formatter)
# #     file_handler.setLevel(logging.INFO)
    
# #     # Console handler  
# #     console_handler = logging.StreamHandler()
# #     console_handler.setLevel(logging.DEBUG)
# #     console_handler.setFormatter(formatter)
    
# #     # Configure root logger
# #     logger = logging.getLogger()
# #     logger.setLevel(logging.INFO)
    
# #     # Clear existing handlers
# #     for handler in logger.handlers[:]:
# #         logger.removeHandler(handler)
    
# #     # Add our handlers
# #     logger.addHandler(file_handler)
    
# #     # Only add console handler in development
# #     if os.getenv('FLASK_ENV') == 'development':
# #         logger.addHandler(console_handler)
    
# #     return logger

# # logger = setup_logging()

# # # Environment validation
# # def validate_environment():
# #     """Validate all required environment variables"""
# #     required_vars = [
# #         'OPENAI_API_KEY',
# #         'BAMBOOHR_API_KEY', 
# #         'BAMBOOHR_SUBDOMAIN',
# #         'SMTP_SERVER',
# #         'SENDER_EMAIL',
# #         'SENDER_PASSWORD',
# #         'COMPANY_NAME'
# #     ]
    
# #     missing = []
# #     for var in required_vars:
# #         if not os.getenv(var):
# #             missing.append(var)
    
# #     if missing:
# #         error_msg = f"Missing required environment variables: {', '.join(missing)}"
# #         logger.error(error_msg)
# #         raise EnvironmentError(error_msg)
    
# #     logger.info("Environment validation passed")

# # # Configuration from environment
# # ASSESSMENT_CONFIG = {
# #     'EXPIRY_HOURS': int(os.getenv('ASSESSMENT_EXPIRY_HOURS', '48')),
# #     'REMINDER_HOURS': int(os.getenv('ASSESSMENT_REMINDER_HOURS', '24')),
# #     'INTERVIEW_DELAY_DAYS': int(os.getenv('INTERVIEW_DELAY_DAYS', '3')),
# #     'ATS_THRESHOLD': float(os.getenv('ATS_THRESHOLD', '70')),
# #     'MAX_RETRIES': int(os.getenv('MAX_RETRIES', '3')),
# #     'RETRY_DELAY': int(os.getenv('RETRY_DELAY', '2'))
# # }

# # # Create Flask app
# # app = Flask(__name__)

# # # CORS Configuration - SINGLE SOURCE OF TRUTH
# # CORS(app, 
# #      origins=["http://localhost:3000", "http://127.0.0.1:3000", "https://yourfrontenddomain.com"],
# #      allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
# #      methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
# #      supports_credentials=True)

# # # Admin notification function
# # def notify_admin(subject, message, error_details=None):
# #     """Send critical notifications to admin"""
# #     try:
# #         admin_email = os.getenv('ADMIN_EMAIL')
# #         if not admin_email:
# #             logger.warning("ADMIN_EMAIL not set, skipping notification")
# #             return
        
# #         from email_util import send_email
        
# #         body_html = f"""
# #         <html>
# #             <body>
# #                 <h2>TalentFlow AI Alert: {subject}</h2>
# #                 <p>{message}</p>
# #                 {f'<pre>{error_details}</pre>' if error_details else ''}
# #                 <p>Time: {datetime.now().isoformat()}</p>
# #             </body>
# #         </html>
# #         """
        
# #         send_email(admin_email, f"[TalentFlow Alert] {subject}", body_html)
        
# #     except Exception as e:
# #         logger.error(f"Failed to send admin notification: {e}")

# # # Rate limiting decorator
# # def rate_limit(max_calls=10, time_window=60):
# #     """Simple rate limiting decorator"""
# #     calls = {}
    
# #     def decorator(func):
# #         @wraps(func)
# #         def wrapper(*args, **kwargs):
# #             now = time.time()
# #             key = request.remote_addr
            
# #             if key not in calls:
# #                 calls[key] = []
            
# #             # Remove old calls
# #             calls[key] = [call_time for call_time in calls[key] if now - call_time < time_window]
            
# #             if len(calls[key]) >= max_calls:
# #                 return jsonify({"error": "Rate limit exceeded"}), 429
            
# #             calls[key].append(now)
# #             return func(*args, **kwargs)
# #         return wrapper
# #     return decorator

# # @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
# # def get_jobs_from_bamboohr():
# #     """Get jobs from BambooHR with retry logic"""
# #     try:
# #         API_KEY = os.getenv("BAMBOOHR_API_KEY")
# #         SUBDOMAIN = os.getenv("BAMBOOHR_SUBDOMAIN")
        
# #         if not API_KEY or not SUBDOMAIN:
# #             raise ValueError("BambooHR credentials not configured")
            
# #         auth = (API_KEY, "x")
# #         headers = {"Accept": "application/json", "Content-Type": "application/json"}
# #         url = f"https://api.bamboohr.com/api/gateway.php/{SUBDOMAIN}/v1/applicant_tracking/jobs/"
        
# #         resp = requests.get(url, auth=auth, headers=headers, timeout=100)
# #         resp.raise_for_status()
        
# #         jobs = resp.json()
# #         open_jobs = []
        
# #         session = SessionLocal()
# #         try:
# #             for job in jobs:
# #                 if job.get("status", {}).get("label", "").lower() == "open":
# #                     # Get candidate count for this job
# #                     candidate_count = session.query(Candidate).filter_by(job_id=str(job["id"])).count()
                    
# #                     open_jobs.append({
# #                         "id": job["id"],
# #                         "title": job.get("title", {}).get("label", ""),
# #                         "location": job.get("location", {}).get("label", ""),
# #                         "department": job.get("department", {}).get("label", ""),
# #                         "postingUrl": job.get("postingUrl", ""),
# #                         "applications": candidate_count,
# #                         "status": "Active",
# #                         "description": job.get("description", "")
# #                     })
# #         finally:
# #             session.close()
        
# #         return jsonify(open_jobs)
        
# #     except requests.exceptions.RequestException as e:
# #         logger.error(f"BambooHR API error: {e}")
# #         notify_admin("BambooHR API Error", f"Failed to fetch jobs: {str(e)}")
# #         return jsonify({"error": "Failed to fetch jobs"}), 503
# #     except Exception as e:
# #         logger.error(f"Unexpected error fetching jobs: {e}")
# #         return jsonify({"error": "Internal server error"}), 500

# # @app.route('/api/jobs', methods=['GET'])
# # @rate_limit(max_calls=30, time_window=60)
# # def api_jobs():
# #     """Enhanced API endpoint to get jobs with candidate counts"""
# #     try:
# #         # Try to get from BambooHR first
# #         try:
# #             return get_jobs_from_bamboohr()
# #         except Exception as bamboo_error:
# #             logger.warning(f"BambooHR unavailable, falling back to database: {bamboo_error}")
        
# #         # Fallback to database
# #         session = SessionLocal()
# #         try:
# #             # Get unique jobs from candidates table
# #             jobs_data = session.query(
# #                 Candidate.job_id,
# #                 Candidate.job_title,
# #                 func.count(Candidate.id).label('applications')
# #             ).filter(
# #                 Candidate.job_id.isnot(None),
# #                 Candidate.job_title.isnot(None)
# #             ).group_by(
# #                 Candidate.job_id, 
# #                 Candidate.job_title
# #             ).all()
            
# #             jobs = []
# #             for job_id, job_title, app_count in jobs_data:
# #                 # Get additional stats
# #                 shortlisted = session.query(Candidate).filter_by(
# #                     job_id=job_id, 
# #                     status='Shortlisted'
# #                 ).count()
                
# #                 completed_assessments = session.query(Candidate).filter_by(
# #                     job_id=job_id, 
# #                     exam_completed=True
# #                 ).count()
                
# #                 jobs.append({
# #                     'id': str(job_id),
# #                     'title': job_title,
# #                     'department': 'Engineering',  # Default
# #                     'location': 'Remote',  # Default
# #                     'applications': app_count,
# #                     'shortlisted': shortlisted,
# #                     'completed_assessments': completed_assessments,
# #                     'status': 'Active',
# #                     'description': f'Job description for {job_title}',
# #                     'postingUrl': ''
# #                 })
            
# #             logger.info(f"Found {len(jobs)} jobs from database")
# #             return jsonify(jobs), 200
            
# #         finally:
# #             session.close()
        
# #     except Exception as e:
# #         logger.error(f"Error in api_jobs: {e}", exc_info=True)
# #         return jsonify({"error": "Failed to fetch jobs", "message": str(e)}), 500

# # @app.route('/api/run_full_pipeline', methods=['POST'])
# # @rate_limit(max_calls=5, time_window=300)  # Max 5 pipeline runs per 5 minutes
# # def api_run_full_pipeline():
# #     """API endpoint to start the full recruitment pipeline"""
# #     try:
# #         data = request.json
# #         job_id = data.get('job_id')
# #         job_title = data.get('job_title')
# #         job_desc = data.get('job_desc', "")
        
# #         logger.info(f"Pipeline request received: job_id={job_id}, job_title={job_title}")
        
# #         if not job_id or not job_title:
# #             return jsonify({"success": False, "message": "job_id and job_title are required"}), 400
        
# #         # Start the pipeline in a separate thread
# #         pipeline_thread = threading.Thread(
# #             target=lambda: run_pipeline_with_monitoring(job_id, job_title, job_desc),
# #             daemon=True,
# #             name=f"pipeline_{job_id}_{int(time.time())}"
# #         )
# #         pipeline_thread.start()
        
# #         # Store thread info for monitoring
# #         if not hasattr(app, 'active_pipelines'):
# #             app.active_pipelines = {}
        
# #         app.active_pipelines[pipeline_thread.name] = {
# #             'job_id': job_id,
# #             'job_title': job_title,
# #             'started_at': datetime.now(),
# #             'thread': pipeline_thread
# #         }
        
# #         return jsonify({
# #             "success": True, 
# #             "message": f"Pipeline started for {job_title}",
# #             "pipeline_id": pipeline_thread.name,
# #             "estimated_time": "5-10 minutes"
# #         }), 200
        
# #     except Exception as e:
# #         logger.error(f"Error in run_full_pipeline: {e}", exc_info=True)
# #         return jsonify({"success": False, "message": str(e)}), 500

# # def run_pipeline_with_monitoring(job_id, job_title, job_desc):
# #     """Wrapper to run pipeline with monitoring and error handling"""
# #     start_time = time.time()
    
# #     try:
# #         logger.info(f"Starting monitored pipeline for job_id={job_id}")
# #         full_recruitment_pipeline(job_id, job_title, job_desc)
        
# #         duration = time.time() - start_time
# #         logger.info(f"Pipeline completed successfully in {duration:.2f} seconds")
        
# #         # Send success notification
# #         notify_admin(
# #             "Pipeline Completed Successfully",
# #             f"Job: {job_title} (ID: {job_id})\nDuration: {duration:.2f} seconds"
# #         )
        
# #     except Exception as e:
# #         duration = time.time() - start_time
# #         error_msg = f"Pipeline failed for job {job_title} (ID: {job_id}) after {duration:.2f} seconds"
# #         logger.error(error_msg, exc_info=True)
        
# #         # Send failure notification
# #         notify_admin(
# #             "Pipeline Failed",
# #             error_msg,
# #             error_details=traceback.format_exc()
# #         )

# # def full_recruitment_pipeline(job_id, job_title, job_desc):
# #     """Run the full recruitment pipeline with proper error handling"""
# #     session = SessionLocal()
# #     pipeline_status = {
# #         'job_id': job_id,
# #         'steps_completed': [],
# #         'errors': []
# #     }
    
# #     try:
# #         logger.info(f"Starting full recruitment pipeline for job_id={job_id}, job_title={job_title}")
        
# #         # STEP 1: Scraping
# #         try:
# #             logger.info(f"STEP 1: Scraping resumes for job_id={job_id}")
# #             asyncio.run(scrape_job(job_id))
# #             pipeline_status['steps_completed'].append('scraping')
# #             logger.info("✅ Scraping completed successfully")
# #         except Exception as e:
# #             error_msg = f"Scraping failed: {str(e)}"
# #             logger.error(error_msg, exc_info=True)
# #             pipeline_status['errors'].append(error_msg)
        
# #         # STEP 2: Create assessment
# #         try:
# #             logger.info(f"STEP 2: Creating assessment for '{job_title}' in Testlify")
# #             create_assessment(job_title, job_desc)
# #             pipeline_status['steps_completed'].append('assessment_creation')
# #             logger.info("✅ Assessment created successfully")
# #         except Exception as e:
# #             error_msg = f"Assessment creation failed: {str(e)}"
# #             logger.error(error_msg, exc_info=True)
# #             pipeline_status['errors'].append(error_msg)
        
# #         # STEP 3: Get invite link
# #         invite_link = None
# #         try:
# #             logger.info(f"STEP 3: Extracting invite link for '{job_title}' from Testlify")
# #             invite_link = get_invite_link(job_title)
# #             if invite_link:
# #                 pipeline_status['steps_completed'].append('invite_link_extraction')
# #                 logger.info(f"✅ Got invite link: {invite_link}")
# #         except Exception as e:
# #             error_msg = f"Invite link extraction failed: {str(e)}"
# #             logger.error(error_msg, exc_info=True)
# #             pipeline_status['errors'].append(error_msg)
        
# #         if not invite_link:
# #             invite_link = f"https://candidate.testlify.com/assessment/{job_id}"
# #             logger.warning(f"Using fallback invite link: {invite_link}")
        
# #         # STEP 4: Run AI screening
# #         try:
# #             logger.info("STEP 4: Running AI-powered screening...")
# #             run_recruitment_with_invite_link(
# #                 job_id=job_id, 
# #                 job_title=job_title, 
# #                 job_desc=job_desc, 
# #                 invite_link=invite_link
# #             )
# #             pipeline_status['steps_completed'].append('ai_screening')
# #             logger.info("✅ AI screening completed successfully")
# #         except Exception as e:
# #             error_msg = f"AI screening failed: {str(e)}"
# #             logger.error(error_msg, exc_info=True)
# #             pipeline_status['errors'].append(error_msg)
# #             raise  # This is critical, so we raise
        
# #         # Log pipeline summary
# #         logger.info(f"Pipeline completed. Steps: {pipeline_status['steps_completed']}, Errors: {len(pipeline_status['errors'])}")
        
# #         if pipeline_status['errors']:
# #             notify_admin(
# #                 "Pipeline Completed with Warnings",
# #                 f"Job: {job_title}\nCompleted steps: {', '.join(pipeline_status['steps_completed'])}\nErrors: {', '.join(pipeline_status['errors'])}"
# #             )
            
# #     except Exception as e:
# #         logger.error(f"Fatal pipeline error: {e}", exc_info=True)
# #         raise
# #     finally:
# #         session.close()
# #         logger.info("🚀 Recruitment pipeline finished")

# # @app.route('/api/candidates', methods=['GET'])
# # @rate_limit(max_calls=60, time_window=60)
# # def api_candidates():
# #     """API endpoint to get candidates with enhanced error handling"""
# #     session = SessionLocal()
# #     try:
# #         job_id = request.args.get('job_id')
# #         status_filter = request.args.get('status')
# #         limit = int(request.args.get('limit', 100))
# #         offset = int(request.args.get('offset', 0))
        
# #         query = session.query(Candidate)
        
# #         if job_id:
# #             query = query.filter_by(job_id=str(job_id))
        
# #         if status_filter:
# #             query = query.filter_by(status=status_filter)
        
# #         # Add pagination
# #         candidates = query.offset(offset).limit(limit).all()
# #         total_count = query.count()
        
# #         logger.info(f"Found {len(candidates)} candidates (total: {total_count}) for job_id={job_id}, status={status_filter}")
        
# #         result = []
# #         for c in candidates:
# #             try:
# #                 # Calculate time remaining for assessment
# #                 time_remaining = None
# #                 link_expired = False
                
# #                 if c.exam_link_sent_date and not c.exam_completed:
# #                     deadline = c.exam_link_sent_date + timedelta(hours=ASSESSMENT_CONFIG['EXPIRY_HOURS'])
# #                     if datetime.now() < deadline:
# #                         time_remaining = (deadline - datetime.now()).total_seconds() / 3600  # hours
# #                     else:
# #                         link_expired = True
                
# #                 candidate_data = {
# #                     "id": c.id,
# #                     "name": c.name or "Unknown",
# #                     "email": c.email or "",
# #                     "job_id": c.job_id,
# #                     "job_title": c.job_title or "Unknown Position",
# #                     "status": c.status,
# #                     "ats_score": float(c.ats_score) if c.ats_score else 0.0,
# #                     "linkedin": c.linkedin,
# #                     "github": c.github,
# #                     "phone": getattr(c, 'phone', None),
# #                     "resume_path": c.resume_path,
# #                     "processed_date": c.processed_date.isoformat() if c.processed_date else None,
# #                     "score_reasoning": c.score_reasoning,
# #                     "decision_reason": getattr(c, 'decision_reason', None),
                    
# #                     # Assessment fields
# #                     "assessment_invite_link": c.assessment_invite_link,
# #                     "assessment_id": getattr(c, 'assessment_id', None),
# #                     "exam_link_sent": bool(c.exam_link_sent),
# #                     "exam_link_sent_date": c.exam_link_sent_date.isoformat() if c.exam_link_sent_date else None,
# #                     "link_clicked": bool(c.link_clicked),
# #                     "link_clicked_date": c.link_clicked_date.isoformat() if c.link_clicked_date else None,
# #                     "exam_started": bool(c.exam_started),
# #                     "exam_started_date": c.exam_started_date.isoformat() if c.exam_started_date else None,
# #                     "exam_completed": bool(c.exam_completed),
# #                     "exam_completed_date": c.exam_completed_date.isoformat() if c.exam_completed_date else None,
# #                     "exam_expired": bool(getattr(c, 'exam_expired', False)) or link_expired,
# #                     "link_expired": link_expired,
# #                     "time_remaining_hours": time_remaining,
                    
# #                     # Exam results
# #                     "exam_score": c.exam_score,
# #                     "exam_total_questions": getattr(c, 'exam_total_questions', None),
# #                     "exam_correct_answers": getattr(c, 'exam_correct_answers', None),
# #                     "exam_percentage": float(c.exam_percentage) if c.exam_percentage else None,
# #                     "exam_time_taken": getattr(c, 'exam_time_taken', None),
# #                     "exam_feedback": getattr(c, 'exam_feedback', None),
# #                     "exam_sections_scores": getattr(c, 'exam_sections_scores', None),
# #                     "exam_difficulty_level": getattr(c, 'exam_difficulty_level', None),
# #                     "exam_cheating_flag": bool(getattr(c, 'exam_cheating_flag', False)),
                    
# #                     # Interview fields
# #                     "interview_scheduled": bool(c.interview_scheduled),
# #                     "interview_date": c.interview_date.isoformat() if c.interview_date else None,
# #                     "interview_link": c.interview_link,
# #                     "interview_type": getattr(c, 'interview_type', None),
# #                     "interview_feedback": getattr(c, 'interview_feedback', None),
# #                     "interview_score": float(getattr(c, 'interview_score', 0)) if getattr(c, 'interview_score', None) else None,
# #                     "interviewer_name": getattr(c, 'interviewer_name', None),
                    
# #                     # Status fields
# #                     "final_status": c.final_status,
# #                     "rejection_reason": getattr(c, 'rejection_reason', None),
# #                     "notification_sent": bool(getattr(c, 'notification_sent', False)),
# #                     "notification_sent_date": getattr(c, 'notification_sent_date', None),
# #                     "reminder_sent": bool(getattr(c, 'reminder_sent', False)),
# #                     "reminder_sent_date": getattr(c, 'reminder_sent_date', None),
                    
# #                     # Legacy fields for backward compatibility
# #                     "testlify_link": getattr(c, 'testlify_link', None) or c.assessment_invite_link,
# #                     "attendance_deadline": getattr(c, 'attendance_deadline', None),
# #                     "attended_assessment": bool(getattr(c, 'attended_assessment', False)) or bool(c.exam_completed),
# #                     "attended_at": getattr(c, 'attended_at', c.exam_completed_date).isoformat() if getattr(c, 'attended_at', c.exam_completed_date) else None
# #                 }
                
# #                 result.append(candidate_data)
                
# #             except Exception as e:
# #                 logger.error(f"Error processing candidate {c.id}: {e}")
# #                 continue
        
# #         return jsonify(result), 200
        
# #     except Exception as e:
# #         logger.error(f"Error in api_candidates: {e}", exc_info=True)
# #         return jsonify({"error": "Failed to fetch candidates", "message": str(e)}), 500
# #     finally:
# #         session.close()

# # @app.route('/api/send_assessment', methods=['POST'])
# # @rate_limit(max_calls=20, time_window=60)
# # def api_send_assessment():
# #     """Send assessment link to a specific candidate"""
# #     try:
# #         data = request.json
# #         candidate_id = data.get('candidate_id')
        
# #         if not candidate_id:
# #             return jsonify({"success": False, "message": "candidate_id is required"}), 400
        
# #         session = SessionLocal()
# #         try:
# #             candidate = session.query(Candidate).filter_by(id=candidate_id).first()
# #             if not candidate:
# #                 return jsonify({"success": False, "message": "Candidate not found"}), 404
            
# #             # Update candidate with assessment sent info
# #             candidate.exam_link_sent = True
# #             candidate.exam_link_sent_date = datetime.now()
            
# #             # Generate assessment link if not exists
# #             if not candidate.assessment_invite_link:
# #                 candidate.assessment_invite_link = f"https://app.testlify.com/assessment/{getattr(candidate, 'assessment_id', candidate.job_id)}"
            
# #             # Send email with assessment link
# #             try:
# #                 send_assessment_email(candidate)
# #                 logger.info(f"Assessment link sent to {candidate.email}")
# #             except Exception as e:
# #                 logger.warning(f"Failed to send assessment email to {candidate.email}: {e}")
            
# #             session.commit()
            
# #             return jsonify({
# #                 "success": True,
# #                 "message": f"Assessment link sent to {candidate.name}",
# #                 "candidate": {
# #                     "id": candidate.id,
# #                     "name": candidate.name,
# #                     "email": candidate.email,
# #                     "assessment_link": candidate.assessment_invite_link
# #                 }
# #             }), 200
            
# #         finally:
# #             session.close()
        
# #     except Exception as e:
# #         logger.error(f"Error in send_assessment: {e}", exc_info=True)
# #         return jsonify({"success": False, "message": str(e)}), 500

# # @app.route('/api/send_reminders', methods=['POST'])
# # @rate_limit(max_calls=10, time_window=60)
# # def api_send_reminders():
# #     """Send reminder emails to specific candidates"""
# #     try:
# #         data = request.json
# #         candidate_ids = data.get('candidate_ids', [])
        
# #         if not candidate_ids:
# #             return jsonify({"success": False, "message": "candidate_ids array is required"}), 400
        
# #         session = SessionLocal()
# #         try:
# #             reminded_count = 0
# #             failed_count = 0
            
# #             for candidate_id in candidate_ids:
# #                 try:
# #                     candidate = session.query(Candidate).filter_by(id=candidate_id).first()
# #                     if not candidate:
# #                         failed_count += 1
# #                         continue
                    
# #                     # Check if candidate is eligible for reminder
# #                     if not candidate.exam_link_sent or candidate.exam_completed:
# #                         failed_count += 1
# #                         continue
                    
# #                     # Send reminder email
# #                     try:
# #                         # Calculate hours remaining
# #                         hours_remaining = 24  # Default
# #                         if candidate.exam_link_sent_date:
# #                             deadline = candidate.exam_link_sent_date + timedelta(hours=48)
# #                             hours_remaining = max(0, int((deadline - datetime.now()).total_seconds() / 3600))
                        
# #                         send_assessment_reminder(candidate, hours_remaining)
                        
# #                         # Update reminder tracking
# #                         candidate.reminder_sent = True
# #                         candidate.reminder_sent_date = datetime.now()
                        
# #                         reminded_count += 1
                        
# #                     except Exception as e:
# #                         logger.error(f"Failed to send reminder to {candidate.email}: {e}")
# #                         failed_count += 1
                
# #                 except Exception as e:
# #                     logger.error(f"Error processing candidate {candidate_id}: {e}")
# #                     failed_count += 1
            
# #             session.commit()
            
# #             return jsonify({
# #                 "success": True,
# #                 "reminded_count": reminded_count,
# #                 "failed_count": failed_count,
# #                 "message": f"Sent reminders to {reminded_count} candidates. {failed_count} failed."
# #             }), 200
            
# #         finally:
# #             session.close()
        
# #     except Exception as e:
# #         logger.error(f"Error in send_reminders: {e}", exc_info=True)
# #         return jsonify({"success": False, "message": str(e)}), 500

# # @app.route('/api/schedule-interview', methods=['POST'])
# # @rate_limit(max_calls=10, time_window=60)
# # def api_schedule_interview():
# #     """Schedule an interview for a candidate"""
# #     try:
# #         data = request.json
# #         candidate_id = data.get('candidate_id')
# #         email = data.get('email')
# #         interview_date = data.get('date')
# #         time_slot = data.get('time_slot')
        
# #         if not candidate_id and not email:
# #             return jsonify({"success": False, "message": "candidate_id or email is required"}), 400
        
# #         session = SessionLocal()
# #         try:
# #             # Find candidate
# #             if candidate_id:
# #                 candidate = session.query(Candidate).filter_by(id=candidate_id).first()
# #             else:
# #                 candidate = session.query(Candidate).filter_by(email=email).first()
            
# #             if not candidate:
# #                 return jsonify({"success": False, "message": "Candidate not found"}), 404
            
# #             # Parse interview date
# #             if isinstance(interview_date, str):
# #                 interview_datetime = datetime.fromisoformat(interview_date.replace('Z', '+00:00'))
# #             else:
# #                 interview_datetime = datetime.now() + timedelta(days=3)
            
# #             # Update candidate
# #             candidate.interview_scheduled = True
# #             candidate.interview_date = interview_datetime
# #             candidate.final_status = 'Interview Scheduled'
            
# #             # Generate Google Meet link
# #             meeting_link = f"https://meet.google.com/lookup/generated-meeting-id-{candidate.id}"
# #             candidate.interview_link = meeting_link
            
# #             # Send interview confirmation email
# #             try:
# #                 send_interview_confirmation_email(candidate, interview_datetime, meeting_link)
# #             except Exception as e:
# #                 logger.warning(f"Failed to send interview email to {candidate.email}: {e}")
            
# #             session.commit()
            
# #             return jsonify({
# #                 "success": True,
# #                 "message": f"Interview scheduled for {candidate.name}",
# #                 "meeting_link": meeting_link,
# #                 "interview_date": interview_datetime.isoformat(),
# #                 "candidate": {
# #                     "id": candidate.id,
# #                     "name": candidate.name,
# #                     "email": candidate.email
# #                 }
# #             }), 200
            
# #         finally:
# #             session.close()
        
# #     except Exception as e:
# #         logger.error(f"Error in schedule_interview: {e}", exc_info=True)
# #         return jsonify({"success": False, "message": str(e)}), 500

# # @app.route('/api/recruitment-stats', methods=['GET'])
# # @rate_limit(max_calls=20, time_window=60)
# # def api_recruitment_stats():
# #     """Get recruitment statistics for charts"""
# #     session = SessionLocal()
# #     try:
# #         stats = []
# #         current_date = datetime.now()
        
# #         # Get last 6 months of data
# #         for i in range(6):
# #             try:
# #                 month_date = current_date - timedelta(days=30*i)
# #                 month_name = month_date.strftime('%b')
                
# #                 # Calculate month boundaries
# #                 month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
# #                 if month_start.month == 12:
# #                     month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(seconds=1)
# #                 else:
# #                     month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(seconds=1)
                
# #                 # Get statistics for this month
# #                 applications = session.query(Candidate).filter(
# #                     and_(
# #                         Candidate.processed_date >= month_start,
# #                         Candidate.processed_date <= month_end
# #                     )
# #                 ).count()
                
# #                 interviews = session.query(Candidate).filter(
# #                     and_(
# #                         Candidate.interview_scheduled == True,
# #                         Candidate.interview_date >= month_start,
# #                         Candidate.interview_date <= month_end
# #                     )
# #                 ).count()
                
# #                 hires = session.query(Candidate).filter(
# #                     and_(
# #                         Candidate.final_status == "Hired",
# #                         Candidate.processed_date >= month_start,
# #                         Candidate.processed_date <= month_end
# #                     )
# #                 ).count()
                
# #                 stats.append({
# #                     "month": month_name,
# #                     "applications": applications,
# #                     "interviews": interviews,
# #                     "hires": hires
# #                 })
                
# #             except Exception as e:
# #                 logger.error(f"Error calculating stats for month {i}: {e}")
# #                 stats.append({
# #                     "month": (current_date - timedelta(days=30*i)).strftime('%b'),
# #                     "applications": 0,
# #                     "interviews": 0,
# #                     "hires": 0
# #                 })
        
# #         # Reverse to get chronological order
# #         stats.reverse()
        
# #         logger.info(f"Generated recruitment stats for {len(stats)} months")
# #         return jsonify(stats), 200
        
# #     except Exception as e:
# #         logger.error(f"Error in api_recruitment_stats: {e}", exc_info=True)
# #         return jsonify({"error": "Failed to get statistics", "message": str(e)}), 500
# #     finally:
# #         session.close()

# # @app.route('/health', methods=['GET'])
# # def health_check():
# #     """Enhanced health check endpoint"""
# #     health_status = {
# #         "status": "healthy",
# #         "timestamp": datetime.now().isoformat(),
# #         "version": "2.0.0",
# #         "checks": {}
# #     }
    
# #     # Check database
# #     try:
# #         session = SessionLocal()
# #         session.execute("SELECT 1")
# #         session.close()
# #         health_status["checks"]["database"] = "healthy"
# #     except Exception as e:
# #         health_status["checks"]["database"] = f"unhealthy: {str(e)}"
# #         health_status["status"] = "degraded"
    
# #     # Check external services
# #     try:
# #         API_KEY = os.getenv("BAMBOOHR_API_KEY")
# #         if API_KEY:
# #             health_status["checks"]["bamboohr"] = "configured"
# #         else:
# #             health_status["checks"]["bamboohr"] = "not configured"
# #     except:
# #         health_status["checks"]["bamboohr"] = "unknown"
    
# #     return jsonify(health_status), 200 if health_status["status"] == "healthy" else 503

# # # Error handlers
# # @app.errorhandler(404)
# # def not_found(error):
# #     return jsonify({"error": "Endpoint not found"}), 404

# # @app.errorhandler(500)
# # def internal_error(error):
# #     logger.error(f"Internal server error: {error}")
# #     return jsonify({"error": "Internal server error"}), 500

# # @app.errorhandler(429)
# # def rate_limit_exceeded(error):
# #     return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429

# # # Startup validation
# # with app.app_context():
# #     try:
# #         validate_environment()
# #         logger.info("TalentFlow AI Backend started successfully")
# #     except Exception as e:
# #         logger.error(f"Startup failed: {e}")
# #         print(f"❌ Startup failed: {e}")
# #         print("Please check your environment variables in .env file")
# #         sys.exit(1)

# # if __name__ == "__main__":
# #     print("🚀 Starting TalentFlow AI Backend (Production Mode)...")
# #     print("📍 Server running at http://127.0.0.1:5000")
# #     print("📍 Logging to: logs/talentflow.log")
    
# #     # In production, use a proper WSGI server like Gunicorn
# #     if os.getenv('FLASK_ENV') == 'production':
# #         print("⚠️  Warning: Use a production WSGI server like Gunicorn in production!")
    
# #     app.run(
# #         host='0.0.0.0',
# #         port=5000,
# #         debug=os.getenv('FLASK_ENV') == 'development',
# #         use_reloader=False
# #     )
# # backend.py - Production Ready Version with Fixed CORS

# from flask import Flask, request, jsonify, redirect, render_template_string, send_from_directory
# from flask_cors import CORS
# from datetime import datetime, timedelta
# from db import Candidate, SessionLocal
# import threading
# import asyncio
# import time
# import traceback
# import os
# import json
# from sqlalchemy import func, and_
# import requests
# import logging
# from logging.handlers import RotatingFileHandler
# from functools import wraps
# from tenacity import retry, stop_after_attempt, wait_exponential
# import sys

# # Import your existing modules
# try:
#     from scraper import scrape_job
#     from latest import create_programming_assessment
#     from test_link import get_invite_link
#     from clint_recruitment_system import run_recruitment_with_invite_link
#     from email_util import send_assessment_email, send_assessment_reminder, send_interview_confirmation_email, send_interview_link_email, send_rejection_email
# except ImportError as e:
#     logging.error(f"Critical module import failed: {e}")
#     raise

# # Add after existing imports
# try:
#     from testlify_results_scraper import scrape_all_pending_assessments, scrape_assessment_results_by_name
# except ImportError as e:
#     logging.warning(f"Testlify scraper not available: {e}")

# # Setup proper logging
# def setup_logging():
#     """Configure logging for production"""
#     if not os.path.exists('logs'):
#         os.makedirs('logs')
    
#     # Create formatter
#     formatter = logging.Formatter(
#         '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
#     )
    
#     # File handler
#     file_handler = RotatingFileHandler(
#         'logs/talentflow.log',
#         maxBytes=10485760,  # 10MB
#         backupCount=10,
#         encoding='utf-8'
#     )
#     file_handler.setFormatter(formatter)
#     file_handler.setLevel(logging.INFO)
    
#     # Console handler  
#     console_handler = logging.StreamHandler()
#     console_handler.setLevel(logging.DEBUG)
#     console_handler.setFormatter(formatter)
    
#     # Configure root logger
#     logger = logging.getLogger()
#     logger.setLevel(logging.INFO)
    
#     # Clear existing handlers
#     for handler in logger.handlers[:]:
#         logger.removeHandler(handler)
    
#     # Add our handlers
#     logger.addHandler(file_handler)
    
#     # Only add console handler in development
#     if os.getenv('FLASK_ENV') == 'development':
#         logger.addHandler(console_handler)
    
#     return logger

# logger = setup_logging()

# # Environment validation
# def validate_environment():
#     """Validate all required environment variables"""
#     required_vars = [
#         'OPENAI_API_KEY',
#         'BAMBOOHR_API_KEY', 
#         'BAMBOOHR_SUBDOMAIN',
#         'SMTP_SERVER',
#         'SENDER_EMAIL',
#         'SENDER_PASSWORD',
#         'COMPANY_NAME'
#     ]
    
#     missing = []
#     for var in required_vars:
#         if not os.getenv(var):
#             missing.append(var)
    
#     if missing:
#         error_msg = f"Missing required environment variables: {', '.join(missing)}"
#         logger.error(error_msg)
#         raise EnvironmentError(error_msg)
    
#     logger.info("Environment validation passed")

# # Configuration from environment
# ASSESSMENT_CONFIG = {
#     'EXPIRY_HOURS': int(os.getenv('ASSESSMENT_EXPIRY_HOURS', '48')),
#     'REMINDER_HOURS': int(os.getenv('ASSESSMENT_REMINDER_HOURS', '24')),
#     'INTERVIEW_DELAY_DAYS': int(os.getenv('INTERVIEW_DELAY_DAYS', '3')),
#     'ATS_THRESHOLD': float(os.getenv('ATS_THRESHOLD', '70')),
#     'MAX_RETRIES': int(os.getenv('MAX_RETRIES', '3')),
#     'RETRY_DELAY': int(os.getenv('RETRY_DELAY', '2'))
# }

# # Create Flask app
# app = Flask(__name__)

# # Enhanced CORS Configuration
# CORS(app, 
#      origins=["http://localhost:3000", "http://127.0.0.1:3000", "https://yourfrontenddomain.com"],
#      allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept"],
#      methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
#      supports_credentials=True,
#      expose_headers=["Content-Type", "Authorization"])

# # Add request logging for debugging
# @app.before_request
# def log_request_info():
#     """Log incoming requests for debugging"""
#     if request.endpoint and (request.endpoint.startswith('api_') or 'api' in request.path):
#         logger.info(f"🌐 {request.method} {request.path} from {request.remote_addr}")
#         if request.method == 'OPTIONS':
#             logger.info(f"🔧 CORS preflight for {request.path}")
#         if request.method in ['POST', 'PUT'] and request.is_json:
#             logger.info(f"📦 Request data keys: {list(request.json.keys()) if request.json else 'None'}")

# # Admin notification function
# def notify_admin(subject, message, error_details=None):
#     """Send critical notifications to admin"""
#     try:
#         admin_email = os.getenv('ADMIN_EMAIL')
#         if not admin_email:
#             logger.warning("ADMIN_EMAIL not set, skipping notification")
#             return
        
#         from email_util import send_email
        
#         body_html = f"""
#         <html>
#             <body>
#                 <h2>TalentFlow AI Alert: {subject}</h2>
#                 <p>{message}</p>
#                 {f'<pre>{error_details}</pre>' if error_details else ''}
#                 <p>Time: {datetime.now().isoformat()}</p>
#             </body>
#         </html>
#         """
        
#         send_email(admin_email, f"[TalentFlow Alert] {subject}", body_html)
        
#     except Exception as e:
#         logger.error(f"Failed to send admin notification: {e}")

# # Rate limiting decorator
# def rate_limit(max_calls=10, time_window=60):
#     """Simple rate limiting decorator that excludes OPTIONS requests"""
#     calls = {}
    
#     def decorator(func):
#         @wraps(func)
#         def wrapper(*args, **kwargs):
#             # Skip rate limiting for OPTIONS requests (CORS preflight)
#             if request.method == 'OPTIONS':
#                 return func(*args, **kwargs)
            
#             now = time.time()
#             key = request.remote_addr
            
#             if key not in calls:
#                 calls[key] = []
            
#             # Remove old calls
#             calls[key] = [call_time for call_time in calls[key] if now - call_time < time_window]
            
#             if len(calls[key]) >= max_calls:
#                 return jsonify({"error": "Rate limit exceeded"}), 429
            
#             calls[key].append(now)
#             return func(*args, **kwargs)
#         return wrapper
#     return decorator

# @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
# def get_jobs_from_bamboohr():
#     """Get jobs from BambooHR with retry logic"""
#     try:
#         API_KEY = os.getenv("BAMBOOHR_API_KEY")
#         SUBDOMAIN = os.getenv("BAMBOOHR_SUBDOMAIN")
        
#         if not API_KEY or not SUBDOMAIN:
#             raise ValueError("BambooHR credentials not configured")
            
#         auth = (API_KEY, "x")
#         headers = {"Accept": "application/json", "Content-Type": "application/json"}
#         url = f"https://api.bamboohr.com/api/gateway.php/{SUBDOMAIN}/v1/applicant_tracking/jobs/"
        
#         resp = requests.get(url, auth=auth, headers=headers, timeout=100)
#         resp.raise_for_status()
        
#         jobs = resp.json()
#         open_jobs = []
        
#         session = SessionLocal()
#         try:
#             for job in jobs:
#                 if job.get("status", {}).get("label", "").lower() == "open":
#                     # Get candidate count for this job
#                     candidate_count = session.query(Candidate).filter_by(job_id=str(job["id"])).count()
                    
#                     open_jobs.append({
#                         "id": job["id"],
#                         "title": job.get("title", {}).get("label", ""),
#                         "location": job.get("location", {}).get("label", ""),
#                         "department": job.get("department", {}).get("label", ""),
#                         "postingUrl": job.get("postingUrl", ""),
#                         "applications": candidate_count,
#                         "status": "Active",
#                         "description": job.get("description", "")
#                     })
#         finally:
#             session.close()
        
#         return jsonify(open_jobs)
        
#     except requests.exceptions.RequestException as e:
#         logger.error(f"BambooHR API error: {e}")
#         notify_admin("BambooHR API Error", f"Failed to fetch jobs: {str(e)}")
#         return jsonify({"error": "Failed to fetch jobs"}), 503
#     except Exception as e:
#         logger.error(f"Unexpected error fetching jobs: {e}")
#         return jsonify({"error": "Internal server error"}), 500

# @app.route('/api/jobs', methods=['GET'])
# @rate_limit(max_calls=30, time_window=60)
# def api_jobs():
#     """Enhanced API endpoint to get jobs with candidate counts"""
#     try:
#         # Try to get from BambooHR first
#         try:
#             return get_jobs_from_bamboohr()
#         except Exception as bamboo_error:
#             logger.warning(f"BambooHR unavailable, falling back to database: {bamboo_error}")
        
#         # Fallback to database
#         session = SessionLocal()
#         try:
#             # Get unique jobs from candidates table
#             jobs_data = session.query(
#                 Candidate.job_id,
#                 Candidate.job_title,
#                 func.count(Candidate.id).label('applications')
#             ).filter(
#                 Candidate.job_id.isnot(None),
#                 Candidate.job_title.isnot(None)
#             ).group_by(
#                 Candidate.job_id, 
#                 Candidate.job_title
#             ).all()
            
#             jobs = []
#             for job_id, job_title, app_count in jobs_data:
#                 # Get additional stats
#                 shortlisted = session.query(Candidate).filter_by(
#                     job_id=job_id, 
#                     status='Shortlisted'
#                 ).count()
                
#                 completed_assessments = session.query(Candidate).filter_by(
#                     job_id=job_id, 
#                     exam_completed=True
#                 ).count()
                
#                 jobs.append({
#                     'id': str(job_id),
#                     'title': job_title,
#                     'department': 'Engineering',  # Default
#                     'location': 'Remote',  # Default
#                     'applications': app_count,
#                     'shortlisted': shortlisted,
#                     'completed_assessments': completed_assessments,
#                     'status': 'Active',
#                     'description': f'Job description for {job_title}',
#                     'postingUrl': ''
#                 })
            
#             logger.info(f"Found {len(jobs)} jobs from database")
#             return jsonify(jobs), 200
            
#         finally:
#             session.close()
        
#     except Exception as e:
#         logger.error(f"Error in api_jobs: {e}", exc_info=True)
#         return jsonify({"error": "Failed to fetch jobs", "message": str(e)}), 500

# @app.route('/api/run_full_pipeline', methods=['POST'])
# @rate_limit(max_calls=5, time_window=300)  # Max 5 pipeline runs per 5 minutes
# def api_run_full_pipeline():
#     """API endpoint to start the full recruitment pipeline"""
#     try:
#         data = request.json
#         job_id = data.get('job_id')
#         job_title = data.get('job_title')
#         job_desc = data.get('job_desc', "")
        
#         logger.info(f"Pipeline request received: job_id={job_id}, job_title={job_title}")
        
#         if not job_id or not job_title:
#             return jsonify({"success": False, "message": "job_id and job_title are required"}), 400
        
#         # Start the pipeline in a separate thread
#         pipeline_thread = threading.Thread(
#             target=lambda: run_pipeline_with_monitoring(job_id, job_title, job_desc),
#             daemon=True,
#             name=f"pipeline_{job_id}_{int(time.time())}"
#         )
#         pipeline_thread.start()
        
#         # Store thread info for monitoring
#         if not hasattr(app, 'active_pipelines'):
#             app.active_pipelines = {}
        
#         app.active_pipelines[pipeline_thread.name] = {
#             'job_id': job_id,
#             'job_title': job_title,
#             'started_at': datetime.now(),
#             'thread': pipeline_thread
#         }
        
#         return jsonify({
#             "success": True, 
#             "message": f"Pipeline started for {job_title}",
#             "pipeline_id": pipeline_thread.name,
#             "estimated_time": "5-10 minutes"
#         }), 200
        
#     except Exception as e:
#         logger.error(f"Error in run_full_pipeline: {e}", exc_info=True)
#         return jsonify({"success": False, "message": str(e)}), 500

# def run_pipeline_with_monitoring(job_id, job_title, job_desc):
#     """Wrapper to run pipeline with monitoring and error handling"""
#     start_time = time.time()
    
#     try:
#         logger.info(f"Starting monitored pipeline for job_id={job_id}")
#         full_recruitment_pipeline(job_id, job_title, job_desc)
        
#         duration = time.time() - start_time
#         logger.info(f"Pipeline completed successfully in {duration:.2f} seconds")
        
#         # Send success notification
#         notify_admin(
#             "Pipeline Completed Successfully",
#             f"Job: {job_title} (ID: {job_id})\nDuration: {duration:.2f} seconds"
#         )
        
#     except Exception as e:
#         duration = time.time() - start_time
#         error_msg = f"Pipeline failed for job {job_title} (ID: {job_id}) after {duration:.2f} seconds"
#         logger.error(error_msg, exc_info=True)
        
#         # Send failure notification
#         notify_admin(
#             "Pipeline Failed",
#             error_msg,
#             error_details=traceback.format_exc()
#         )

# def full_recruitment_pipeline(job_id, job_title, job_desc):
#     """Run the full recruitment pipeline with proper error handling"""
#     session = SessionLocal()
#     pipeline_status = {
#         'job_id': job_id,
#         'steps_completed': [],
#         'errors': []
#     }
    
#     try:
#         logger.info(f"Starting full recruitment pipeline for job_id={job_id}, job_title={job_title}")
        
#         # STEP 1: Scraping
#         try:
#             logger.info(f"STEP 1: Scraping resumes for job_id={job_id}")
#             asyncio.run(scrape_job(job_id))
#             pipeline_status['steps_completed'].append('scraping')
#             logger.info("✅ Scraping completed successfully")
#         except Exception as e:
#             error_msg = f"Scraping failed: {str(e)}"
#             logger.error(error_msg, exc_info=True)
#             pipeline_status['errors'].append(error_msg)
        
#         # STEP 2: Create assessment
#         try:
#             logger.info(f"STEP 2: Creating assessment for '{job_title}' in Testlify")
#             create_programming_assessment(job_title, job_desc)
#             pipeline_status['steps_completed'].append('assessment_creation')
#             logger.info("✅ Assessment created successfully")
#         except Exception as e:
#             error_msg = f"Assessment creation failed: {str(e)}"
#             logger.error(error_msg, exc_info=True)
#             pipeline_status['errors'].append(error_msg)
        
#         # STEP 3: Get invite link
#         invite_link = None
#         try:
#             logger.info(f"STEP 3: Extracting invite link for '{job_title}' from Testlify")
#             invite_link = get_invite_link(job_title)
#             if invite_link:
#                 pipeline_status['steps_completed'].append('invite_link_extraction')
#                 logger.info(f"✅ Got invite link: {invite_link}")
#         except Exception as e:
#             error_msg = f"Invite link extraction failed: {str(e)}"
#             logger.error(error_msg, exc_info=True)
#             pipeline_status['errors'].append(error_msg)
        
#         if not invite_link:
#             invite_link = f"https://candidate.testlify.com/assessment/{job_id}"
#             logger.warning(f"Using fallback invite link: {invite_link}")
        
#         # STEP 4: Run AI screening
#         try:
#             logger.info("STEP 4: Running AI-powered screening...")
#             run_recruitment_with_invite_link(
#                 job_id=job_id, 
#                 job_title=job_title, 
#                 job_desc=job_desc, 
#                 invite_link=invite_link
#             )
#             pipeline_status['steps_completed'].append('ai_screening')
#             logger.info("✅ AI screening completed successfully")
#         except Exception as e:
#             error_msg = f"AI screening failed: {str(e)}"
#             logger.error(error_msg, exc_info=True)
#             pipeline_status['errors'].append(error_msg)
#             raise  # This is critical, so we raise
        
#         # Log pipeline summary
#         logger.info(f"Pipeline completed. Steps: {pipeline_status['steps_completed']}, Errors: {len(pipeline_status['errors'])}")
        
#         if pipeline_status['errors']:
#             notify_admin(
#                 "Pipeline Completed with Warnings",
#                 f"Job: {job_title}\nCompleted steps: {', '.join(pipeline_status['steps_completed'])}\nErrors: {', '.join(pipeline_status['errors'])}"
#             )
            
#     except Exception as e:
#         logger.error(f"Fatal pipeline error: {e}", exc_info=True)
#         raise
#     finally:
#         session.close()
#         logger.info("🚀 Recruitment pipeline finished")

# @app.route('/api/candidates', methods=['GET'])
# @rate_limit(max_calls=60, time_window=60)
# def api_candidates():
#     """API endpoint to get candidates with enhanced error handling"""
#     session = SessionLocal()
#     try:
#         job_id = request.args.get('job_id')
#         status_filter = request.args.get('status')
#         limit = int(request.args.get('limit', 100))
#         offset = int(request.args.get('offset', 0))
        
#         query = session.query(Candidate)
        
#         if job_id:
#             query = query.filter_by(job_id=str(job_id))
        
#         if status_filter:
#             query = query.filter_by(status=status_filter)
        
#         # Add pagination
#         candidates = query.offset(offset).limit(limit).all()
#         total_count = query.count()
        
#         logger.info(f"Found {len(candidates)} candidates (total: {total_count}) for job_id={job_id}, status={status_filter}")
        
#         result = []
#         for c in candidates:
#             try:
#                 # Calculate time remaining for assessment
#                 time_remaining = None
#                 link_expired = False
                
#                 if c.exam_link_sent_date and not c.exam_completed:
#                     deadline = c.exam_link_sent_date + timedelta(hours=ASSESSMENT_CONFIG['EXPIRY_HOURS'])
#                     if datetime.now() < deadline:
#                         time_remaining = (deadline - datetime.now()).total_seconds() / 3600  # hours
#                     else:
#                         link_expired = True
                
#                 candidate_data = {
#                     "id": c.id,
#                     "name": c.name or "Unknown",
#                     "email": c.email or "",
#                     "job_id": c.job_id,
#                     "job_title": c.job_title or "Unknown Position",
#                     "status": c.status,
#                     "ats_score": float(c.ats_score) if c.ats_score else 0.0,
#                     "linkedin": c.linkedin,
#                     "github": c.github,
#                     "phone": getattr(c, 'phone', None),
#                     "resume_path": c.resume_path,
#                     "processed_date": c.processed_date.isoformat() if c.processed_date else None,
#                     "score_reasoning": c.score_reasoning,
#                     "decision_reason": getattr(c, 'decision_reason', None),
                    
#                     # Assessment fields
#                     "assessment_invite_link": c.assessment_invite_link,
#                     "assessment_id": getattr(c, 'assessment_id', None),
#                     "exam_link_sent": bool(c.exam_link_sent),
#                     "exam_link_sent_date": c.exam_link_sent_date.isoformat() if c.exam_link_sent_date else None,
#                     "link_clicked": bool(c.link_clicked),
#                     "link_clicked_date": c.link_clicked_date.isoformat() if c.link_clicked_date else None,
#                     "exam_started": bool(c.exam_started),
#                     "exam_started_date": c.exam_started_date.isoformat() if c.exam_started_date else None,
#                     "exam_completed": bool(c.exam_completed),
#                     "exam_completed_date": c.exam_completed_date.isoformat() if c.exam_completed_date else None,
#                     "exam_expired": bool(getattr(c, 'exam_expired', False)) or link_expired,
#                     "link_expired": link_expired,
#                     "time_remaining_hours": time_remaining,
                    
#                     # Exam results
#                     "exam_score": c.exam_score,
#                     "exam_total_questions": getattr(c, 'exam_total_questions', None),
#                     "exam_correct_answers": getattr(c, 'exam_correct_answers', None),
#                     "exam_percentage": float(c.exam_percentage) if c.exam_percentage else None,
#                     "exam_time_taken": getattr(c, 'exam_time_taken', None),
#                     "exam_feedback": getattr(c, 'exam_feedback', None),
#                     "exam_sections_scores": getattr(c, 'exam_sections_scores', None),
#                     "exam_difficulty_level": getattr(c, 'exam_difficulty_level', None),
#                     "exam_cheating_flag": bool(getattr(c, 'exam_cheating_flag', False)),
                    
#                     # Interview fields
#                     "interview_scheduled": bool(c.interview_scheduled),
#                     "interview_date": c.interview_date.isoformat() if c.interview_date else None,
#                     "interview_link": c.interview_link,
#                     "interview_type": getattr(c, 'interview_type', None),
#                     "interview_feedback": getattr(c, 'interview_feedback', None),
#                     "interview_score": float(getattr(c, 'interview_score', 0)) if getattr(c, 'interview_score', None) else None,
#                     "interviewer_name": getattr(c, 'interviewer_name', None),
                    
#                     # Status fields
#                     "final_status": c.final_status,
#                     "rejection_reason": getattr(c, 'rejection_reason', None),
#                     "notification_sent": bool(getattr(c, 'notification_sent', False)),
#                     "notification_sent_date": getattr(c, 'notification_sent_date', None),
#                     "reminder_sent": bool(getattr(c, 'reminder_sent', False)),
#                     "reminder_sent_date": getattr(c, 'reminder_sent_date', None),
                    
#                     # Legacy fields for backward compatibility
#                     "testlify_link": getattr(c, 'testlify_link', None) or c.assessment_invite_link,
#                     "attendance_deadline": getattr(c, 'attendance_deadline', None),
#                     "attended_assessment": bool(getattr(c, 'attended_assessment', False)) or bool(c.exam_completed),
#                     "attended_at": getattr(c, 'attended_at', c.exam_completed_date).isoformat() if getattr(c, 'attended_at', c.exam_completed_date) else None
#                 }
                
#                 result.append(candidate_data)
                
#             except Exception as e:
#                 logger.error(f"Error processing candidate {c.id}: {e}")
#                 continue
        
#         return jsonify(result), 200
        
#     except Exception as e:
#         logger.error(f"Error in api_candidates: {e}", exc_info=True)
#         return jsonify({"error": "Failed to fetch candidates", "message": str(e)}), 500
#     finally:
#         session.close()

# @app.route('/api/send_assessment', methods=['POST'])
# @rate_limit(max_calls=20, time_window=60)
# def api_send_assessment():
#     """Send assessment link to a specific candidate"""
#     try:
#         data = request.json
#         candidate_id = data.get('candidate_id')
        
#         if not candidate_id:
#             return jsonify({"success": False, "message": "candidate_id is required"}), 400
        
#         session = SessionLocal()
#         try:
#             candidate = session.query(Candidate).filter_by(id=candidate_id).first()
#             if not candidate:
#                 return jsonify({"success": False, "message": "Candidate not found"}), 404
            
#             # Update candidate with assessment sent info
#             candidate.exam_link_sent = True
#             candidate.exam_link_sent_date = datetime.now()
            
#             # Generate assessment link if not exists
#             if not candidate.assessment_invite_link:
#                 candidate.assessment_invite_link = f"https://app.testlify.com/assessment/{getattr(candidate, 'assessment_id', candidate.job_id)}"
            
#             # Send email with assessment link
#             try:
#                 send_assessment_email(candidate)
#                 logger.info(f"Assessment link sent to {candidate.email}")
#             except Exception as e:
#                 logger.warning(f"Failed to send assessment email to {candidate.email}: {e}")
            
#             session.commit()
            
#             return jsonify({
#                 "success": True,
#                 "message": f"Assessment link sent to {candidate.name}",
#                 "candidate": {
#                     "id": candidate.id,
#                     "name": candidate.name,
#                     "email": candidate.email,
#                     "assessment_link": candidate.assessment_invite_link
#                 }
#             }), 200
            
#         finally:
#             session.close()
        
#     except Exception as e:
#         logger.error(f"Error in send_assessment: {e}", exc_info=True)
#         return jsonify({"success": False, "message": str(e)}), 500

# @app.route('/api/send_reminders', methods=['POST'])
# @rate_limit(max_calls=10, time_window=60)
# def api_send_reminders():
#     """Send reminder emails to specific candidates"""
#     try:
#         data = request.json
#         candidate_ids = data.get('candidate_ids', [])
        
#         if not candidate_ids:
#             return jsonify({"success": False, "message": "candidate_ids array is required"}), 400
        
#         session = SessionLocal()
#         try:
#             reminded_count = 0
#             failed_count = 0
            
#             for candidate_id in candidate_ids:
#                 try:
#                     candidate = session.query(Candidate).filter_by(id=candidate_id).first()
#                     if not candidate:
#                         failed_count += 1
#                         continue
                    
#                     # Check if candidate is eligible for reminder
#                     if not candidate.exam_link_sent or candidate.exam_completed:
#                         failed_count += 1
#                         continue
                    
#                     # Send reminder email
#                     try:
#                         # Calculate hours remaining
#                         hours_remaining = 24  # Default
#                         if candidate.exam_link_sent_date:
#                             deadline = candidate.exam_link_sent_date + timedelta(hours=48)
#                             hours_remaining = max(0, int((deadline - datetime.now()).total_seconds() / 3600))
                        
#                         send_assessment_reminder(candidate, hours_remaining)
                        
#                         # Update reminder tracking
#                         candidate.reminder_sent = True
#                         candidate.reminder_sent_date = datetime.now()
                        
#                         reminded_count += 1
                        
#                     except Exception as e:
#                         logger.error(f"Failed to send reminder to {candidate.email}: {e}")
#                         failed_count += 1
                
#                 except Exception as e:
#                     logger.error(f"Error processing candidate {candidate_id}: {e}")
#                     failed_count += 1
            
#             session.commit()
            
#             return jsonify({
#                 "success": True,
#                 "reminded_count": reminded_count,
#                 "failed_count": failed_count,
#                 "message": f"Sent reminders to {reminded_count} candidates. {failed_count} failed."
#             }), 200
            
#         finally:
#             session.close()
        
#     except Exception as e:
#         logger.error(f"Error in send_reminders: {e}", exc_info=True)
#         return jsonify({"success": False, "message": str(e)}), 500

# @app.route('/api/schedule-interview', methods=['POST'])
# @rate_limit(max_calls=10, time_window=60)
# def api_schedule_interview():
#     """Schedule an interview for a candidate"""
#     try:
#         data = request.json
#         candidate_id = data.get('candidate_id')
#         email = data.get('email')
#         interview_date = data.get('date')
#         time_slot = data.get('time_slot')
        
#         if not candidate_id and not email:
#             return jsonify({"success": False, "message": "candidate_id or email is required"}), 400
        
#         session = SessionLocal()
#         try:
#             # Find candidate
#             if candidate_id:
#                 candidate = session.query(Candidate).filter_by(id=candidate_id).first()
#             else:
#                 candidate = session.query(Candidate).filter_by(email=email).first()
            
#             if not candidate:
#                 return jsonify({"success": False, "message": "Candidate not found"}), 404
            
#             # Parse interview date
#             if isinstance(interview_date, str):
#                 interview_datetime = datetime.fromisoformat(interview_date.replace('Z', '+00:00'))
#             else:
#                 interview_datetime = datetime.now() + timedelta(days=3)
            
#             # Update candidate
#             candidate.interview_scheduled = True
#             candidate.interview_date = interview_datetime
#             candidate.final_status = 'Interview Scheduled'
            
#             # Generate Google Meet link
#             meeting_link = f"https://meet.google.com/lookup/generated-meeting-id-{candidate.id}"
#             candidate.interview_link = meeting_link
            
#             # Send interview confirmation email
#             try:
#                 send_interview_confirmation_email(candidate, interview_datetime, meeting_link)
#             except Exception as e:
#                 logger.warning(f"Failed to send interview email to {candidate.email}: {e}")
            
#             session.commit()
            
#             return jsonify({
#                 "success": True,
#                 "message": f"Interview scheduled for {candidate.name}",
#                 "meeting_link": meeting_link,
#                 "interview_date": interview_datetime.isoformat(),
#                 "candidate": {
#                     "id": candidate.id,
#                     "name": candidate.name,
#                     "email": candidate.email
#                 }
#             }), 200
            
#         finally:
#             session.close()
        
#     except Exception as e:
#         logger.error(f"Error in schedule_interview: {e}", exc_info=True)
#         return jsonify({"success": False, "message": str(e)}), 500

# @app.route('/api/recruitment-stats', methods=['GET'])
# @rate_limit(max_calls=20, time_window=60)
# def api_recruitment_stats():
#     """Get recruitment statistics for charts"""
#     session = SessionLocal()
#     try:
#         stats = []
#         current_date = datetime.now()
        
#         # Get last 6 months of data
#         for i in range(6):
#             try:
#                 month_date = current_date - timedelta(days=30*i)
#                 month_name = month_date.strftime('%b')
                
#                 # Calculate month boundaries
#                 month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
#                 if month_start.month == 12:
#                     month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(seconds=1)
#                 else:
#                     month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(seconds=1)
                
#                 # Get statistics for this month
#                 applications = session.query(Candidate).filter(
#                     and_(
#                         Candidate.processed_date >= month_start,
#                         Candidate.processed_date <= month_end
#                     )
#                 ).count()
                
#                 interviews = session.query(Candidate).filter(
#                     and_(
#                         Candidate.interview_scheduled == True,
#                         Candidate.interview_date >= month_start,
#                         Candidate.interview_date <= month_end
#                     )
#                 ).count()
                
#                 hires = session.query(Candidate).filter(
#                     and_(
#                         Candidate.final_status == "Hired",
#                         Candidate.processed_date >= month_start,
#                         Candidate.processed_date <= month_end
#                     )
#                 ).count()
                
#                 stats.append({
#                     "month": month_name,
#                     "applications": applications,
#                     "interviews": interviews,
#                     "hires": hires
#                 })
                
#             except Exception as e:
#                 logger.error(f"Error calculating stats for month {i}: {e}")
#                 stats.append({
#                     "month": (current_date - timedelta(days=30*i)).strftime('%b'),
#                     "applications": 0,
#                     "interviews": 0,
#                     "hires": 0
#                 })
        
#         # Reverse to get chronological order
#         stats.reverse()
        
#         logger.info(f"Generated recruitment stats for {len(stats)} months")
#         return jsonify(stats), 200
        
#     except Exception as e:
#         logger.error(f"Error in api_recruitment_stats: {e}", exc_info=True)
#         return jsonify({"error": "Failed to get statistics", "message": str(e)}), 500
#     finally:
#         session.close()

# @app.route('/api/scrape_assessment_results', methods=['POST', 'OPTIONS'])
# @rate_limit(max_calls=3, time_window=300)  # Max 3 scraping requests per 5 minutes
# def api_scrape_assessment_results():
#     """API endpoint to scrape assessment results for a specific assessment"""
#     if request.method == 'OPTIONS':
#         return '', 200
        
#     try:
#         data = request.json
#         assessment_name = data.get('assessment_name')
        
#         if not assessment_name:
#             return jsonify({"success": False, "message": "assessment_name is required"}), 400
        
#         logger.info(f"Starting results scraping for assessment: {assessment_name}")
        
#         # Start scraping in a separate thread
#         scraping_thread = threading.Thread(
#             target=lambda: run_scraping_with_monitoring(assessment_name),
#             daemon=True,
#             name=f"scraping_{assessment_name.replace(' ', '_')}_{int(time.time())}"
#         )
#         scraping_thread.start()
        
#         return jsonify({
#             "success": True,
#             "message": f"Started scraping results for '{assessment_name}'",
#             "estimated_time": "2-5 minutes"
#         }), 200
        
#     except Exception as e:
#         logger.error(f"Error in scrape_assessment_results: {e}", exc_info=True)
#         return jsonify({"success": False, "message": str(e)}), 500


# @app.route('/api/scrape_all_pending_results', methods=['POST', 'OPTIONS'])
# @rate_limit(max_calls=1, time_window=600)  # Max 1 bulk scraping per 10 minutes
# def api_scrape_all_pending_results():
#     """API endpoint to scrape all pending assessment results"""
#     if request.method == 'OPTIONS':
#         return '', 200
        
#     try:
#         logger.info("Starting bulk results scraping for all pending assessments")
        
#         # Start bulk scraping in a separate thread
#         scraping_thread = threading.Thread(
#             target=lambda: run_bulk_scraping_with_monitoring(),
#             daemon=True,
#             name=f"bulk_scraping_{int(time.time())}"
#         )
#         scraping_thread.start()
        
#         return jsonify({
#             "success": True,
#             "message": "Started bulk scraping for all pending assessments",
#             "estimated_time": "5-15 minutes"
#         }), 200
        
#     except Exception as e:
#         logger.error(f"Error in scrape_all_pending_results: {e}", exc_info=True)
#         return jsonify({"success": False, "message": str(e)}), 500


# @app.route('/api/manual_process_candidate', methods=['POST', 'OPTIONS'])
# @rate_limit(max_calls=10, time_window=60)
# def api_manual_process_candidate():
#     """Manually process a candidate's exam result"""
#     if request.method == 'OPTIONS':
#         return '', 200
        
#     try:
#         data = request.json
#         candidate_email = data.get('candidate_email')
#         exam_score = data.get('exam_score')
#         total_questions = data.get('total_questions', 100)
#         time_taken = data.get('time_taken', 0)
        
#         if not candidate_email:
#             return jsonify({"success": False, "message": "candidate_email is required"}), 400
        
#         if exam_score is None:
#             return jsonify({"success": False, "message": "exam_score is required"}), 400
        
#         session = SessionLocal()
#         try:
#             candidate = session.query(Candidate).filter_by(email=candidate_email).first()
#             if not candidate:
#                 return jsonify({"success": False, "message": "Candidate not found"}), 404
            
#             # Calculate percentage
#             exam_percentage = (exam_score / total_questions * 100) if total_questions else 0
            
#             # Update candidate
#             candidate.exam_completed = True
#             candidate.exam_completed_date = datetime.now()
#             candidate.exam_score = exam_score
#             candidate.exam_total_questions = total_questions
#             candidate.exam_time_taken = time_taken
#             candidate.exam_percentage = exam_percentage
            
#             # Add detailed feedback based on performance
#             if exam_percentage >= 90:
#                 candidate.exam_feedback = "Outstanding performance! Exceptional technical knowledge and problem-solving skills demonstrated."
#             elif exam_percentage >= 80:
#                 candidate.exam_feedback = "Excellent performance! Strong technical competence and understanding shown."
#             elif exam_percentage >= 70:
#                 candidate.exam_feedback = "Good performance! Solid understanding of key concepts with room for growth."
#             elif exam_percentage >= 60:
#                 candidate.exam_feedback = "Fair performance. Shows promise with some areas needing improvement."
#             else:
#                 candidate.exam_feedback = "Performance indicates opportunities for growth in fundamental concepts."
            
#             # Process next steps based on score
#             if exam_percentage >= 70:
#                 candidate.final_status = 'Interview Scheduled'
#                 candidate.interview_scheduled = True
#                 candidate.interview_date = datetime.now() + timedelta(days=ASSESSMENT_CONFIG['INTERVIEW_DELAY_DAYS'])
                
#                 # Send interview email
#                 try:
#                     interview_link = send_interview_link_email(candidate)
#                     candidate.interview_link = interview_link
#                     message = f"Interview scheduled for {candidate.name}. Score: {exam_percentage:.1f}%"
#                 except Exception as e:
#                     logger.error(f"Failed to send interview email: {e}")
#                     message = f"Result processed for {candidate.name} (Score: {exam_percentage:.1f}%) but email failed"
                
#             else:
#                 candidate.final_status = 'Rejected After Exam'
                
#                 # Send rejection email
#                 try:
#                     send_rejection_email(candidate)
#                     message = f"Rejection email sent to {candidate.name}. Score: {exam_percentage:.1f}%"
#                 except Exception as e:
#                     logger.error(f"Failed to send rejection email: {e}")
#                     message = f"Result processed for {candidate.name} (Score: {exam_percentage:.1f}%) but email failed"
            
#             session.commit()
            
#             return jsonify({
#                 "success": True,
#                 "message": message,
#                 "candidate": {
#                     "name": candidate.name,
#                     "email": candidate.email,
#                     "exam_percentage": exam_percentage,
#                     "final_status": candidate.final_status,
#                     "interview_scheduled": candidate.interview_scheduled
#                 }
#             }), 200
            
#         finally:
#             session.close()
        
#     except Exception as e:
#         logger.error(f"Error in manual_process_candidate: {e}", exc_info=True)
#         return jsonify({"success": False, "message": str(e)}), 500


# @app.route('/api/assessment_metrics/<job_id>', methods=['GET'])
# def api_assessment_metrics(job_id):
#     """Get detailed assessment metrics for a specific job"""
#     session = SessionLocal()
#     try:
#         candidates = session.query(Candidate).filter_by(job_id=str(job_id)).all()
        
#         # Calculate detailed metrics
#         total_candidates = len(candidates)
#         assessments_sent = len([c for c in candidates if c.exam_link_sent])
#         assessments_started = len([c for c in candidates if c.exam_started])
#         assessments_completed = len([c for c in candidates if c.exam_completed])
#         assessments_passed = len([c for c in candidates if c.exam_completed and c.exam_percentage and c.exam_percentage >= 70])
#         assessments_pending = len([c for c in candidates if c.exam_link_sent and not c.exam_completed])
        
#         # Calculate average scores and times
#         completed_candidates = [c for c in candidates if c.exam_completed and c.exam_percentage is not None]
#         avg_score = sum(c.exam_percentage for c in completed_candidates) / len(completed_candidates) if completed_candidates else 0
#         avg_time = sum(getattr(c, 'exam_time_taken', 0) or 0 for c in completed_candidates) / len(completed_candidates) if completed_candidates else 0
        
#         # Calculate conversion rates
#         send_to_start_rate = (assessments_started / assessments_sent * 100) if assessments_sent > 0 else 0
#         start_to_complete_rate = (assessments_completed / assessments_started * 100) if assessments_started > 0 else 0
#         completion_rate = (assessments_completed / assessments_sent * 100) if assessments_sent > 0 else 0
#         pass_rate = (assessments_passed / assessments_completed * 100) if assessments_completed > 0 else 0
        
#         # Recent activity (last 7 days)
#         seven_days_ago = datetime.now() - timedelta(days=7)
#         recent_completed = len([c for c in candidates if c.exam_completed_date and c.exam_completed_date >= seven_days_ago])
#         recent_started = len([c for c in candidates if c.exam_started_date and c.exam_started_date >= seven_days_ago])
        
#         return jsonify({
#             "success": True,
#             "metrics": {
#                 "total_candidates": total_candidates,
#                 "assessments_sent": assessments_sent,
#                 "assessments_started": assessments_started,
#                 "assessments_completed": assessments_completed,
#                 "assessments_passed": assessments_passed,
#                 "assessments_pending": assessments_pending,
#                 "avg_score": round(avg_score, 1),
#                 "avg_time_minutes": round(avg_time, 1),
#                 "send_to_start_rate": round(send_to_start_rate, 1),
#                 "start_to_complete_rate": round(start_to_complete_rate, 1),
#                 "completion_rate": round(completion_rate, 1),
#                 "pass_rate": round(pass_rate, 1),
#                 "recent_activity": {
#                     "completed_last_7_days": recent_completed,
#                     "started_last_7_days": recent_started
#                 }
#             }
#         }), 200
        
#     except Exception as e:
#         logger.error(f"Error in assessment_metrics: {e}", exc_info=True)
#         return jsonify({"success": False, "message": str(e)}), 500
#     finally:
#         session.close()


# @app.route('/api/routes', methods=['GET'])
# def list_routes():
#     """Debug endpoint to list all available routes"""
#     routes = []
#     for rule in app.url_map.iter_rules():
#         if rule.endpoint != 'static':
#             routes.append({
#                 'endpoint': rule.endpoint,
#                 'methods': list(rule.methods),
#                 'rule': str(rule)
#             })
#     return jsonify({
#         "total_routes": len(routes),
#         "routes": sorted(routes, key=lambda x: x['rule'])
#     }), 200


# @app.route('/api/test-cors', methods=['GET', 'POST', 'OPTIONS'])
# def test_cors():
#     """Test endpoint for CORS debugging"""
#     if request.method == 'OPTIONS':
#         return '', 200
    
#     return jsonify({
#         "message": "CORS is working!",
#         "method": request.method,
#         "timestamp": datetime.now().isoformat(),
#         "headers": dict(request.headers)
#     }), 200


# @app.route('/api/scraping_status', methods=['GET'])
# def api_scraping_status():
#     """Get status of running scraping operations"""
#     try:
#         # Get active scraping threads
#         active_threads = []
#         for thread in threading.enumerate():
#             if thread.name.startswith(('scraping_', 'bulk_scraping_')):
#                 thread_info = {
#                     "name": thread.name,
#                     "is_alive": thread.is_alive(),
#                     "daemon": thread.daemon
#                 }
#                 active_threads.append(thread_info)
        
#         return jsonify({
#             "success": True,
#             "active_operations": len(active_threads),
#             "operations": active_threads
#         }), 200
        
#     except Exception as e:
#         logger.error(f"Error in scraping_status: {e}", exc_info=True)
#         return jsonify({"success": False, "message": str(e)}), 500


# def run_scraping_with_monitoring(assessment_name: str):
#     """Wrapper to run scraping with monitoring and error handling"""
#     start_time = time.time()
    
#     try:
#         logger.info(f"Starting monitored scraping for assessment: {assessment_name}")
        
#         # Import and run the scraping function
#         try:
#             from testlify_results_scraper import scrape_assessment_results_by_name
#         except ImportError as e:
#             logger.error(f"Failed to import scraper: {e}")
#             notify_admin(
#                 "Scraper Import Error",
#                 f"Could not import results scraper: {str(e)}. Please ensure testlify_results_scraper.py is available."
#             )
#             return
        
#         # Run the async scraping function
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
#         try:
#             results = loop.run_until_complete(scrape_assessment_results_by_name(assessment_name))
#         finally:
#             loop.close()
        
#         duration = time.time() - start_time
#         logger.info(f"Scraping completed successfully in {duration:.2f} seconds. Found {len(results)} candidates.")
        
#         # Send success notification
#         notify_admin(
#             "Assessment Results Scraping Completed",
#             f"Assessment: {assessment_name}\nCandidates processed: {len(results)}\nDuration: {duration:.2f} seconds"
#         )
        
#     except Exception as e:
#         duration = time.time() - start_time
#         error_msg = f"Scraping failed for assessment '{assessment_name}' after {duration:.2f} seconds"
#         logger.error(error_msg, exc_info=True)
        
#         # Send failure notification
#         notify_admin(
#             "Assessment Results Scraping Failed",
#             error_msg,
#             error_details=traceback.format_exc()
#         )


# def run_bulk_scraping_with_monitoring():
#     """Wrapper to run bulk scraping with monitoring"""
#     start_time = time.time()
    
#     try:
#         logger.info("Starting bulk scraping for all pending assessments")
        
#         # Import and run the bulk scraping function
#         try:
#             from testlify_results_scraper import scrape_all_pending_assessments
#         except ImportError as e:
#             logger.error(f"Failed to import scraper: {e}")
#             notify_admin(
#                 "Scraper Import Error",
#                 f"Could not import results scraper: {str(e)}. Please ensure testlify_results_scraper.py is available."
#             )
#             return
        
#         # Run the async scraping function
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
#         try:
#             results_summary = loop.run_until_complete(scrape_all_pending_assessments())
#         finally:
#             loop.close()
        
#         duration = time.time() - start_time
#         total_candidates = sum(results_summary.values()) if isinstance(results_summary, dict) else 0
        
#         logger.info(f"Bulk scraping completed in {duration:.2f} seconds. Processed {len(results_summary)} assessments, {total_candidates} candidates.")
        
#         # Send success notification
#         if isinstance(results_summary, dict):
#             summary_text = "\n".join([f"- {assessment}: {count} candidates" for assessment, count in results_summary.items()])
#         else:
#             summary_text = f"Processed {total_candidates} total candidates"
            
#         notify_admin(
#             "Bulk Assessment Results Scraping Completed",
#             f"Assessments processed: {len(results_summary) if isinstance(results_summary, dict) else 'Unknown'}\nTotal candidates: {total_candidates}\nDuration: {duration:.2f} seconds\n\nBreakdown:\n{summary_text}"
#         )
        
#     except Exception as e:
#         duration = time.time() - start_time
#         error_msg = f"Bulk scraping failed after {duration:.2f} seconds"
#         logger.error(error_msg, exc_info=True)
        
#         # Send failure notification
#         notify_admin(
#             "Bulk Assessment Results Scraping Failed",
#             error_msg,
#             error_details=traceback.format_exc()
#         )


# @app.route('/health', methods=['GET'])
# def health_check():
#     """Enhanced health check endpoint"""
#     health_status = {
#         "status": "healthy",
#         "timestamp": datetime.now().isoformat(),
#         "version": "2.0.0",
#         "checks": {}
#     }
    
#     # Check database
#     try:
#         session = SessionLocal()
#         session.execute("SELECT 1")
#         session.close()
#         health_status["checks"]["database"] = "healthy"
#     except Exception as e:
#         health_status["checks"]["database"] = f"unhealthy: {str(e)}"
#         health_status["status"] = "degraded"
    
#     # Check external services
#     try:
#         API_KEY = os.getenv("BAMBOOHR_API_KEY")
#         if API_KEY:
#             health_status["checks"]["bamboohr"] = "configured"
#         else:
#             health_status["checks"]["bamboohr"] = "not configured"
#     except:
#         health_status["checks"]["bamboohr"] = "unknown"
    
#     return jsonify(health_status), 200 if health_status["status"] == "healthy" else 503

# # Error handlers
# @app.errorhandler(404)
# def not_found(error):
#     return jsonify({"error": "Endpoint not found"}), 404

# @app.errorhandler(500)
# def internal_error(error):
#     logger.error(f"Internal server error: {error}")
#     return jsonify({"error": "Internal server error"}), 500

# @app.errorhandler(429)
# def rate_limit_exceeded(error):
#     return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429

# # Startup validation
# with app.app_context():
#     try:
#         validate_environment()
#         logger.info("TalentFlow AI Backend started successfully")
#     except Exception as e:
#         logger.error(f"Startup failed: {e}")
#         print(f"❌ Startup failed: {e}")
#         print("Please check your environment variables in .env file")
#         sys.exit(1)

# if __name__ == "__main__":
#     print("🚀 Starting TalentFlow AI Backend (Production Mode)...")
#     print("📍 Server running at http://127.0.0.1:5000")
#     print("📍 Logging to: logs/talentflow.log")
    
#     # In production, use a proper WSGI server like Gunicorn
#     if os.getenv('FLASK_ENV') == 'production':
#         print("⚠️  Warning: Use a production WSGI server like Gunicorn in production!")
    
#     app.run(
#         host='0.0.0.0',
#         port=5000,
#         debug=os.getenv('FLASK_ENV') == 'development',
#         use_reloader=False
#     )
# backend.py - Optimized Version with Performance Improvements

from flask import Flask, request, jsonify, redirect, render_template_string, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
from db import Candidate, SessionLocal
import threading
import asyncio
import time
import traceback
import os
import json
from sqlalchemy import func, and_
import requests
import logging
from logging.handlers import RotatingFileHandler
from functools import wraps
from tenacity import retry, stop_after_attempt, wait_exponential
import sys
from flask_caching import Cache
import redis
from concurrent.futures import ThreadPoolExecutor
import uuid

# Import your existing modules
try:
    from scraper import scrape_job
    from latest import create_programming_assessment
    from test_link import get_invite_link
    from clint_recruitment_system import run_recruitment_with_invite_link
    from email_util import send_assessment_email, send_assessment_reminder, send_interview_confirmation_email, send_interview_link_email, send_rejection_email
except ImportError as e:
    logging.error(f"Critical module import failed: {e}")
    raise

# Add after existing imports
try:
    from testlify_results_scraper import scrape_all_pending_assessments, scrape_assessment_results_by_name
except ImportError as e:
    logging.warning(f"Testlify scraper not available: {e}")

# Setup proper logging
def setup_logging():
    """Configure logging for production"""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )
    
    # File handler
    file_handler = RotatingFileHandler(
        'logs/talentflow.log',
        maxBytes=10485760,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # Console handler  
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add our handlers
    logger.addHandler(file_handler)
    
    # Only add console handler in development
    if os.getenv('FLASK_ENV') == 'development':
        logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

# Configuration from environment
ASSESSMENT_CONFIG = {
    'EXPIRY_HOURS': int(os.getenv('ASSESSMENT_EXPIRY_HOURS', '48')),
    'REMINDER_HOURS': int(os.getenv('ASSESSMENT_REMINDER_HOURS', '24')),
    'INTERVIEW_DELAY_DAYS': int(os.getenv('INTERVIEW_DELAY_DAYS', '3')),
    'ATS_THRESHOLD': float(os.getenv('ATS_THRESHOLD', '70')),
    'MAX_RETRIES': int(os.getenv('MAX_RETRIES', '3')),
    'RETRY_DELAY': int(os.getenv('RETRY_DELAY', '2'))
}

# Create Flask app
app = Flask(__name__)

# Setup caching
cache_config = {
    'CACHE_TYPE': 'simple',  # Use Redis in production
    'CACHE_DEFAULT_TIMEOUT': 300  # 5 minutes
}

if os.getenv('REDIS_URL'):
    cache_config = {
        'CACHE_TYPE': 'redis',
        'CACHE_REDIS_URL': os.getenv('REDIS_URL'),
        'CACHE_DEFAULT_TIMEOUT': 300
    }

cache = Cache(app, config=cache_config)

# Enhanced CORS Configuration
CORS(app, 
     origins=["http://localhost:3000", "http://127.0.0.1:3000", "https://yourfrontenddomain.com"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Cache-Control"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     supports_credentials=True,
     expose_headers=["Content-Type", "Authorization"])

# Thread pool for background tasks
executor = ThreadPoolExecutor(max_workers=4)

# Pipeline status tracking
pipeline_status = {}
pipeline_lock = threading.Lock()

# Performance monitoring
request_metrics = {
    'total_requests': 0,
    'avg_response_time': 0,
    'slow_requests': 0
}
# Admin notification function
def notify_admin(subject, message, error_details=None):
    """Send critical notifications to admin"""
    try:
        admin_email = os.getenv('ADMIN_EMAIL')
        if not admin_email:
            logger.warning("ADMIN_EMAIL not set, skipping notification")
            return
        
        from email_util import send_email
        
        body_html = f"""
        <html>
            <body>
                <h2>TalentFlow AI Alert: {subject}</h2>
                <p>{message}</p>
                {f'<pre>{error_details}</pre>' if error_details else ''}
                <p>Time: {datetime.now().isoformat()}</p>
            </body>
        </html>
        """
        
        send_email(admin_email, f"[TalentFlow Alert] {subject}", body_html)
        
    except Exception as e:
        logger.error(f"Failed to send admin notification: {e}")

# Add request timing middleware
@app.before_request
def before_request():
    request.start_time = time.time()
    request_metrics['total_requests'] += 1

@app.after_request
def after_request(response):
    if hasattr(request, 'start_time'):
        duration = time.time() - request.start_time
        
        # Update metrics
        if request_metrics['avg_response_time'] == 0:
            request_metrics['avg_response_time'] = duration
        else:
            request_metrics['avg_response_time'] = (request_metrics['avg_response_time'] + duration) / 2
        
        if duration > 5.0:  # Slow request threshold
            request_metrics['slow_requests'] += 1
            logger.warning(f"Slow request: {request.method} {request.path} took {duration:.2f}s")
        
        # Add performance headers
        response.headers['X-Response-Time'] = f"{duration:.3f}s"
        response.headers['X-Request-ID'] = getattr(request, 'request_id', 'unknown')
    
    return response

# Add request logging for debugging
@app.before_request
def log_request_info():
    """Log incoming requests for debugging"""
    request.request_id = str(uuid.uuid4())[:8]
    if request.endpoint and (request.endpoint.startswith('api_') or 'api' in request.path):
        logger.info(f"🌐 [{request.request_id}] {request.method} {request.path} from {request.remote_addr}")
        if request.method == 'OPTIONS':
            logger.info(f"🔧 [{request.request_id}] CORS preflight for {request.path}")

# Rate limiting decorator with better performance
def rate_limit(max_calls=10, time_window=60):
    """Enhanced rate limiting decorator with memory optimization"""
    calls = {}
    cleanup_counter = 0
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal cleanup_counter
            
            # Skip rate limiting for OPTIONS requests (CORS preflight)
            if request.method == 'OPTIONS':
                return func(*args, **kwargs)
            
            now = time.time()
            key = request.remote_addr
            
            # Periodic cleanup to prevent memory leaks
            cleanup_counter += 1
            if cleanup_counter % 100 == 0:
                cutoff = now - time_window * 2
                for ip in list(calls.keys()):
                    calls[ip] = [call_time for call_time in calls.get(ip, []) if call_time > cutoff]
                    if not calls[ip]:
                        del calls[ip]
            
            if key not in calls:
                calls[key] = []
            
            # Remove old calls
            calls[key] = [call_time for call_time in calls[key] if now - call_time < time_window]
            
            if len(calls[key]) >= max_calls:
                logger.warning(f"Rate limit exceeded for {key}")
                return jsonify({"error": "Rate limit exceeded"}), 429
            
            calls[key].append(now)
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Pipeline management functions
def update_pipeline_status(job_id, status, message, progress=None):
    """Thread-safe pipeline status updates"""
    with pipeline_lock:
        pipeline_status[str(job_id)] = {
            'status': status,
            'message': message,
            'progress': progress,
            'timestamp': datetime.now().isoformat(),
            'job_id': str(job_id)
        }
    logger.info(f"Pipeline {job_id}: {status} - {message}")

def get_pipeline_status(job_id=None):
    """Get pipeline status (thread-safe)"""
    with pipeline_lock:
        if job_id:
            return pipeline_status.get(str(job_id))
        return dict(pipeline_status)

# Optimized data fetching with caching
@cache.memoize(timeout=300)
def get_cached_jobs():
    """Cached job fetching"""
    try:
        API_KEY = os.getenv("BAMBOOHR_API_KEY")
        SUBDOMAIN = os.getenv("BAMBOOHR_SUBDOMAIN")
        
        if not API_KEY or not SUBDOMAIN:
            raise ValueError("BambooHR credentials not configured")
            
        auth = (API_KEY, "x")
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        url = f"https://api.bamboohr.com/api/gateway.php/{SUBDOMAIN}/v1/applicant_tracking/jobs/"
        
        resp = requests.get(url, auth=auth, headers=headers, timeout=10)
        resp.raise_for_status()
        
        jobs = resp.json()
        open_jobs = []
        
        session = SessionLocal()
        try:
            for job in jobs:
                if job.get("status", {}).get("label", "").lower() == "open":
                    # Get candidate count for this job
                    candidate_count = session.query(Candidate).filter_by(job_id=str(job["id"])).count()
                    
                    open_jobs.append({
                        "id": job["id"],
                        "title": job.get("title", {}).get("label", ""),
                        "location": job.get("location", {}).get("label", ""),
                        "department": job.get("department", {}).get("label", ""),
                        "postingUrl": job.get("postingUrl", ""),
                        "applications": candidate_count,
                        "status": "Active",
                        "description": job.get("description", "")
                    })
        finally:
            session.close()
        
        return open_jobs
        
    except Exception as e:
        logger.error(f"BambooHR API error: {e}")
        # Fallback to database
        return get_jobs_from_database()

def get_jobs_from_database():
    """Fallback job fetching from database"""
    session = SessionLocal()
    try:
        jobs_data = session.query(
            Candidate.job_id,
            Candidate.job_title,
            func.count(Candidate.id).label('applications')
        ).filter(
            Candidate.job_id.isnot(None),
            Candidate.job_title.isnot(None)
        ).group_by(
            Candidate.job_id, 
            Candidate.job_title
        ).all()
        
        jobs = []
        for job_id, job_title, app_count in jobs_data:
            jobs.append({
                'id': str(job_id),
                'title': job_title,
                'department': 'Engineering',
                'location': 'Remote',
                'applications': app_count,
                'status': 'Active',
                'description': f'Job description for {job_title}',
                'postingUrl': ''
            })
        
        return jobs
    finally:
        session.close()

@cache.memoize(timeout=180)  # 3 minutes cache
def get_cached_candidates(job_id=None, status_filter=None):
    """Cached candidate fetching with optimized queries"""
    session = SessionLocal()
    try:
        query = session.query(Candidate)
        
        if job_id:
            query = query.filter_by(job_id=str(job_id))
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        # Optimize query - only get needed fields for list view
        candidates = query.all()
        
        result = []
        for c in candidates:
            try:
                # Calculate time remaining for assessment
                time_remaining = None
                link_expired = False
                
                if c.exam_link_sent_date and not c.exam_completed:
                    deadline = c.exam_link_sent_date + timedelta(hours=ASSESSMENT_CONFIG['EXPIRY_HOURS'])
                    if datetime.now() < deadline:
                        time_remaining = (deadline - datetime.now()).total_seconds() / 3600
                    else:
                        link_expired = True
                
                candidate_data = {
                    "id": c.id,
                    "name": c.name or "Unknown",
                    "email": c.email or "",
                    "job_id": c.job_id,
                    "job_title": c.job_title or "Unknown Position",
                    "status": c.status,
                    "ats_score": float(c.ats_score) if c.ats_score else 0.0,
                    "linkedin": c.linkedin,
                    "github": c.github,
                    "phone": getattr(c, 'phone', None),
                    "resume_path": c.resume_path,
                    "processed_date": c.processed_date.isoformat() if c.processed_date else None,
                    "score_reasoning": c.score_reasoning,
                    
                    # Assessment fields
                    "assessment_invite_link": c.assessment_invite_link,
                    "exam_link_sent": bool(c.exam_link_sent),
                    "exam_link_sent_date": c.exam_link_sent_date.isoformat() if c.exam_link_sent_date else None,
                    "exam_completed": bool(c.exam_completed),
                    "exam_completed_date": c.exam_completed_date.isoformat() if c.exam_completed_date else None,
                    "link_expired": link_expired,
                    "time_remaining_hours": time_remaining,
                    
                    # Exam results
                    "exam_percentage": float(c.exam_percentage) if c.exam_percentage else None,
                    
                    # Interview fields
                    "interview_scheduled": bool(c.interview_scheduled),
                    "interview_date": c.interview_date.isoformat() if c.interview_date else None,
                    "interview_link": c.interview_link,
                    
                    # Status fields
                    "final_status": c.final_status,
                }
                
                result.append(candidate_data)
                
            except Exception as e:
                logger.error(f"Error processing candidate {c.id}: {e}")
                continue
        
        return result
    finally:
        session.close()

# Enhanced API endpoints
@app.route('/api/jobs', methods=['GET', 'OPTIONS'])
@rate_limit(max_calls=30, time_window=60)
def api_jobs():
    """Enhanced API endpoint to get jobs with caching"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        jobs = get_cached_jobs()
        return jsonify(jobs), 200
    except Exception as e:
        logger.error(f"Error in api_jobs: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch jobs", "message": str(e)}), 500

@app.route('/api/candidates', methods=['GET', 'OPTIONS'])
@rate_limit(max_calls=60, time_window=60)
def api_candidates():
    """Enhanced API endpoint to get candidates with caching"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        job_id = request.args.get('job_id')
        status_filter = request.args.get('status')
        
        candidates = get_cached_candidates(job_id, status_filter)
        return jsonify(candidates), 200
        
    except Exception as e:
        logger.error(f"Error in api_candidates: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch candidates", "message": str(e)}), 500

@app.route('/api/run_full_pipeline', methods=['POST', 'OPTIONS'])
@rate_limit(max_calls=5, time_window=300)
def api_run_full_pipeline():
    """Enhanced pipeline API with status tracking"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.json
        job_id = data.get('job_id')
        job_title = data.get('job_title')
        job_desc = data.get('job_desc', "")
        
        logger.info(f"[{request.request_id}] Pipeline request: job_id={job_id}, job_title={job_title}")
        
        if not job_id or not job_title:
            return jsonify({"success": False, "message": "job_id and job_title are required"}), 400
        
        # Check if pipeline is already running for this job
        current_status = get_pipeline_status(job_id)
        if current_status and current_status.get('status') == 'running':
            return jsonify({
                "success": False,
                "message": f"Pipeline already running for {job_title}",
                "status": current_status
            }), 409
        
        # # Update status to starting
        # update_pipeline_status(job_id, 'starting', f'Initializing pipeline for {job_title}', 0)
        
# Update status to starting
        update_pipeline_status(job_id, 'starting', f'Initializing pipeline for {job_title}', 0)
        
        # Start the pipeline in background thread
        future = executor.submit(run_pipeline_with_monitoring, job_id, job_title, job_desc)
        
        # Store future for tracking
        with pipeline_lock:
            pipeline_status[str(job_id)]['future'] = future
        
        return jsonify({
            "success": True, 
            "message": f"Pipeline started for {job_title}",
            "job_id": job_id,
            "estimated_time": "5-10 minutes",
            "status_endpoint": f"/api/pipeline_status/{job_id}"
        }), 200
        
    except Exception as e:
        logger.error(f"Error in run_full_pipeline: {e}", exc_info=True)
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/pipeline_status', methods=['GET', 'OPTIONS'])
@app.route('/api/pipeline_status/<job_id>', methods=['GET', 'OPTIONS'])
def api_pipeline_status(job_id=None):
    """Get pipeline status for specific job or all jobs"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        if job_id:
            status = get_pipeline_status(job_id)
            if not status:
                return jsonify({"success": False, "message": "Pipeline not found"}), 404
            
            # Clean up the status (remove future object for JSON serialization)
            clean_status = {k: v for k, v in status.items() if k != 'future'}
            return jsonify({"success": True, "status": clean_status}), 200
        else:
            all_status = get_pipeline_status()
            # Clean up all statuses
            clean_statuses = {k: {sk: sv for sk, sv in v.items() if sk != 'future'} 
                            for k, v in all_status.items()}
            return jsonify({"success": True, "pipelines": clean_statuses}), 200
            
    except Exception as e:
        logger.error(f"Error in pipeline_status: {e}", exc_info=True)
        return jsonify({"success": False, "message": str(e)}), 500

def run_pipeline_with_monitoring(job_id, job_title, job_desc):
    """Enhanced pipeline runner with detailed progress tracking"""
    start_time = time.time()
    
    try:
        logger.info(f"Starting monitored pipeline for job_id={job_id}")
        update_pipeline_status(job_id, 'running', 'Pipeline started', 10)
        
        # Clear relevant caches
        cache.delete_memoized(get_cached_candidates)
        cache.delete_memoized(get_cached_jobs)
        
        full_recruitment_pipeline(job_id, job_title, job_desc)
        
        duration = time.time() - start_time
        update_pipeline_status(job_id, 'completed', f'Pipeline completed successfully in {duration:.1f}s', 100)
        logger.info(f"Pipeline completed successfully in {duration:.2f} seconds")
        
    except Exception as e:
        duration = time.time() - start_time
        error_msg = f"Pipeline failed after {duration:.2f} seconds: {str(e)}"
        update_pipeline_status(job_id, 'error', error_msg, None)
        logger.error(error_msg, exc_info=True)

def full_recruitment_pipeline(job_id, job_title, job_desc):
    """Enhanced recruitment pipeline with progress tracking"""
    try:
        logger.info(f"Starting full recruitment pipeline for job_id={job_id}, job_title={job_title}")
        
        # STEP 1: Scraping (20% progress)
        try:
            update_pipeline_status(job_id, 'running', 'Scraping resumes...', 20)
            logger.info(f"STEP 1: Scraping resumes for job_id={job_id}")
            asyncio.run(scrape_job(job_id))
            logger.info("✅ Scraping completed successfully")
        except Exception as e:
            logger.error(f"Scraping failed: {str(e)}", exc_info=True)
            # Continue with next step even if scraping fails
        
        # STEP 2: Create assessment (40% progress)
        try:
            update_pipeline_status(job_id, 'running', 'Creating programming assessment...', 40)
            logger.info(f"STEP 2: Creating assessment for '{job_title}' in Testlify")
            create_programming_assessment(job_title, job_desc)
            logger.info("✅ Assessment created successfully")
        except Exception as e:
            logger.error(f"Assessment creation failed: {str(e)}", exc_info=True)
        
        # STEP 3: Get invite link (60% progress)
        invite_link = None
        try:
            update_pipeline_status(job_id, 'running', 'Extracting assessment invite link...', 60)
            logger.info(f"STEP 3: Extracting invite link for '{job_title}' from Testlify")
            invite_link = get_invite_link(job_title)
            if invite_link:
                logger.info(f"✅ Got invite link: {invite_link}")
        except Exception as e:
            logger.error(f"Invite link extraction failed: {str(e)}", exc_info=True)
        
        if not invite_link:
            invite_link = f"https://candidate.testlify.com/assessment/{job_id}"
            logger.warning(f"Using fallback invite link: {invite_link}")
        
        # STEP 4: Run AI screening (80% progress)
        try:
            update_pipeline_status(job_id, 'running', 'Running AI-powered screening...', 80)
            logger.info("STEP 4: Running AI-powered screening...")
            run_recruitment_with_invite_link(
                job_id=job_id, 
                job_title=job_title, 
                job_desc=job_desc, 
                invite_link=invite_link
            )
            logger.info("✅ AI screening completed successfully")
        except Exception as e:
            logger.error(f"AI screening failed: {str(e)}", exc_info=True)
            raise  # This is critical, so we raise
        
        # Final step: Clear caches
        cache.delete_memoized(get_cached_candidates)
        cache.delete_memoized(get_cached_jobs)
        
        logger.info("🚀 Recruitment pipeline finished successfully")
            
    except Exception as e:
        logger.error(f"Fatal pipeline error: {e}", exc_info=True)
        raise

@app.route('/api/recruitment-stats', methods=['GET', 'OPTIONS'])
@rate_limit(max_calls=20, time_window=60)
@cache.memoize(timeout=600)  # 10 minute cache
def api_recruitment_stats():
    """Cached recruitment statistics"""
    if request.method == 'OPTIONS':
        return '', 200
    
    session = SessionLocal()
    try:
        stats = []
        current_date = datetime.now()
        
        # Get last 6 months of data efficiently
        for i in range(6):
            try:
                month_date = current_date - timedelta(days=30*i)
                month_name = month_date.strftime('%b')
                
                # Calculate month boundaries
                month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                if month_start.month == 12:
                    month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(seconds=1)
                else:
                    month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(seconds=1)
                
                # Single query for all stats
                applications = session.query(func.count(Candidate.id)).filter(
                    and_(
                        Candidate.processed_date >= month_start,
                        Candidate.processed_date <= month_end
                    )
                ).scalar() or 0
                
                interviews = session.query(func.count(Candidate.id)).filter(
                    and_(
                        Candidate.interview_scheduled == True,
                        Candidate.interview_date >= month_start,
                        Candidate.interview_date <= month_end
                    )
                ).scalar() or 0
                
                hires = session.query(func.count(Candidate.id)).filter(
                    and_(
                        Candidate.final_status == "Hired",
                        Candidate.processed_date >= month_start,
                        Candidate.processed_date <= month_end
                    )
                ).scalar() or 0
                
                stats.append({
                    "month": month_name,
                    "applications": applications,
                    "interviews": interviews,
                    "hires": hires
                })
                
            except Exception as e:
                logger.error(f"Error calculating stats for month {i}: {e}")
                stats.append({
                    "month": (current_date - timedelta(days=30*i)).strftime('%b'),
                    "applications": 0,
                    "interviews": 0,
                    "hires": 0
                })
        
        # Reverse to get chronological order
        stats.reverse()
        
        logger.info(f"Generated recruitment stats for {len(stats)} months")
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Error in api_recruitment_stats: {e}", exc_info=True)
        return jsonify({"error": "Failed to get statistics", "message": str(e)}), 500
    finally:
        session.close()

@app.route('/api/send_reminder/<int:candidate_id>', methods=['POST', 'OPTIONS'])
@rate_limit(max_calls=10, time_window=60)
def api_send_reminder(candidate_id):
    """Send reminder to specific candidate"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        session = SessionLocal()
        try:
            candidate = session.query(Candidate).filter_by(id=candidate_id).first()
            if not candidate:
                return jsonify({"success": False, "message": "Candidate not found"}), 404
            
            # Check if candidate is eligible for reminder
            if not candidate.exam_link_sent or candidate.exam_completed:
                return jsonify({"success": False, "message": "Candidate not eligible for reminder"}), 400
            
            # Calculate hours remaining
            hours_remaining = 24  # Default
            if candidate.exam_link_sent_date:
                deadline = candidate.exam_link_sent_date + timedelta(hours=48)
                hours_remaining = max(0, int((deadline - datetime.now()).total_seconds() / 3600))
            
            # Send reminder email
            send_assessment_reminder(candidate, hours_remaining)
            
            # Update reminder tracking
            candidate.reminder_sent = True
            candidate.reminder_sent_date = datetime.now()
            session.commit()
            
            # Clear cache
            cache.delete_memoized(get_cached_candidates)
            
            return jsonify({
                "success": True,
                "message": f"Reminder sent to {candidate.name}"
            }), 200
            
        finally:
            session.close()
        
    except Exception as e:
        logger.error(f"Error in send_reminder: {e}", exc_info=True)
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/schedule-interview', methods=['POST', 'OPTIONS'])
@rate_limit(max_calls=10, time_window=60)
def api_schedule_interview():
    """Schedule an interview for a candidate"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.json
        candidate_id = data.get('candidate_id')
        email = data.get('email')
        interview_date = data.get('date')
        time_slot = data.get('time_slot')
        
        if not candidate_id and not email:
            return jsonify({"success": False, "message": "candidate_id or email is required"}), 400
        
        session = SessionLocal()
        try:
            # Find candidate
            if candidate_id:
                candidate = session.query(Candidate).filter_by(id=candidate_id).first()
            else:
                candidate = session.query(Candidate).filter_by(email=email).first()
            
            if not candidate:
                return jsonify({"success": False, "message": "Candidate not found"}), 404
            
            # Parse interview date
            if isinstance(interview_date, str):
                interview_datetime = datetime.fromisoformat(interview_date.replace('Z', '+00:00'))
            else:
                interview_datetime = datetime.now() + timedelta(days=3)
            
            # Update candidate
            candidate.interview_scheduled = True
            candidate.interview_date = interview_datetime
            candidate.final_status = 'Interview Scheduled'
            
            # Generate Google Meet link
            meeting_link = f"https://meet.google.com/lookup/generated-meeting-id-{candidate.id}"
            candidate.interview_link = meeting_link
            
            # Send interview confirmation email
            try:
                send_interview_confirmation_email(candidate, interview_datetime, meeting_link)
            except Exception as e:
                logger.warning(f"Failed to send interview email to {candidate.email}: {e}")
            
            session.commit()
            
            # Clear cache
            cache.delete_memoized(get_cached_candidates)
            
            return jsonify({
                "success": True,
                "message": f"Interview scheduled for {candidate.name}",
                "meeting_link": meeting_link,
                "interview_date": interview_datetime.isoformat(),
                "candidate": {
                    "id": candidate.id,
                    "name": candidate.name,
                    "email": candidate.email
                }
            }), 200
            
        finally:
            session.close()
        
    except Exception as e:
        logger.error(f"Error in schedule_interview: {e}", exc_info=True)
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/scrape_assessment_results', methods=['POST', 'OPTIONS'])
@rate_limit(max_calls=3, time_window=300)  # Max 3 scraping requests per 5 minutes
def api_scrape_assessment_results():
    """API endpoint to scrape assessment results for a specific assessment"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.json
        assessment_name = data.get('assessment_name')
        
        if not assessment_name:
            return jsonify({"success": False, "message": "assessment_name is required"}), 400
        
        logger.info(f"Starting results scraping for assessment: {assessment_name}")
        
        # Start scraping in a separate thread
        scraping_thread = threading.Thread(
            target=lambda: run_scraping_with_monitoring(assessment_name),
            daemon=True,
            name=f"scraping_{assessment_name.replace(' ', '_')}_{int(time.time())}"
        )
        scraping_thread.start()
        
        return jsonify({
            "success": True,
            "message": f"Started scraping results for '{assessment_name}'",
            "estimated_time": "2-5 minutes"
        }), 200
        
    except Exception as e:
        logger.error(f"Error in scrape_assessment_results: {e}", exc_info=True)
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/scrape_all_pending_results', methods=['POST', 'OPTIONS'])
@rate_limit(max_calls=1, time_window=600)  # Max 1 bulk scraping per 10 minutes
def api_scrape_all_pending_results():
    """API endpoint to scrape all pending assessment results"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        logger.info("Starting bulk results scraping for all pending assessments")
        
        # Start bulk scraping in a separate thread
        scraping_thread = threading.Thread(
            target=lambda: run_bulk_scraping_with_monitoring(),
            daemon=True,
            name=f"bulk_scraping_{int(time.time())}"
        )
        scraping_thread.start()
        
        return jsonify({
            "success": True,
            "message": "Started bulk scraping for all pending assessments",
            "estimated_time": "5-15 minutes"
        }), 200
        
    except Exception as e:
        logger.error(f"Error in scrape_all_pending_results: {e}", exc_info=True)
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/scrape_assessment_results', methods=['GET','OPTIONS'])
def api_scraping_status():
    """Get status of running scraping operations"""
    try:
        # Get active scraping threads
        active_threads = []
        for thread in threading.enumerate():
            if thread.name.startswith(('scraping_', 'bulk_scraping_')):
                thread_info = {
                    "name": thread.name,
                    "is_alive": thread.is_alive(),
                    "daemon": thread.daemon
                }
                active_threads.append(thread_info)
        
        return jsonify({
            "success": True,
            "active_operations": len(active_threads),
            "operations": active_threads
        }), 200
        
    except Exception as e:
        logger.error(f"Error in scraping_status: {e}", exc_info=True)
        return jsonify({"success": False, "message": str(e)}), 500
def run_scraping_with_monitoring(assessment_name: str):
    """Wrapper to run scraping with monitoring and error handling"""
    start_time = time.time()
    
    try:
        logger.info(f"Starting monitored scraping for assessment: {assessment_name}")
        
        # Import and run the scraping function
        try:
            from testlify_results_scraper import scrape_assessment_results_by_name
        except ImportError as e:
            logger.error(f"Failed to import scraper: {e}")
            notify_admin(
                "Scraper Import Error",
                f"Could not import results scraper: {str(e)}. Please ensure testlify_results_scraper.py is available."
            )
            return
        
        # Run the async scraping function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(scrape_assessment_results_by_name(assessment_name))
        finally:
            loop.close()
        
        duration = time.time() - start_time
        logger.info(f"Scraping completed successfully in {duration:.2f} seconds. Found {len(results)} candidates.")
        
        # Send success notification
        notify_admin(
            "Assessment Results Scraping Completed",
            f"Assessment: {assessment_name}\nCandidates processed: {len(results)}\nDuration: {duration:.2f} seconds"
        )
        
    except Exception as e:
        duration = time.time() - start_time
        error_msg = f"Scraping failed for assessment '{assessment_name}' after {duration:.2f} seconds"
        logger.error(error_msg, exc_info=True)
        
        # Send failure notification
        notify_admin(
            "Assessment Results Scraping Failed",
            error_msg,
            error_details=traceback.format_exc()
        )


def run_bulk_scraping_with_monitoring():
    """Wrapper to run bulk scraping with monitoring"""
    start_time = time.time()
    
    try:
        logger.info("Starting bulk scraping for all pending assessments")
        
        # Import and run the bulk scraping function
        try:
            from testlify_results_scraper import scrape_all_pending_assessments
        except ImportError as e:
            logger.error(f"Failed to import scraper: {e}")
            notify_admin(
                "Scraper Import Error",
                f"Could not import results scraper: {str(e)}. Please ensure testlify_results_scraper.py is available."
            )
            return
        
        # Run the async scraping function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results_summary = loop.run_until_complete(scrape_all_pending_assessments())
        finally:
            loop.close()
        
        duration = time.time() - start_time
        total_candidates = sum(results_summary.values()) if isinstance(results_summary, dict) else 0
        
        logger.info(f"Bulk scraping completed in {duration:.2f} seconds. Processed {len(results_summary)} assessments, {total_candidates} candidates.")
        
        # Send success notification
        if isinstance(results_summary, dict):
            summary_text = "\n".join([f"- {assessment}: {count} candidates" for assessment, count in results_summary.items()])
        else:
            summary_text = f"Processed {total_candidates} total candidates"
            
        notify_admin(
            "Bulk Assessment Results Scraping Completed",
            f"Assessments processed: {len(results_summary) if isinstance(results_summary, dict) else 'Unknown'}\nTotal candidates: {total_candidates}\nDuration: {duration:.2f} seconds\n\nBreakdown:\n{summary_text}"
        )
        
    except Exception as e:
        duration = time.time() - start_time
        error_msg = f"Bulk scraping failed after {duration:.2f} seconds"
        logger.error(error_msg, exc_info=True)
        
        # Send failure notification
        notify_admin(
            "Bulk Assessment Results Scraping Failed",
            error_msg,
            error_details=traceback.format_exc()
        )

@app.route('/health', methods=['GET'])
def health_check():
    """Enhanced health check endpoint with system status"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.1.0",
        "checks": {},
        "performance": {
            "avg_response_time": f"{request_metrics['avg_response_time']:.3f}s",
            "total_requests": request_metrics['total_requests'],
            "slow_requests": request_metrics['slow_requests']
        }
    }
    
    # Check database
    try:
        session = SessionLocal()
        session.execute("SELECT 1")
        session.close()
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check cache
    try:
        cache.set('health_check', 'ok', timeout=1)
        if cache.get('health_check') == 'ok':
            health_status["checks"]["cache"] = "healthy"
        else:
            health_status["checks"]["cache"] = "unhealthy"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["cache"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check thread pool
    try:
        if hasattr(executor, '_threads'):
            active_threads = len([t for t in executor._threads if t.is_alive()])
            health_status["checks"]["thread_pool"] = f"healthy ({active_threads} active threads)"
        else:
            health_status["checks"]["thread_pool"] = "healthy"
    except Exception as e:
        health_status["checks"]["thread_pool"] = f"degraded: {str(e)}"
    
    return jsonify(health_status), 200 if health_status["status"] == "healthy" else 503

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429

# Cleanup on shutdown
import atexit

def cleanup():
    """Cleanup resources on shutdown"""
    logger.info("Shutting down TalentFlow AI Backend...")
    executor.shutdown(wait=True)
    
atexit.register(cleanup)

if __name__ == "__main__":
    print("🚀 Starting TalentFlow AI Backend (Optimized Version)...")
    print("📍 Server running at http://127.0.0.1:5000")
    print("📍 Logging to: logs/talentflow.log")
    print("⚡ Performance optimizations enabled")
    print("💾 Caching enabled")
    print("🔄 Pipeline status tracking enabled")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=os.getenv('FLASK_ENV') == 'development',
        use_reloader=False,
        threaded=True
    )