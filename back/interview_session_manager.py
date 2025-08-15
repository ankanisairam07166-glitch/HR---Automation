# interview_session_manager.py - Enhanced Version with Best Features from Both

import os
import json
import uuid
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import threading
import time
from pathlib import Path
import hashlib
import queue
from dataclasses import dataclass, asdict

from sqlalchemy.orm import Session
from db import SessionLocal, Candidate
import boto3  # For S3 storage
from openai import OpenAI  # For AI analysis

logger = logging.getLogger(__name__)

@dataclass
class InterviewQuestion:
    """Represents a question asked during the interview"""
    question_id: str
    question_text: str
    question_type: str  # technical, behavioral, cultural, etc.
    timestamp: datetime
    avatar_used: str = "default"
    expected_answer_keywords: List[str] = None
    difficulty_level: str = "medium"  # easy, medium, hard
    category: str = "general"
    duration: int = 0

@dataclass
class InterviewAnswer:
    """Represents a candidate's answer to a question"""
    answer_id: str
    question_id: str
    answer_text: str
    timestamp: datetime
    duration_seconds: int
    audio_quality: str = "good"  # poor, fair, good, excellent
    confidence_score: float = 0.0  # 0-1
    sentiment: str = "neutral"
    keywords: List[str] = None

class InterviewSessionManager:
    """Enhanced manager with best features from both versions"""
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict] = {}
        self.recording_threads: Dict[str, threading.Thread] = {}
        self.recordings_dir = Path("interview_recordings")
        self.recordings_dir.mkdir(exist_ok=True)
        
        # Background processing queues
        self.recording_queue = queue.Queue()
        self.analysis_queue = queue.Queue()
        self.session_lock = threading.Lock()
        
        # Initialize OpenAI for analysis
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Initialize S3 for cloud storage (optional)
        self.s3_client = None
        if os.getenv('AWS_ACCESS_KEY_ID'):
            self.s3_client = boto3.client('s3')
            self.s3_bucket = os.getenv('S3_BUCKET_NAME', 'interview-recordings')
        
        # Start background workers
        self._start_background_workers()
    
    def _start_background_workers(self):
        """Start background workers for recording and analysis"""
        # Recording worker
        self.recording_thread = threading.Thread(target=self._recording_worker, daemon=True)
        self.recording_thread.start()
        
        # Analysis worker
        self.analysis_thread = threading.Thread(target=self._analysis_worker, daemon=True)
        self.analysis_thread.start()
        
        logger.info("Interview session manager background workers started")
    
    def create_interview_session(self, candidate_id: int, interview_token: str) -> str:
        """Create a new interview session"""
        session_id = str(uuid.uuid4())
        
        session = SessionLocal()
        try:
            candidate = session.query(Candidate).filter_by(id=candidate_id).first()
            if not candidate:
                raise ValueError(f"Candidate {candidate_id} not found")
            
            # Create session data
            session_data = {
                'session_id': session_id,
                'candidate_id': candidate_id,
                'candidate_name': candidate.name,
                'candidate_email': candidate.email,
                'interview_token': interview_token,
                'job_title': candidate.job_title,
                'job_description': candidate.job_description,
                'started_at': datetime.now().isoformat(),
                'status': 'active',
                'questions': [],
                'answers': [],
                'recording_status': 'not_started',
                'recording_file': None,
                'network_quality': 'good',
                'technical_issues': []
            }
            
            # Store in active sessions with lock
            with self.session_lock:
                self.active_sessions[session_id] = session_data
            
            # Update candidate record
            candidate.interview_session_id = session_id
            candidate.interview_started_at = datetime.now()
            candidate.interview_recording_status = 'pending'
            session.commit()
            
            logger.info(f"Created interview session {session_id} for candidate {candidate_id}")
            return session_id
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating interview session: {e}")
            raise
        finally:
            session.close()
    
    def start_interview_recording(self, session_id: str, recording_config: Dict = None) -> bool:
        """Start recording the interview session"""
        try:
            with self.session_lock:
                if session_id not in self.active_sessions:
                    logger.error(f"Session {session_id} not found")
                    return False
                
                session_data = self.active_sessions[session_id]
            
            # Create recording filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"interview_{session_data['candidate_id']}_{timestamp}.webm"
            filepath = self.recordings_dir / filename
            
            # Update session data
            with self.session_lock:
                session_data['recording_status'] = 'recording'
                session_data['recording_file'] = str(filepath)
                session_data['recording_started_at'] = datetime.now().isoformat()
                session_data['recording_config'] = recording_config or {
                    'video_codec': 'vp8',
                    'audio_codec': 'opus',
                    'video_bitrate': '1000k',
                    'audio_bitrate': '128k',
                    'resolution': '1280x720'
                }
            
            # Add to recording queue
            self.recording_queue.put({
                'action': 'start',
                'session_id': session_id,
                'recording_file': str(filepath),
                'config': recording_config or {}
            })
            
            # Update database
            session = SessionLocal()
            try:
                candidate = session.query(Candidate).filter_by(
                    interview_session_id=session_id
                ).first()
                if candidate:
                    candidate.interview_recording_status = 'recording'
                    candidate.interview_recording_file = str(filepath)
                    candidate.interview_recording_format = 'webm'
                    candidate.interview_recording_quality = 'HD'
                    session.commit()
            finally:
                session.close()
            
            logger.info(f"Started recording for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting recording: {e}")
            return False
    
    def add_interview_question(self, session_id: str, question_data: Dict) -> Optional[str]:
        """Add a question asked by the avatar"""
        try:
            with self.session_lock:
                if session_id not in self.active_sessions:
                    return None
                
                session_data = self.active_sessions[session_id]
            
            question = InterviewQuestion(
                question_id=str(uuid.uuid4()),
                question_text=question_data.get('text', ''),
                question_type=question_data.get('type', 'general'),
                timestamp=datetime.now(),
                avatar_used=question_data.get('avatar', 'default'),
                expected_answer_keywords=question_data.get('keywords', []),
                difficulty_level=question_data.get('difficulty', 'medium'),
                category=question_data.get('category', 'general'),
                duration=question_data.get('duration', 0)
            )
            
            with self.session_lock:
                self.active_sessions[session_id]['questions'].append(asdict(question))
            
            # Update question count in database
            self._update_question_count(session_id)
            
            logger.info(f"Added question {question.question_id} to session {session_id}")
            return question.question_id
            
        except Exception as e:
            logger.error(f"Error adding question: {e}")
            return None
    
    def add_interview_answer(self, session_id: str, question_id: str, answer_data: Dict) -> Optional[str]:
        """Add a candidate's answer"""
        try:
            with self.session_lock:
                if session_id not in self.active_sessions:
                    return None
                
                session_data = self.active_sessions[session_id]
            
            answer = InterviewAnswer(
                answer_id=str(uuid.uuid4()),
                question_id=question_id,
                answer_text=answer_data.get('text', ''),
                timestamp=datetime.now(),
                duration_seconds=answer_data.get('duration', 0),
                audio_quality=answer_data.get('audio_quality', 'good'),
                confidence_score=answer_data.get('confidence', 0.0),
                sentiment=answer_data.get('sentiment', 'neutral'),
                keywords=answer_data.get('keywords', [])
            )
            
            with self.session_lock:
                self.active_sessions[session_id]['answers'].append(asdict(answer))
            
            # Update answer count in database
            self._update_answer_count(session_id)
            
            logger.info(f"Added answer {answer.answer_id} to session {session_id}")
            return answer.answer_id
            
        except Exception as e:
            logger.error(f"Error adding answer: {e}")
            return None
    
    def end_interview_session(self, session_id: str) -> bool:
        """End the interview session and trigger analysis"""
        try:
            with self.session_lock:
                if session_id not in self.active_sessions:
                    return False
                
                session_data = self.active_sessions[session_id]
                session_data['ended_at'] = datetime.now().isoformat()
                session_data['status'] = 'completed'
                session_data['recording_status'] = 'completed'
            
            # Calculate duration
            started_at = datetime.fromisoformat(session_data['started_at'])
            duration = (datetime.now() - started_at).total_seconds()
            
            # Save session data to file
            session_file = self.recordings_dir / f"session_{session_id}.json"
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            # Stop recording
            self.recording_queue.put({
                'action': 'stop',
                'session_id': session_id
            })
            
            # Add to analysis queue
            self.analysis_queue.put({
                'session_id': session_id,
                'session_file': str(session_file)
            })
            
            # Update database
            session = SessionLocal()
            try:
                candidate = session.query(Candidate).filter_by(
                    interview_session_id=session_id
                ).first()
                
                if candidate:
                    candidate.interview_completed_at = datetime.now()
                    candidate.interview_recording_status = 'completed'
                    candidate.interview_recording_duration = int(duration)
                    candidate.interview_total_questions = len(session_data['questions'])
                    candidate.interview_answered_questions = len(session_data['answers'])
                    
                    # Store Q&A data
                    candidate.interview_questions_asked = json.dumps(session_data['questions'])
                    candidate.interview_answers_given = json.dumps(session_data['answers'])
                    
                    # Store session logs
                    candidate.interview_session_logs = json.dumps({
                        'session_id': session_id,
                        'duration': duration,
                        'network_quality': session_data.get('network_quality'),
                        'technical_issues': session_data.get('technical_issues', [])
                    })
                    
                    candidate.interview_ai_analysis_status = 'pending'
                    session.commit()
                    
            finally:
                session.close()
            
            # Clean up active session
            with self.session_lock:
                del self.active_sessions[session_id]
            
            logger.info(f"Ended interview session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            return False
    
    def _recording_worker(self):
        """Background worker for handling interview recordings"""
        while True:
            try:
                recording_task = self.recording_queue.get(timeout=1)
                
                if recording_task.get('action') == 'stop':
                    session_id = recording_task['session_id']
                    logger.info(f"Stopping recording for session {session_id}")
                    # Implement recording stop logic here
                    
                elif recording_task.get('action') == 'start':
                    session_id = recording_task['session_id']
                    recording_file = recording_task['recording_file']
                    config = recording_task['config']
                    
                    logger.info(f"Starting recording for session {session_id} to {recording_file}")
                    # Implement recording start logic here
                    
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in recording worker: {e}")
    
    def _analysis_worker(self):
        """Background worker for AI analysis of interviews"""
        while True:
            try:
                analysis_task = self.analysis_queue.get(timeout=1)
                session_id = analysis_task['session_id']
                session_file = analysis_task['session_file']
                
                logger.info(f"Starting AI analysis for session {session_id}")
                
                # Load session data
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                
                # Get candidate ID
                candidate_id = session_data['candidate_id']
                
                # Perform analysis in thread
                self._analyze_interview(session_id, candidate_id)
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in analysis worker: {e}")
    
    def _analyze_interview(self, session_id: str, candidate_id: int):
        """Analyze the interview using AI"""
        try:
            # Load session data
            session_file = self.recordings_dir / f"session_{session_id}.json"
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            # Prepare transcript for analysis
            transcript = self._create_transcript(session_data)
            
            # AI Analysis
            analysis = self._perform_ai_analysis(transcript, session_data)
            
            # Update database with analysis results
            session = SessionLocal()
            try:
                candidate = session.query(Candidate).filter_by(id=candidate_id).first()
                if candidate:
                    candidate.interview_ai_score = analysis['overall_score']
                    candidate.interview_ai_technical_score = analysis['technical_score']
                    candidate.interview_ai_communication_score = analysis['communication_score']
                    candidate.interview_ai_problem_solving_score = analysis['problem_solving_score']
                    candidate.interview_ai_cultural_fit_score = analysis['cultural_fit_score']
                    candidate.interview_ai_overall_feedback = analysis['overall_feedback']
                    candidate.interview_ai_questions_analysis = json.dumps(analysis['question_analysis'])
                    candidate.interview_ai_analysis_status = 'completed'
                    candidate.interview_transcript = transcript
                    
                    # Determine final status
                    if analysis['overall_score'] >= 80:
                        candidate.interview_final_status = 'passed'
                        candidate.final_status = 'Interview Passed - Proceed to Next Round'
                    elif analysis['overall_score'] >= 60:
                        candidate.interview_final_status = 'needs_review'
                        candidate.final_status = 'Interview Complete - Under Review'
                    else:
                        candidate.interview_final_status = 'failed'
                        candidate.final_status = 'Interview Complete - Not Selected'
                    
                    session.commit()
                    logger.info(f"AI analysis completed for candidate {candidate_id}")
                    
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            # Update status to failed
            session = SessionLocal()
            try:
                candidate = session.query(Candidate).filter_by(id=candidate_id).first()
                if candidate:
                    candidate.interview_ai_analysis_status = 'failed'
                    session.commit()
            finally:
                session.close()
    
    def _create_transcript(self, session_data: Dict) -> str:
        """Create a formatted transcript from Q&A data"""
        transcript_lines = []
        
        # Create Q&A mapping
        qa_pairs = []
        for question in session_data['questions']:
            # Find corresponding answer
            answer = next(
                (a for a in session_data['answers'] if a['question_id'] == question['question_id']),
                None
            )
            qa_pairs.append((question, answer))
        
        # Format transcript
        transcript_lines.append(f"Interview Transcript - {session_data['job_title']}")
        transcript_lines.append(f"Candidate: {session_data['candidate_name']}")
        transcript_lines.append(f"Date: {session_data['started_at']}")
        transcript_lines.append("-" * 50)
        
        for i, (question, answer) in enumerate(qa_pairs, 1):
            transcript_lines.append(f"\nQ{i} [{question['category']}]: {question['question_text']}")
            if answer:
                transcript_lines.append(f"A{i}: {answer['answer_text']}")
            else:
                transcript_lines.append(f"A{i}: [No answer provided]")
        
        return "\n".join(transcript_lines)
    
    def _perform_ai_analysis(self, transcript: str, session_data: Dict) -> Dict:
        """Perform AI analysis on the interview"""
        try:
            # Prepare the analysis prompt
            prompt = f"""
            Analyze this technical interview transcript and provide detailed feedback.
            
            Job Title: {session_data['job_title']}
            
            Transcript:
            {transcript}
            
            Please analyze and score (0-100) the following aspects:
            1. Technical Skills - Knowledge of required technologies and concepts
            2. Communication Skills - Clarity, articulation, and presentation
            3. Problem Solving - Approach to challenges and analytical thinking
            4. Cultural Fit - Alignment with company values and team dynamics
            
            Also provide:
            - Overall score (weighted average)
            - Overall feedback and recommendation
            - Specific feedback for each question
            
            Format the response as JSON.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert technical interviewer providing detailed candidate assessment."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            analysis = json.loads(response.choices[0].message.content)
            
            # Ensure all required fields
            return {
                'overall_score': analysis.get('overall_score', 0),
                'technical_score': analysis.get('technical_score', 0),
                'communication_score': analysis.get('communication_score', 0),
                'problem_solving_score': analysis.get('problem_solving_score', 0),
                'cultural_fit_score': analysis.get('cultural_fit_score', 0),
                'overall_feedback': analysis.get('overall_feedback', 'Analysis pending'),
                'question_analysis': analysis.get('question_analysis', [])
            }
            
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            # Return default scores
            return {
                'overall_score': 50,
                'technical_score': 50,
                'communication_score': 50,
                'problem_solving_score': 50,
                'cultural_fit_score': 50,
                'overall_feedback': 'AI analysis could not be completed. Manual review required.',
                'question_analysis': []
            }
    
    def _update_question_count(self, session_id: str):
        """Update question count in database"""
        session = SessionLocal()
        try:
            candidate = session.query(Candidate).filter_by(
                interview_session_id=session_id
            ).first()
            if candidate:
                with self.session_lock:
                    candidate.interview_total_questions = len(
                        self.active_sessions[session_id]['questions']
                    )
                session.commit()
        finally:
            session.close()
    
    def _update_answer_count(self, session_id: str):
        """Update answer count in database"""
        session = SessionLocal()
        try:
            candidate = session.query(Candidate).filter_by(
                interview_session_id=session_id
            ).first()
            if candidate:
                with self.session_lock:
                    candidate.interview_answered_questions = len(
                        self.active_sessions[session_id]['answers']
                    )
                session.commit()
        finally:
            session.close()
    
    def get_session_data(self, session_id: str) -> Optional[Dict]:
        """Get session data"""
        with self.session_lock:
            if session_id in self.active_sessions:
                return self.active_sessions[session_id].copy()
        
        # Try to load from file if not active
        session_file = self.recordings_dir / f"session_{session_id}.json"
        if session_file.exists():
            with open(session_file, 'r') as f:
                return json.load(f)
        
        return None
    
    def upload_recording_to_cloud(self, session_id: str, local_file_path: str) -> Optional[str]:
        """Upload recording to cloud storage (S3)"""
        if not self.s3_client:
            return None
        
        try:
            filename = os.path.basename(local_file_path)
            s3_key = f"interviews/{session_id}/{filename}"
            
            self.s3_client.upload_file(
                local_file_path,
                self.s3_bucket,
                s3_key,
                ExtraArgs={'ContentType': 'video/webm'}
            )
            
            # Generate URL
            url = f"https://{self.s3_bucket}.s3.amazonaws.com/{s3_key}"
            
            # Update database
            session = SessionLocal()
            try:
                candidate = session.query(Candidate).filter_by(
                    interview_session_id=session_id
                ).first()
                if candidate:
                    candidate.interview_recording_url = url
                    session.commit()
            finally:
                session.close()
            
            logger.info(f"Uploaded recording to S3: {url}")
            return url
            
        except Exception as e:
            logger.error(f"Error uploading to S3: {e}")
            return None


# Global instance
interview_session_manager = InterviewSessionManager()


# Resume and Job Description Based Knowledge Base Creation
def create_knowledge_base_from_resume_and_job(candidate_id: int) -> str:
    """Create HeyGen knowledge base from resume and job description"""
    session = SessionLocal()
    try:
        candidate = session.query(Candidate).filter_by(id=candidate_id).first()
        if not candidate:
            raise ValueError("Candidate not found")
        
        # Extract resume content
        resume_content = ""
        if candidate.resume_path and os.path.exists(candidate.resume_path):
            # Parse resume (you'll need a resume parser like pypdf2 or python-docx)
            resume_content = extract_resume_content(candidate.resume_path)
        
        # Prepare knowledge base content
        kb_name = f"Interview_{candidate.name}_{candidate.job_title}_{datetime.now().strftime('%Y%m%d')}"
        
        # Create interview questions based on resume and job description
        interview_questions = generate_interview_questions(
            resume_content=resume_content,
            job_description=candidate.job_description or "",
            job_title=candidate.job_title
        )
        
        # Create custom prompt for HeyGen
        custom_prompt = f"""
        You are conducting a professional interview for {candidate.name} applying for {candidate.job_title}.
        
        Resume Summary: {resume_content[:1000]}...
        
        Job Requirements: {candidate.job_description}
        
        Interview Questions to Ask:
        {json.dumps(interview_questions, indent=2)}
        
        Instructions:
        - Be professional and friendly
        - Ask follow-up questions based on answers
        - Assess technical skills, experience, and cultural fit
        - Keep the interview conversational
        - Show genuine interest in their responses
        """
        
        # Call HeyGen API to create knowledge base
        heygen_key = os.getenv('HEYGEN_API_KEY')
        if heygen_key:
            import requests
            
            response = requests.post(
                'https://api.heygen.com/v1/streaming/knowledge_base',
                headers={
                    'X-Api-Key': heygen_key,
                    'Content-Type': 'application/json'
                },
                json={
                    'name': kb_name,
                    'custom_prompt': custom_prompt,
                    'opening_line': f"Hello {candidate.name}, welcome to your interview for the {candidate.job_title} position. I'm excited to learn more about your experience and skills.",
                    'useful_links': [candidate.resume_path] if candidate.resume_path else []
                }
            )
            
            if response.status_code == 200:
                kb_data = response.json()
                kb_id = kb_data['data']['knowledge_base_id']
                
                # Update candidate record
                candidate.knowledge_base_id = kb_id
                candidate.interview_kb_id = kb_id
                session.commit()
                
                logger.info(f"Created knowledge base {kb_id} for candidate {candidate_id}")
                return kb_id
        
        # Fallback KB ID
        fallback_kb_id = f"kb_{candidate_id}_{int(time.time())}"
        candidate.knowledge_base_id = fallback_kb_id
        candidate.interview_kb_id = fallback_kb_id
        session.commit()
        
        return fallback_kb_id
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating knowledge base: {e}")
        raise
    finally:
        session.close()


def generate_interview_questions(resume_content: str, job_description: str, job_title: str) -> List[Dict]:
    """Generate interview questions based on resume and job description"""
    questions = []
    
    # Standard opening questions
    questions.extend([
        {
            "type": "opening",
            "question": "Can you tell me about yourself and your professional journey?",
            "category": "general",
            "expected_duration": 120
        },
        {
            "type": "motivation",
            "question": f"What interests you about this {job_title} position?",
            "category": "general",
            "expected_duration": 90
        }
    ])
    
    # Technical questions based on job description
    if "python" in job_description.lower() or "python" in resume_content.lower():
        questions.append({
            "type": "technical",
            "question": "Can you describe your experience with Python and any significant projects you've built?",
            "category": "technical",
            "expected_duration": 120
        })
    
    if "react" in job_description.lower() or "javascript" in job_description.lower():
        questions.append({
            "type": "technical",
            "question": "Tell me about your experience with React and modern JavaScript frameworks.",
            "category": "technical",
            "expected_duration": 120
        })
    
    # Behavioral questions
    questions.extend([
        {
            "type": "behavioral",
            "question": "Can you describe a challenging technical problem you solved and your approach?",
            "category": "behavioral",
            "expected_duration": 150
        },
        {
            "type": "behavioral",
            "question": "How do you handle working on multiple projects with competing deadlines?",
            "category": "behavioral",
            "expected_duration": 120
        }
    ])
    
    # Role-specific questions
    if "lead" in job_title.lower() or "senior" in job_title.lower():
        questions.append({
            "type": "leadership",
            "question": "Can you share an example of how you've mentored junior team members?",
            "category": "behavioral",
            "expected_duration": 120
        })
    
    # Closing questions
    questions.extend([
        {
            "type": "closing",
            "question": "What questions do you have about the role or our company?",
            "category": "general",
            "expected_duration": 180
        },
        {
            "type": "closing",
            "question": "What are your salary expectations and when would you be available to start?",
            "category": "general",
            "expected_duration": 90
        }
    ])
    
    return questions


def extract_resume_content(resume_path: str) -> str:
    """Extract text content from resume file"""
    try:
        import PyPDF2
        from docx import Document
        
        file_ext = os.path.splitext(resume_path)[1].lower()
        
        if file_ext == '.pdf':
            with open(resume_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
                
        elif file_ext in ['.docx', '.doc']:
            doc = Document(resume_path)
            return "\n".join([paragraph.text for paragraph in doc.paragraphs])
            
        else:
            # Try to read as text
            with open(resume_path, 'r', encoding='utf-8') as file:
                return file.read()
                
    except Exception as e:
        logger.error(f"Error extracting resume content: {e}")
        return "Resume content could not be extracted"