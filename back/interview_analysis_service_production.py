# interview_analysis_service_production.py
import json
import time
import logging
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum
import queue
import os

from db import SessionLocal, Candidate
from sqlalchemy.exc import SQLAlchemyError
from flask_caching import Cache

logger = logging.getLogger(__name__)

class AnalysisStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
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
    """Production-ready interview analysis service with reliability features"""
    
    def __init__(self, cache: Cache, max_workers: int = 4):
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
            'retry_delay': int(os.getenv('ANALYSIS_RETRY_DELAY', '300')),  # 5 minutes
            'stale_threshold': int(os.getenv('ANALYSIS_STALE_THRESHOLD', '3600')),  # 1 hour
            'batch_size': int(os.getenv('ANALYSIS_BATCH_SIZE', '10')),
        }
        
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
        for i in range(2):  # 2 dedicated worker threads
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"AnalysisWorker-{i}",
                daemon=True
            )
            worker.start()
            self.worker_threads.append(worker)
            
        logger.info(f"✅ Interview Analysis Service started with {len(self.worker_threads)} workers")
    
    def stop(self):
        """Stop the analysis service gracefully"""
        logger.info("Stopping Interview Analysis Service...")
        self.is_running = False
        
        # Wait for threads to finish
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
            
        for worker in self.worker_threads:
            worker.join(timeout=5)
            
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        logger.info("✅ Interview Analysis Service stopped")
    
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
                # Get task with timeout
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
            # Find completed interviews without analysis
            candidates = session.query(Candidate).filter(
                Candidate.interview_completed_at.isnot(None),
                Candidate.interview_ai_analysis_status.is_(None) | 
                (Candidate.interview_ai_analysis_status == AnalysisStatus.PENDING.value),
                Candidate.interview_auto_score_triggered == False
            ).limit(self.config['batch_size']).all()
            
            for candidate in candidates:
                # Skip if already in queue or completed
                if candidate.id in self.completed_analyses:
                    continue
                    
                # Mark as triggered
                candidate.interview_auto_score_triggered = True
                session.commit()
                
                # Add to queue
                task = AnalysisTask(
                    candidate_id=candidate.id,
                    priority=self._calculate_priority(candidate)
                )
                self.analysis_queue.put((task.priority, task))
                
                logger.info(f"📋 Queued analysis for candidate {candidate.id} ({candidate.name})")
                
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
                
                # Reset status
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
                priority=1,  # High priority for retries
                retry_count=self.failed_analyses.get(candidate_id, {}).get('retry_count', 0) + 1
            )
            self.analysis_queue.put((task.priority, task))
            logger.info(f"🔄 Retrying analysis for candidate {candidate_id}")
    
    def _calculate_priority(self, candidate) -> int:
        """Calculate task priority (lower = higher priority)"""
        priority = 5  # Default
        
        # Prioritize based on completion time
        if candidate.interview_completed_at:
            hours_ago = (datetime.now() - candidate.interview_completed_at).total_seconds() / 3600
            if hours_ago < 1:
                priority = 1
            elif hours_ago < 6:
                priority = 3
        
        return priority
    
    def _process_analysis_task(self, task: AnalysisTask):
        """Process a single analysis task"""
        logger.info(f"🔍 Processing analysis for candidate {task.candidate_id}")
        
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
                # Update candidate with results
                self._save_analysis_results(candidate, analysis_result, session)
                
                # Mark as completed
                with self._lock:
                    self.completed_analyses.add(task.candidate_id)
                
                # Send real-time update
                self._send_realtime_update(task.candidate_id, analysis_result)
                
                logger.info(f"✅ Analysis completed for candidate {task.candidate_id}: {analysis_result['overall_score']}%")
            else:
                raise Exception("Analysis returned no results")
                
        except Exception as e:
            logger.error(f"Analysis failed for candidate {task.candidate_id}: {e}", exc_info=True)
            
            # Update failure status
            if candidate:
                candidate.interview_ai_analysis_status = AnalysisStatus.FAILED.value
                session.commit()
            
            # Track failure
            with self._lock:
                self.failed_analyses[task.candidate_id] = {
                    'failed_at': datetime.now(),
                    'retry_count': task.retry_count,
                    'error': str(e)
                }
                
        finally:
            session.close()

    def _validate_interview_responses(self, qa_pairs: List[Dict]) -> bool:
        """Validate that interview has real responses, not just test data"""
        
        if not qa_pairs:
            return False
        
        valid_responses = 0
        total_questions = len(qa_pairs)
        
        for qa in qa_pairs:
            answer = qa.get('answer', '').strip()
            
            # Check if answer is meaningful
            if answer and len(answer) > 5:
                # Check it's not a test response
                invalid_patterns = ['INIT_INTERVIEW', 'TEST', 'undefined', 'null']
                if not any(pattern in answer for pattern in invalid_patterns):
                    valid_responses += 1
        
        # Require at least 30% valid responses for scoring
        return (valid_responses / total_questions) >= 0.3 if total_questions > 0 else False

    
    def _perform_analysis(self, candidate) -> Optional[Dict[str, Any]]:
        """Perform the actual analysis with validation"""
        try:
            # Parse Q&A data
            qa_pairs = self._parse_qa_data_safely(candidate)
            
            # CRITICAL: Validate responses first
            if not self._validate_interview_responses(qa_pairs):
                logger.warning(f"No valid responses for candidate {candidate.id}")
                return {
                    'technical_score': 0,
                    'communication_score': 0,
                    'problem_solving_score': 0,
                    'cultural_fit_score': 0,
                    'overall_score': 0,
                    'strengths': [],
                    'weaknesses': ['No valid responses provided', 'Interview incomplete'],
                    'recommendations': ['Schedule new interview'],
                    'feedback': 'Interview incomplete - no valid responses were provided.',
                    'confidence': 0,
                    'method': 'no_responses'
                }
            
            # Now perform actual analysis only if we have valid responses
            if self._has_ai_capability():
                try:
                    return self._analyze_with_ai_production(qa_pairs, candidate)
                except Exception as e:
                    logger.warning(f"AI analysis failed, falling back to rules: {e}")
            
            return self._analyze_with_rules_production(qa_pairs, candidate)
            
        except Exception as e:
            logger.error(f"Analysis error: {e}", exc_info=True)
            return None
    
    def _parse_qa_data_safely(self, candidate) -> List[Dict]:
        """Safely parse Q&A data from multiple sources"""
        qa_pairs = []
        
        # Try parsing qa_pairs field
        if candidate.interview_qa_pairs:
            try:
                parsed = json.loads(candidate.interview_qa_pairs)
                if isinstance(parsed, list) and parsed:
                    return parsed
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse qa_pairs for candidate {candidate.id}")
        
        # Try parsing separate questions/answers
        try:
            questions = json.loads(candidate.interview_questions_asked or '[]')
            answers = json.loads(candidate.interview_answers_given or '[]')
            
            for i, question in enumerate(questions):
                qa_pair = {
                    'question': question.get('text', '') if isinstance(question, dict) else str(question),
                    'answer': '',
                    'timestamp': question.get('timestamp') if isinstance(question, dict) else None,
                    'order': i + 1
                }
                
                # Match with answer
                if i < len(answers):
                    answer = answers[i]
                    qa_pair['answer'] = answer.get('text', '') if isinstance(answer, dict) else str(answer)
                
                qa_pairs.append(qa_pair)
                
        except Exception as e:
            logger.error(f"Failed to parse questions/answers: {e}")
        
        return qa_pairs
    
    def _has_ai_capability(self) -> bool:
        """Check if AI analysis is available"""
        return bool(os.getenv('OPENAI_API_KEY') or os.getenv('ANTHROPIC_API_KEY'))
    
    def _analyze_with_ai_production(self, qa_pairs: List[Dict], candidate) -> Dict[str, Any]:
        """Production AI analysis with proper error handling"""
        import openai
        
        openai.api_key = os.getenv('OPENAI_API_KEY')
        
        # Prepare Q&A text
        qa_text = self._format_qa_for_ai(qa_pairs)
        
        # Create prompt
        prompt = self._create_ai_prompt(qa_text, candidate)
        
        try:
            # Call OpenAI with retry logic
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
                    
                    # Parse response
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
        # Calculate comprehensive metrics
        metrics = self._calculate_interview_metrics(qa_pairs)
        
        # Calculate scores
        scores = self._calculate_scores_from_metrics(metrics, candidate)
        
        # Generate insights
        insights = self._generate_insights_from_metrics(metrics, scores)
        
        # Generate feedback
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
            'method': 'rule-based-v2',
            'metrics': metrics  # Include for debugging
        }
    
    def _calculate_interview_metrics(self, qa_pairs: List[Dict]) -> Dict[str, Any]:
        """Calculate detailed interview metrics"""
        total_questions = len(qa_pairs)
        answered_questions = sum(1 for qa in qa_pairs if qa.get('answer'))
        
        # Answer lengths
        answer_lengths = [len(qa.get('answer', '')) for qa in qa_pairs if qa.get('answer')]
        avg_answer_length = sum(answer_lengths) / len(answer_lengths) if answer_lengths else 0
        
        # Keywords analysis
        technical_keywords = ['implement', 'develop', 'design', 'architecture', 'algorithm', 
                             'database', 'api', 'framework', 'optimize', 'scale']
        soft_keywords = ['team', 'collaborate', 'communicate', 'lead', 'manage', 
                        'problem', 'solution', 'challenge', 'learn', 'adapt']
        
        all_answers = ' '.join([qa.get('answer', '') for qa in qa_pairs]).lower()
        technical_keyword_count = sum(1 for kw in technical_keywords if kw in all_answers)
        soft_keyword_count = sum(1 for kw in soft_keywords if kw in all_answers)
        
        # Question-specific analysis
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
            'total_answer_length': sum(answer_lengths),
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
            elif length < 20:
                score -= 20
                
            # Structure bonus (sentences, punctuation)
            sentences = answer.count('.') + answer.count('!') + answer.count('?')
            if sentences > 3:
                score += 10
            elif sentences > 1:
                score += 5
                
            # Specificity bonus
            if any(char.isdigit() for char in answer):  # Contains numbers
                score += 5
            if answer.count(',') > 2:  # Lists or detailed points
                score += 5
                
            quality_scores.append(min(100, max(0, score)))
        
        return sum(quality_scores) / len(quality_scores) if quality_scores else 0
    
    def _calculate_scores_from_metrics(self, metrics: Dict, candidate) -> Dict[str, float]:
        """Calculate final scores from metrics"""
        # Base scores
        technical_score = 40
        communication_score = 40
        problem_solving_score = 40
        cultural_fit_score = 40
        
        # Technical score calculation
        technical_score += min(30, metrics['completion_rate'] * 0.3)
        technical_score += min(15, metrics['technical_keyword_count'] * 3)
        technical_score += min(15, metrics['answer_quality_score'] * 0.15)
        
        # Communication score
        communication_score += min(30, metrics['completion_rate'] * 0.3)
        communication_score += min(20, (metrics['avg_answer_length'] / 10))
        communication_score += min(10, metrics['soft_keyword_count'] * 2)
        
        # Problem solving score
        problem_solving_score += min(25, metrics['behavioral_questions_answered'] * 5)
        problem_solving_score += min(25, metrics['answer_quality_score'] * 0.25)
        problem_solving_score += min(10, metrics['completion_rate'] * 0.1)
        
        # Cultural fit score
        cultural_fit_score += min(30, metrics['completion_rate'] * 0.3)
        cultural_fit_score += min(20, metrics['soft_keyword_count'] * 3)
        cultural_fit_score += min(10, (metrics['answered_questions'] / metrics['total_questions'] * 10) if metrics['total_questions'] > 0 else 0)
        
        # Ensure scores are within bounds
        scores = {
            'technical': min(100, max(0, technical_score)),
            'communication': min(100, max(0, communication_score)),
            'problem_solving': min(100, max(0, problem_solving_score)),
            'cultural_fit': min(100, max(0, cultural_fit_score))
        }
        
        # Calculate weighted overall score
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
        
        # Completion rate insights
        if metrics['completion_rate'] >= 95:
            strengths.append("Excellent interview completion - answered all questions thoroughly")
        elif metrics['completion_rate'] >= 80:
            strengths.append("Good interview engagement with high completion rate")
        elif metrics['completion_rate'] < 60:
            weaknesses.append("Low completion rate indicates potential communication issues")
            
        # Answer quality insights
        if metrics['avg_answer_length'] > 150:
            strengths.append("Provided detailed and comprehensive responses")
        elif metrics['avg_answer_length'] < 50:
            weaknesses.append("Responses were too brief and lacked detail")
            recommendations.append("Encourage more detailed responses in future interviews")
            
        # Technical insights
        if metrics['technical_keyword_count'] >= 8:
            strengths.append("Strong technical vocabulary and domain knowledge")
        elif metrics['technical_keyword_count'] < 3:
            weaknesses.append("Limited technical terminology in responses")
            
        # Soft skills insights
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
            
        # Specific area recommendations
        if scores['technical'] < 60:
            recommendations.append("Additional technical screening recommended")
        if scores['communication'] < 60:
            recommendations.append("Communication skills assessment needed")
            
        return {
            'strengths': strengths[:3],  # Top 3
            'weaknesses': weaknesses[:3],  # Top 3
            'recommendations': recommendations[:3]  # Top 3
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
{chr(10).join(f'• {s}' for s in insights['strengths'])}

AREAS FOR IMPROVEMENT
---------------------
{chr(10).join(f'• {w}' for w in insights['weaknesses'])}

RECOMMENDATIONS
---------------
{chr(10).join(f'• {r}' for r in insights['recommendations'])}

TECHNICAL ASSESSMENT
--------------------
The candidate demonstrated {'strong' if scores['technical'] >= 70 else 'moderate' if scores['technical'] >= 50 else 'limited'} technical knowledge 
with {metrics['technical_keyword_count']} technical references in their responses.

COMMUNICATION ASSESSMENT
------------------------
Communication skills were {'excellent' if scores['communication'] >= 80 else 'good' if scores['communication'] >= 60 else 'adequate' if scores['communication'] >= 40 else 'poor'}, 
with responses averaging {metrics['avg_answer_length']:.0f} characters in length.

FINAL ASSESSMENT
----------------
Based on the comprehensive analysis, this candidate is {'highly recommended' if scores['overall'] >= 75 else 'recommended with reservations' if scores['overall'] >= 60 else 'not recommended'} 
for the {candidate.job_title} position.
"""
        return feedback.strip()
    
    def _generate_incomplete_analysis(self, candidate) -> Dict[str, Any]:
        """Generate analysis for incomplete interviews"""
        return {
            'technical_score': 0,
            'communication_score': 0,
            'problem_solving_score': 0,
            'cultural_fit_score': 0,
            'overall_score': 0,
            'strengths': ["Unable to assess - incomplete interview data"],
            'weaknesses': ["Interview was not completed"],
            'recommendations': ["Schedule a follow-up interview"],
            'feedback': f"Interview for {candidate.name} was incomplete. No Q&A data available for analysis.",
            'confidence': 0.1,
            'method': 'incomplete'
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
            
            # Update status
            candidate.interview_ai_analysis_status = AnalysisStatus.COMPLETED.value
            candidate.interview_analysis_completed_at = datetime.now()
            candidate.interview_auto_score_completed_at = datetime.now()
            
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
            
            # Clear caches
            if self.cache:
                self.cache.delete(f"candidate_{candidate.id}")
                self.cache.delete("interview_results")
                self.cache.delete("interview_results_list")
                
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
                'final_status': 'Passed' if results['overall_score'] >= 70 else 'Failed',
                'recommendation': results.get('recommendations', [''])[0] if results.get('recommendations') else '',
                'timestamp': datetime.now().isoformat(),
                'method': results.get('method', 'unknown')
            }
            
            # Store in cache for polling
            if self.cache:
                self.cache.set(
                    f"interview_update_{candidate_id}", 
                    json.dumps(update_data), 
                    timeout=300
                )
                
                # Also store in a list of recent updates
                recent_updates = self.cache.get("recent_interview_updates") or "[]"
                recent_updates = json.loads(recent_updates)
                recent_updates.append(update_data)
                
                # Keep only last 50 updates
                recent_updates = recent_updates[-50:]
                
                self.cache.set(
                    "recent_interview_updates",
                    json.dumps(recent_updates),
                    timeout=300
                )
                
            logger.info(f"📡 Sent real-time update for candidate {candidate_id}")
            
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
Analyze this technical interview for the {candidate.job_title} position at a technology company.

CANDIDATE: {candidate.name}

INTERVIEW TRANSCRIPT:
{qa_text}

Please provide a comprehensive analysis with the following:

1. SCORES (0-100):
   - technical_skills: Assess technical knowledge and expertise
   - communication_skills: Evaluate clarity and articulation
   - problem_solving: Rate analytical and problem-solving abilities
   - cultural_fit: Assess alignment with collaborative work environment
   - overall_score: Weighted average (35% technical, 25% communication, 25% problem-solving, 15% cultural)

2. KEY STRENGTHS (list 3):
   - Specific positive observations from the interview

3. AREAS FOR IMPROVEMENT (list 3):
   - Specific areas where the candidate could improve

4. RECOMMENDATIONS (list 3):
   - Actionable next steps (e.g., "Proceed to technical round", "Strong hire", "Additional assessment needed")

5. DETAILED FEEDBACK:
   - Comprehensive paragraph summarizing the interview performance

Format your response as a valid JSON object with these exact keys:
{{
  "technical_skills": <number>,
  "communication_skills": <number>,
  "problem_solving": <number>,
  "cultural_fit": <number>,
  "overall_score": <number>,
  "strengths": ["strength1", "strength2", "strength3"],
  "areas_for_improvement": ["area1", "area2", "area3"],
  "recommendations": ["rec1", "rec2", "rec3"],
  "feedback": "detailed feedback paragraph"
}}
"""
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for AI"""
        return """You are an expert technical interviewer with 15+ years of experience evaluating candidates for software engineering positions. 
You provide fair, unbiased, and constructive assessments based solely on interview performance. 
Your evaluations are thorough, professional, and focused on helping make informed hiring decisions.
Always respond with valid JSON format as requested."""
    
    def _parse_ai_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse AI response safely"""
        try:
            # Try to extract JSON from response
            import re
            
            # Look for JSON object
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                
                # Validate required fields
                required_fields = ['technical_skills', 'communication_skills', 
                                 'problem_solving', 'cultural_fit', 'overall_score']
                
                if all(field in data for field in required_fields):
                    # Normalize field names
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
                priority=0  # Highest priority
            )
            self.analysis_queue.put((task.priority, task))
            logger.info(f"📌 Manually queued analysis for candidate {candidate_id}")
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

# Initialize service (will be set with cache in main app)
interview_analysis_service = ProductionInterviewAnalysisService(cache=None)