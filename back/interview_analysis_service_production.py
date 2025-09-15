# interview_analysis_service_production.py
import json
import time
import logging
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum
import queue
import os
import re

from db import SessionLocal, Candidate
from sqlalchemy.exc import SQLAlchemyError
from flask_caching import Cache

logger = logging.getLogger(__name__)

class AnalysisStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    INVALID = "invalid"
    RETRY = "retry"

@dataclass
class AnalysisTask:
    candidate_id: int
    priority: int = 5
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class ProductionInterviewAnalysisService:
    """Production-ready interview analysis service with strict validation"""
    
    def __init__(self, cache: Cache = None, max_workers: int = 4):
        self.cache = cache
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.analysis_queue = queue.PriorityQueue()
        self.is_running = False
        self.monitor_thread = None
        self.worker_threads = []
        self.failed_analyses = {}
        self.completed_analyses = set()
        self._lock = threading.Lock()
        
        # Configuration
        self.config = {
            'monitor_interval': int(os.getenv('ANALYSIS_MONITOR_INTERVAL', '30')),
            'max_retries': int(os.getenv('ANALYSIS_MAX_RETRIES', '3')),
            'retry_delay': int(os.getenv('ANALYSIS_RETRY_DELAY', '300')),
            'stale_threshold': int(os.getenv('ANALYSIS_STALE_THRESHOLD', '3600')),
            'batch_size': int(os.getenv('ANALYSIS_BATCH_SIZE', '10')),
            'min_questions': int(os.getenv('MIN_INTERVIEW_QUESTIONS', '5')),
            'min_valid_answers': int(os.getenv('MIN_VALID_ANSWERS', '5')),
            'min_answer_length': int(os.getenv('MIN_ANSWER_LENGTH', '30')),
            'min_word_count': int(os.getenv('MIN_WORD_COUNT', '5')),
            'validity_threshold': float(os.getenv('VALIDITY_THRESHOLD', '0.7'))
        }
        
        # Invalid response patterns - CRITICAL FOR YOUR ISSUE
        self.invalid_patterns = [
            'INIT_INTERVIEW', 'TEST', 'TEST_RESPONSE', 'undefined', 'null',
            '[object Object]', 'lorem ipsum', 'START_INTERVIEW', 'END_INTERVIEW',
            'NEXT_QUESTION', 'SKIP', 'test answer', 'sample response',
            'No answer provided'  # Add this to catch empty answers
        ]
        
        # Technical keywords for scoring
        self.technical_keywords = [
            'implement', 'develop', 'design', 'architecture', 'algorithm',
            'database', 'api', 'framework', 'optimize', 'scale', 'debug',
            'testing', 'deployment', 'version control', 'git', 'agile',
            'code', 'programming', 'software', 'function', 'class', 'module',
            'performance', 'security', 'authentication', 'integration'
        ]
        
        # Soft skill keywords
        self.soft_skill_keywords = [
            'team', 'collaborate', 'communicate', 'lead', 'manage',
            'problem', 'solution', 'challenge', 'learn', 'adapt',
            'deadline', 'priority', 'stakeholder', 'conflict', 'feedback',
            'mentor', 'present', 'document', 'plan', 'organize'
        ]
    
    def start(self):
        """Start the analysis service"""
        if self.is_running:
            logger.warning("Analysis service already running")
            return
            
        self.is_running = True
        
        # Start monitor thread
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            name="AnalysisMonitor",
            daemon=True
        )
        self.monitor_thread.start()
        
        # Start worker threads
        for i in range(2):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"AnalysisWorker-{i}",
                daemon=True
            )
            worker.start()
            self.worker_threads.append(worker)
            
        logger.info(f"Interview Analysis Service started with {len(self.worker_threads)} workers")
    
    def stop(self):
        """Stop the analysis service gracefully"""
        logger.info("Stopping Interview Analysis Service...")
        self.is_running = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
            
        for worker in self.worker_threads:
            worker.join(timeout=5)
            
        self.executor.shutdown(wait=True)
        logger.info("Interview Analysis Service stopped")
    
    def _monitor_loop(self):
        """Monitor for interviews needing analysis"""
        while self.is_running:
            try:
                self._check_pending_interviews()
                self._check_stale_analyses()
                self._retry_failed_analyses()
            except Exception as e:
                logger.error(f"Monitor loop error: {e}", exc_info=True)
            
            time.sleep(self.config['monitor_interval'])
    
    def _worker_loop(self):
        """Process analysis tasks from queue"""
        while self.is_running:
            try:
                priority, task = self.analysis_queue.get(timeout=5)
                if task:
                    self._process_analysis_task(task)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Worker loop error: {e}", exc_info=True)
    
    def _check_pending_interviews(self):
        """Check for interviews that need analysis"""
        session = SessionLocal()
        try:
            candidates = session.query(Candidate).filter(
                Candidate.interview_completed_at.isnot(None),
                Candidate.interview_ai_analysis_status.is_(None) | 
                (Candidate.interview_ai_analysis_status == AnalysisStatus.PENDING.value),
                Candidate.interview_auto_score_triggered == False
            ).limit(self.config['batch_size']).all()
            
            for candidate in candidates:
                if candidate.id in self.completed_analyses:
                    continue
                    
                candidate.interview_auto_score_triggered = True
                session.commit()
                
                task = AnalysisTask(
                    candidate_id=candidate.id,
                    priority=self._calculate_priority(candidate)
                )
                self.analysis_queue.put((task.priority, task))
                logger.info(f"Queued analysis for candidate {candidate.id} ({candidate.name})")
                
        except SQLAlchemyError as e:
            logger.error(f"Database error in pending check: {e}")
            session.rollback()
        finally:
            session.close()
    
    def _check_stale_analyses(self):
        """Check for analyses stuck in processing"""
        session = SessionLocal()
        try:
            stale_time = datetime.now() - timedelta(seconds=self.config['stale_threshold'])
            
            stale_candidates = session.query(Candidate).filter(
                Candidate.interview_ai_analysis_status == AnalysisStatus.PROCESSING.value,
                Candidate.interview_analysis_started_at < stale_time
            ).all()
            
            for candidate in stale_candidates:
                logger.warning(f"Found stale analysis for candidate {candidate.id}")
                candidate.interview_ai_analysis_status = AnalysisStatus.RETRY.value
                candidate.interview_auto_score_triggered = False
                session.commit()
                
        except SQLAlchemyError as e:
            logger.error(f"Database error in stale check: {e}")
        finally:
            session.close()
    
    def _retry_failed_analyses(self):
        """Retry failed analyses after delay"""
        current_time = datetime.now()
        
        with self._lock:
            retry_candidates = []
            for candidate_id, failure_info in list(self.failed_analyses.items()):
                if current_time - failure_info['failed_at'] > timedelta(seconds=self.config['retry_delay']):
                    if failure_info['retry_count'] < self.config['max_retries']:
                        retry_candidates.append(candidate_id)
                        del self.failed_analyses[candidate_id]
            
        for candidate_id in retry_candidates:
            task = AnalysisTask(
                candidate_id=candidate_id,
                priority=1,
                retry_count=self.failed_analyses.get(candidate_id, {}).get('retry_count', 0) + 1
            )
            self.analysis_queue.put((task.priority, task))
            logger.info(f"Retrying analysis for candidate {candidate_id}")
    
    def _calculate_priority(self, candidate) -> int:
        """Calculate task priority (lower = higher priority)"""
        priority = 5
        if candidate.interview_completed_at:
            hours_ago = (datetime.now() - candidate.interview_completed_at).total_seconds() / 3600
            if hours_ago < 1:
                priority = 1
            elif hours_ago < 6:
                priority = 3
        return priority
    
    def _process_analysis_task(self, task: AnalysisTask):
        """Process a single analysis task"""
        logger.info(f"Processing analysis for candidate {task.candidate_id}")
        
        session = SessionLocal()
        try:
            candidate = session.query(Candidate).filter_by(id=task.candidate_id).first()
            
            if not candidate:
                logger.error(f"Candidate {task.candidate_id} not found")
                return
            
            # Update status
            candidate.interview_ai_analysis_status = AnalysisStatus.PROCESSING.value
            candidate.interview_analysis_started_at = datetime.now()
            session.commit()
            
            # Perform analysis
            analysis_result = self._perform_analysis(candidate)
            
            if analysis_result:
                self._save_analysis_results(candidate, analysis_result, session)
                
                with self._lock:
                    self.completed_analyses.add(task.candidate_id)
                
                self._send_realtime_update(task.candidate_id, analysis_result)
                
                logger.info(f"Analysis completed for candidate {task.candidate_id}: {analysis_result['overall_score']}%")
            else:
                raise Exception("Analysis returned no results")
                
        except Exception as e:
            logger.error(f"Analysis failed for candidate {task.candidate_id}: {e}", exc_info=True)
            
            if candidate:
                candidate.interview_ai_analysis_status = AnalysisStatus.FAILED.value
                session.commit()
            
            with self._lock:
                self.failed_analyses[task.candidate_id] = {
                    'failed_at': datetime.now(),
                    'retry_count': task.retry_count,
                    'error': str(e)
                }
        finally:
            session.close()
    
    def _validate_interview_responses(self, qa_pairs: List[Dict]) -> Tuple[bool, str]:
        """
        STRICT VALIDATION - THIS IS THE KEY FIX
        Returns: (is_valid, reason)
        """
        
        if not qa_pairs:
            return False, "No Q&A data available"
        
        # Check minimum questions requirement
        if len(qa_pairs) < self.config['min_questions']:
            return False, f"Interview has only {len(qa_pairs)} questions (minimum: {self.config['min_questions']})"
        
        valid_responses = 0
        invalid_responses = []
        total_questions = len(qa_pairs)
        
        for i, qa in enumerate(qa_pairs, 1):
            answer = qa.get('answer', '').strip()
            
            # CRITICAL CHECK - Empty or missing answers
            if not answer or answer == "No answer provided":
                invalid_responses.append(f"Q{i}: No answer provided")
                logger.warning(f"Q{i}: Empty answer detected")
                continue
            
            # Check minimum length
            if len(answer) < self.config['min_answer_length']:
                invalid_responses.append(f"Q{i}: Answer too short ({len(answer)} chars)")
                logger.warning(f"Q{i}: Short answer: {answer[:50]}...")
                continue
            
            # CRITICAL CHECK - Test/invalid patterns
            answer_lower = answer.lower()
            invalid_pattern_found = False
            for pattern in self.invalid_patterns:
                if pattern.lower() in answer_lower:
                    invalid_responses.append(f"Q{i}: Contains invalid pattern '{pattern}'")
                    logger.warning(f"Q{i}: Invalid pattern '{pattern}' found in: {answer[:50]}...")
                    invalid_pattern_found = True
                    break
            
            if invalid_pattern_found:
                continue
            
            # Check if answer has actual content (not just special chars/numbers)
            if not any(c.isalpha() for c in answer):
                invalid_responses.append(f"Q{i}: No alphabetic content")
                logger.warning(f"Q{i}: No alphabetic content in: {answer[:50]}...")
                continue
            
            # Check minimum word count
            word_count = len(answer.split())
            if word_count < self.config['min_word_count']:
                invalid_responses.append(f"Q{i}: Too few words ({word_count})")
                logger.warning(f"Q{i}: Too few words: {answer[:50]}...")
                continue
            
            # Check for repetitive/spam content
            unique_words = set(answer.lower().split())
            if len(unique_words) < 3:
                invalid_responses.append(f"Q{i}: Repetitive content")
                logger.warning(f"Q{i}: Repetitive content: {answer[:50]}...")
                continue
            
            # This answer passed all checks
            valid_responses += 1
            logger.info(f"Q{i}: Valid answer ({len(answer)} chars)")
        
        # Calculate validity rate
        validity_rate = (valid_responses / total_questions) if total_questions > 0 else 0
        
        logger.info(f"Validation complete: {valid_responses}/{total_questions} valid answers ({validity_rate:.1%})")
        
        # Check if interview meets validity requirements
        if valid_responses < self.config['min_valid_answers']:
            reason = f"Only {valid_responses} valid answers (minimum: {self.config['min_valid_answers']}). Issues: {'; '.join(invalid_responses[:3])}"
            logger.warning(f"INVALID INTERVIEW: {reason}")
            return False, reason
        
        if validity_rate < self.config['validity_threshold']:
            reason = f"Validity rate {validity_rate:.1%} below threshold {self.config['validity_threshold']:.0%}. Issues: {'; '.join(invalid_responses[:3])}"
            logger.warning(f"INVALID INTERVIEW: {reason}")
            return False, reason
        
        return True, f"{valid_responses}/{total_questions} valid answers"
    
    def _perform_analysis(self, candidate) -> Optional[Dict[str, Any]]:
        """Perform the actual analysis with strict validation"""
        try:
            # Parse Q&A data
            qa_pairs = self._parse_qa_data_safely(candidate)
            
            logger.info(f"Analyzing {len(qa_pairs)} Q&A pairs for candidate {candidate.id}")
            
            # CRITICAL: Validate responses first
            is_valid, validation_reason = self._validate_interview_responses(qa_pairs)
            
            if not is_valid:
                logger.warning(f"Invalid interview for candidate {candidate.id}: {validation_reason}")
                # THIS IS THE FIX - Return 0 scores for invalid interviews
                return self._generate_invalid_interview_result(validation_reason, qa_pairs)
            
            # Only proceed with scoring if valid
            logger.info(f"Interview validated successfully for candidate {candidate.id}")
            
            # Try AI analysis if available
            if self._has_ai_capability():
                try:
                    return self._analyze_with_ai_production(qa_pairs, candidate)
                except Exception as e:
                    logger.warning(f"AI analysis failed, using rule-based: {e}")
            
            # Fallback to rule-based analysis
            return self._analyze_with_rules_production(qa_pairs, candidate)
            
        except Exception as e:
            logger.error(f"Analysis error: {e}", exc_info=True)
            return self._generate_error_result(str(e))
    
    def _parse_qa_data_safely(self, candidate) -> List[Dict]:
        """Safely parse Q&A data from multiple sources"""
        qa_pairs = []
        
        # Try parsing qa_pairs field first
        if candidate.interview_qa_pairs:
            try:
                parsed = json.loads(candidate.interview_qa_pairs)
                if isinstance(parsed, list) and parsed:
                    logger.info(f"Parsed {len(parsed)} Q&A pairs from interview_qa_pairs field")
                    return parsed
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse qa_pairs for candidate {candidate.id}: {e}")
        
        # Try parsing separate questions/answers
        try:
            questions = json.loads(candidate.interview_questions_asked or '[]')
            answers = json.loads(candidate.interview_answers_given or '[]')
            
            logger.info(f"Found {len(questions)} questions and {len(answers)} answers")
            
            for i, question in enumerate(questions):
                qa_pair = {
                    'question': question.get('text', '') if isinstance(question, dict) else str(question),
                    'answer': '',
                    'timestamp': question.get('timestamp') if isinstance(question, dict) else None,
                    'order': i + 1
                }
                
                if i < len(answers):
                    answer = answers[i]
                    qa_pair['answer'] = answer.get('text', '') if isinstance(answer, dict) else str(answer)
                
                qa_pairs.append(qa_pair)
                
        except Exception as e:
            logger.error(f"Failed to parse questions/answers: {e}")
        
        logger.info(f"Total Q&A pairs parsed: {len(qa_pairs)}")
        return qa_pairs
    
    def _has_ai_capability(self) -> bool:
        """Check if AI analysis is available"""
        return bool(os.getenv('OPENAI_API_KEY') or os.getenv('ANTHROPIC_API_KEY'))
    
    def _analyze_with_ai_production(self, qa_pairs: List[Dict], candidate) -> Dict[str, Any]:
        """Production AI analysis with OpenAI"""
        import openai
        
        openai.api_key = os.getenv('OPENAI_API_KEY')
        
        qa_text = self._format_qa_for_ai(qa_pairs)
        prompt = self._create_ai_prompt(qa_text, candidate)
        
        try:
            for attempt in range(3):
                try:
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": self._get_system_prompt()},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3,
                        max_tokens=1500,
                        timeout=30
                    )
                    
                    content = response.choices[0].message.content
                    result = self._parse_ai_response(content)
                    
                    if result:
                        result['method'] = 'ai-gpt3.5'
                        result['confidence'] = 0.95
                        return result
                        
                except Exception as e:
                    if attempt < 2:
                        time.sleep(2 ** attempt)
                    else:
                        raise
                        
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            raise
    
    def _analyze_with_rules_production(self, qa_pairs: List[Dict], candidate) -> Dict[str, Any]:
        """Enhanced rule-based analysis for production"""
        metrics = self._calculate_interview_metrics(qa_pairs)
        scores = self._calculate_scores_from_metrics(metrics, candidate)
        insights = self._generate_insights_from_metrics(metrics, scores)
        feedback = self._generate_comprehensive_feedback(metrics, scores, insights, candidate)
        
        return {
            'technical_score': scores['technical'],
            'communication_score': scores['communication'],
            'problem_solving_score': scores['problem_solving'],
            'cultural_fit_score': scores['cultural_fit'],
            'overall_score': scores['overall'],
            'strengths': insights['strengths'],
            'weaknesses': insights['weaknesses'],
            'recommendations': insights['recommendations'],
            'feedback': feedback,
            'confidence': 0.75,
            'method': 'rule-based-v2'
        }
    
    def _calculate_interview_metrics(self, qa_pairs: List[Dict]) -> Dict[str, Any]:
        """Calculate detailed interview metrics"""
        total_questions = len(qa_pairs)
        answered_questions = sum(1 for qa in qa_pairs if qa.get('answer'))
        
        answer_lengths = [len(qa.get('answer', '')) for qa in qa_pairs if qa.get('answer')]
        avg_answer_length = sum(answer_lengths) / len(answer_lengths) if answer_lengths else 0
        
        all_answers = ' '.join([qa.get('answer', '') for qa in qa_pairs]).lower()
        technical_keyword_count = sum(1 for kw in self.technical_keywords if kw in all_answers)
        soft_keyword_count = sum(1 for kw in self.soft_skill_keywords if kw in all_answers)
        
        technical_questions_answered = 0
        behavioral_questions_answered = 0
        
        for qa in qa_pairs:
            if qa.get('answer'):
                question_lower = qa.get('question', '').lower()
                if any(kw in question_lower for kw in ['technical', 'code', 'implement', 'design']):
                    technical_questions_answered += 1
                elif any(kw in question_lower for kw in ['team', 'challenge', 'situation', 'describe']):
                    behavioral_questions_answered += 1
        
        return {
            'total_questions': total_questions,
            'answered_questions': answered_questions,
            'completion_rate': (answered_questions / total_questions * 100) if total_questions > 0 else 0,
            'avg_answer_length': avg_answer_length,
            'min_answer_length': min(answer_lengths) if answer_lengths else 0,
            'max_answer_length': max(answer_lengths) if answer_lengths else 0,
            'technical_keyword_count': technical_keyword_count,
            'soft_keyword_count': soft_keyword_count,
            'technical_questions_answered': technical_questions_answered,
            'behavioral_questions_answered': behavioral_questions_answered,
            'answer_quality_score': self._calculate_answer_quality_score(qa_pairs)
        }
    
    def _calculate_answer_quality_score(self, qa_pairs: List[Dict]) -> float:
        """Calculate quality score for answers"""
        if not qa_pairs:
            return 0.0
            
        quality_scores = []
        
        for qa in qa_pairs:
            answer = qa.get('answer', '')
            if not answer:
                quality_scores.append(0)
                continue
                
            score = 50  # Base score
            
            # Length bonus
            length = len(answer)
            if length > 200:
                score += 20
            elif length > 100:
                score += 10
            elif length < 30:
                score -= 20
                
            # Structure bonus
            sentences = answer.count('.') + answer.count('!') + answer.count('?')
            if sentences > 3:
                score += 10
            elif sentences > 1:
                score += 5
                
            # Specificity bonus
            if any(char.isdigit() for char in answer):
                score += 5
            if answer.count(',') > 2:
                score += 5
                
            quality_scores.append(min(100, max(0, score)))
        
        return sum(quality_scores) / len(quality_scores) if quality_scores else 0
    
    def _calculate_scores_from_metrics(self, metrics: Dict, candidate) -> Dict[str, float]:
        """Calculate final scores from metrics with lower base scores"""
        technical_score = 30  # Lower base score - THIS IS IMPORTANT
        communication_score = 30
        problem_solving_score = 30
        cultural_fit_score = 30
        
        # Technical score
        technical_score += min(30, metrics['completion_rate'] * 0.3)
        technical_score += min(20, metrics['technical_keyword_count'] * 2)
        technical_score += min(20, metrics['answer_quality_score'] * 0.2)
        
        # Communication score
        communication_score += min(30, metrics['completion_rate'] * 0.3)
        communication_score += min(25, (metrics['avg_answer_length'] / 8))
        communication_score += min(15, metrics['soft_keyword_count'] * 2)
        
        # Problem solving score
        problem_solving_score += min(30, metrics['behavioral_questions_answered'] * 6)
        problem_solving_score += min(25, metrics['answer_quality_score'] * 0.25)
        problem_solving_score += min(15, metrics['completion_rate'] * 0.15)
        
        # Cultural fit score
        cultural_fit_score += min(30, metrics['completion_rate'] * 0.3)
        cultural_fit_score += min(25, metrics['soft_keyword_count'] * 3)
        cultural_fit_score += min(15, (metrics['answered_questions'] / metrics['total_questions'] * 15) if metrics['total_questions'] > 0 else 0)
        
        scores = {
            'technical': min(100, max(0, technical_score)),
            'communication': min(100, max(0, communication_score)),
            'problem_solving': min(100, max(0, problem_solving_score)),
            'cultural_fit': min(100, max(0, cultural_fit_score))
        }
        
        scores['overall'] = (
            scores['technical'] * 0.35 +
            scores['communication'] * 0.25 +
            scores['problem_solving'] * 0.25 +
            scores['cultural_fit'] * 0.15
        )
        
        return scores
    
    def _generate_insights_from_metrics(self, metrics: Dict, scores: Dict) -> Dict[str, List[str]]:
        """Generate insights based on metrics and scores"""
        strengths = []
        weaknesses = []
        recommendations = []
        
        # Completion rate
        if metrics['completion_rate'] >= 95:
            strengths.append("Excellent interview completion - answered all questions thoroughly")
        elif metrics['completion_rate'] >= 80:
            strengths.append("Good interview engagement with high completion rate")
        elif metrics['completion_rate'] < 60:
            weaknesses.append("Low completion rate indicates potential communication issues")
            
        # Answer quality
        if metrics['avg_answer_length'] > 150:
            strengths.append("Provided detailed and comprehensive responses")
        elif metrics['avg_answer_length'] < 50:
            weaknesses.append("Responses were too brief and lacked detail")
            recommendations.append("Encourage more detailed responses in future interviews")
            
        # Technical skills
        if metrics['technical_keyword_count'] >= 8:
            strengths.append("Strong technical vocabulary and domain knowledge")
        elif metrics['technical_keyword_count'] < 3:
            weaknesses.append("Limited technical terminology in responses")
            
        # Soft skills
        if metrics['soft_keyword_count'] >= 6:
            strengths.append("Good emphasis on teamwork and collaboration")
        elif metrics['soft_keyword_count'] < 2:
            weaknesses.append("Minimal focus on soft skills and team dynamics")
            
        # Score-based recommendations
        if scores['overall'] >= 75:
            recommendations.append("Strong candidate - proceed to next round")
        elif scores['overall'] >= 60:
            recommendations.append("Promising candidate - consider for technical assessment")
        else:
            recommendations.append("May not be suitable for current role requirements")
            
        if scores['technical'] < 60:
            recommendations.append("Additional technical screening recommended")
        if scores['communication'] < 60:
            recommendations.append("Communication skills assessment needed")
            
        return {
            'strengths': strengths[:3],
            'weaknesses': weaknesses[:3],
            'recommendations': recommendations[:3]
        }
    
    def _generate_comprehensive_feedback(self, metrics: Dict, scores: Dict, 
                                        insights: Dict, candidate) -> str:
        """Generate detailed feedback report"""
        feedback = f"""
INTERVIEW ANALYSIS REPORT
========================
Candidate: {candidate.name}
Position: {candidate.job_title}
Date: {datetime.now().strftime('%Y-%m-%d')}

EXECUTIVE SUMMARY
-----------------
Overall Score: {scores['overall']:.1f}/100
Recommendation: {'Highly Recommended' if scores['overall'] >= 75 else 'Recommended' if scores['overall'] >= 60 else 'Not Recommended'}

DETAILED SCORES
---------------
- Technical Skills: {scores['technical']:.1f}/100
- Communication: {scores['communication']:.1f}/100
- Problem Solving: {scores['problem_solving']:.1f}/100
- Cultural Fit: {scores['cultural_fit']:.1f}/100

INTERVIEW METRICS
-----------------
- Questions Answered: {metrics['answered_questions']}/{metrics['total_questions']}
- Completion Rate: {metrics['completion_rate']:.1f}%
- Average Response Length: {metrics['avg_answer_length']:.0f} characters
- Answer Quality Score: {metrics['answer_quality_score']:.1f}/100

KEY STRENGTHS
-------------
{chr(10).join(f'• {s}' for s in insights['strengths']) if insights['strengths'] else '• No significant strengths identified'}

AREAS FOR IMPROVEMENT
---------------------
{chr(10).join(f'• {w}' for w in insights['weaknesses']) if insights['weaknesses'] else '• No major weaknesses identified'}

RECOMMENDATIONS
---------------
{chr(10).join(f'• {r}' for r in insights['recommendations']) if insights['recommendations'] else '• Standard evaluation process'}

FINAL ASSESSMENT
----------------
Based on the comprehensive analysis, this candidate is {'highly recommended' if scores['overall'] >= 75 else 'recommended with reservations' if scores['overall'] >= 60 else 'not recommended'} 
for the {candidate.job_title} position.
"""
        return feedback.strip()
    
    def _generate_invalid_interview_result(self, reason: str, qa_pairs: List[Dict]) -> Dict[str, Any]:
        """THIS IS THE KEY METHOD - Returns 0 scores for invalid interviews"""
        # Get details about what went wrong
        total_questions = len(qa_pairs)
        answered_questions = sum(1 for qa in qa_pairs if qa.get('answer'))
        
        # Identify specific issues
        issues = []
        for i, qa in enumerate(qa_pairs, 1):
            answer = qa.get('answer', '').strip()
            if not answer:
                issues.append(f"Q{i}: No answer")
            elif any(pattern in answer.upper() for pattern in ['INIT_INTERVIEW', 'TEST']):
                issues.append(f"Q{i}: Test/system response detected")
            elif len(answer) < 20:
                issues.append(f"Q{i}: Too brief ({len(answer)} chars)")
        
        logger.warning(f"Generating invalid interview result: {reason}")
        logger.warning(f"Issues found: {issues[:5]}")
        
        return {
            'technical_score': 0,  # ZERO SCORE
            'communication_score': 0,  # ZERO SCORE
            'problem_solving_score': 0,  # ZERO SCORE
            'cultural_fit_score': 0,  # ZERO SCORE
            'overall_score': 0,  # ZERO SCORE - THIS IS WHAT YOU NEED
            'strengths': [],
            'weaknesses': [
                f'Interview validation failed: {reason}',
                f'Only {answered_questions}/{total_questions} questions answered',
                'Invalid or test responses detected'
            ],
            'recommendations': [
                'Schedule a new interview session',
                'Ensure candidate provides complete responses',
                'Verify interview system is working correctly'
            ],
            'feedback': f"""
INTERVIEW INVALID - RESCHEDULE REQUIRED
========================================
Reason: {reason}

Questions Attempted: {answered_questions}/{total_questions}
Issues Found: {', '.join(issues[:5])}

This interview session contains invalid data and cannot be scored.
Please schedule a new interview with the candidate.
""",
            'confidence': 0,
            'method': 'invalid_interview'
        }
    
    def _generate_error_result(self, error_msg: str) -> Dict[str, Any]:
        """Generate result for analysis error"""
        return {
            'technical_score': 0,
            'communication_score': 0,
            'problem_solving_score': 0,
            'cultural_fit_score': 0,
            'overall_score': 0,
            'strengths': [],
            'weaknesses': ['Analysis could not be completed'],
            'recommendations': ['Manual review required'],
            'feedback': f'Analysis Error: {error_msg}',
            'confidence': 0,
            'method': 'error'
        }
    
    def _save_analysis_results(self, candidate, results: Dict, session):
        """Save analysis results to database"""
        try:
            # Update scores
            candidate.interview_ai_score = results['overall_score']
            candidate.interview_ai_technical_score = results['technical_score']
            candidate.interview_ai_communication_score = results['communication_score']
            candidate.interview_ai_problem_solving_score = results['problem_solving_score']
            candidate.interview_ai_cultural_fit_score = results['cultural_fit_score']
            
            # Update feedback and metadata
            candidate.interview_ai_overall_feedback = results['feedback']
            candidate.interview_confidence_score = results['confidence']
            candidate.interview_scoring_method = results['method']
            
            # Store insights as JSON
            candidate.interview_strengths = json.dumps(results.get('strengths', []))
            candidate.interview_weaknesses = json.dumps(results.get('weaknesses', []))
            candidate.interview_recommendations = json.dumps(results.get('recommendations', []))
            
            # Update status - CRITICAL: Set correct status for invalid interviews
            if results['method'] == 'invalid_interview':
                candidate.interview_ai_analysis_status = AnalysisStatus.INVALID.value
                candidate.interview_final_status = 'Invalid'
                candidate.final_status = 'Interview Invalid - Reschedule Required'
                logger.warning(f"Marked interview as INVALID for candidate {candidate.id}")
            else:
                candidate.interview_ai_analysis_status = AnalysisStatus.COMPLETED.value
                candidate.interview_analysis_completed_at = datetime.now()
                
                # Set final status based on score
                if results['overall_score'] >= 70:
                    candidate.interview_final_status = 'Passed'
                    candidate.final_status = 'Interview Passed - Recommended'
                elif results['overall_score'] >= 50:
                    candidate.interview_final_status = 'Review'
                    candidate.final_status = 'Interview Review Required'
                else:
                    candidate.interview_final_status = 'Failed'
                    candidate.final_status = 'Interview Failed'
            
            session.commit()
            
            logger.info(f"Saved analysis results for candidate {candidate.id}: Score={results['overall_score']}, Status={candidate.interview_final_status}")
            
            # Clear caches
            if self.cache:
                self.cache.delete(f"candidate_{candidate.id}")
                self.cache.delete("interview_results")
                
        except Exception as e:
            logger.error(f"Error saving analysis results: {e}")
            session.rollback()
            raise
    
    def _send_realtime_update(self, candidate_id: int, results: Dict):
        """Send real-time update for frontend"""
        try:
            update_data = {
                'candidate_id': candidate_id,
                'status': 'analysis_complete',
                'scores': {
                    'overall': results['overall_score'],
                    'technical': results['technical_score'],
                    'communication': results['communication_score'],
                    'problem_solving': results['problem_solving_score'],
                    'cultural_fit': results['cultural_fit_score']
                },
                'final_status': results.get('method') == 'invalid_interview' and 'Invalid' or (
                    'Passed' if results['overall_score'] >= 70 else 'Failed'
                ),
                'recommendation': results.get('recommendations', [''])[0] if results.get('recommendations') else '',
                'timestamp': datetime.now().isoformat(),
                'method': results.get('method', 'unknown')
            }
            
            if self.cache:
                self.cache.set(
                    f"interview_update_{candidate_id}", 
                    json.dumps(update_data), 
                    timeout=300
                )
                
            logger.info(f"Sent real-time update for candidate {candidate_id}")
            
        except Exception as e:
            logger.error(f"Error sending real-time update: {e}")
    
    def _format_qa_for_ai(self, qa_pairs: List[Dict]) -> str:
        """Format Q&A pairs for AI analysis"""
        formatted_qa = []
        
        for i, qa in enumerate(qa_pairs, 1):
            question = qa.get('question', 'Unknown question')
            answer = qa.get('answer', 'No answer provided')
            
            formatted_qa.append(f"""
Question {i}: {question}
Answer: {answer}
""")
        
        return "\n".join(formatted_qa)
    
    def _create_ai_prompt(self, qa_text: str, candidate) -> str:
        """Create comprehensive AI analysis prompt"""
        return f"""
Analyze this technical interview for the {candidate.job_title} position.

IMPORTANT: Score based on ACTUAL content quality. If answers are test responses, invalid, or too brief, score should be 0-30%.

CANDIDATE: {candidate.name}

INTERVIEW TRANSCRIPT:
{qa_text}

Evaluation Criteria:
1. Technical Skills: Domain knowledge, technical accuracy, depth of understanding
2. Communication: Clarity, structure, articulation of ideas
3. Problem Solving: Analytical thinking, approach to challenges
4. Cultural Fit: Team collaboration, values alignment, soft skills
5. Overall: Weighted average (35% technical, 25% communication, 25% problem-solving, 15% cultural)

SCORING GUIDELINES:
- 0-30%: Invalid responses, test data, or extremely brief answers
- 31-50%: Poor quality responses, significant gaps
- 51-70%: Adequate responses with room for improvement
- 71-85%: Good quality responses, meets requirements
- 86-100%: Exceptional responses with specific examples

Return JSON with these exact keys:
{{
  "technical_skills": <number 0-100>,
  "communication_skills": <number 0-100>,
  "problem_solving": <number 0-100>,
  "cultural_fit": <number 0-100>,
  "overall_score": <number 0-100>,
  "strengths": ["strength1", "strength2", "strength3"],
  "areas_for_improvement": ["area1", "area2", "area3"],
  "recommendations": ["rec1", "rec2", "rec3"],
  "feedback": "detailed feedback paragraph"
}}
"""
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for AI"""
        return """You are an expert technical interviewer evaluating candidates for software engineering positions. 
Provide fair, unbiased assessments based solely on interview performance.
Be critical when responses are invalid, test data, or lack substance.
Score invalid/test responses very low (0-30%).
Always respond with valid JSON format as requested."""
    
    def _parse_ai_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse AI response safely"""
        try:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                
                required_fields = ['technical_skills', 'communication_skills', 
                                 'problem_solving', 'cultural_fit', 'overall_score']
                
                if all(field in data for field in required_fields):
                    return {
                        'technical_score': float(data.get('technical_skills', 0)),
                        'communication_score': float(data.get('communication_skills', 0)),
                        'problem_solving_score': float(data.get('problem_solving', 0)),
                        'cultural_fit_score': float(data.get('cultural_fit', 0)),
                        'overall_score': float(data.get('overall_score', 0)),
                        'strengths': data.get('strengths', [])[:3],
                        'weaknesses': data.get('areas_for_improvement', [])[:3],
                        'recommendations': data.get('recommendations', [])[:3],
                        'feedback': data.get('feedback', 'No detailed feedback provided')
                    }
                    
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            
        return None
    
    def analyze_single_interview(self, candidate_id: int) -> bool:
        """Manually trigger analysis for a specific candidate"""
        try:
            task = AnalysisTask(
                candidate_id=candidate_id,
                priority=0
            )
            self.analysis_queue.put((task.priority, task))
            logger.info(f"Manually queued analysis for candidate {candidate_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error queuing manual analysis: {e}")
            return False
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        with self._lock:
            stats = {
                'is_running': self.is_running,
                'queue_size': self.analysis_queue.qsize(),
                'completed_analyses': len(self.completed_analyses),
                'failed_analyses': len(self.failed_analyses),
                'worker_threads': len([t for t in self.worker_threads if t.is_alive()]),
                'config': self.config
            }
        return stats

# Initialize service
interview_analysis_service = ProductionInterviewAnalysisService(cache=None)