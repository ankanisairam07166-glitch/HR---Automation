# interview_analysis.py - Production Ready Version
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import os
from db import SessionLocal, Candidate
import traceback

# Configure logging
logger = logging.getLogger(__name__)

# Optional OpenAI import with fallback
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available - using fallback analysis")

class InterviewAnalyzer:
    def __init__(self):
        self.openai_key = os.getenv('OPENAI_API_KEY')
        if self.openai_key and OPENAI_AVAILABLE:
            openai.api_key = self.openai_key
            self.use_ai = True
        else:
            self.use_ai = False
            logger.info("Running in fallback mode without OpenAI")
    
    def analyze_interview(self, candidate_id: int) -> Optional[Dict]:
        """Analyze completed interview using stored Q&A pairs with production error handling"""
        session = SessionLocal()
        candidate = None
        
        try:
            # Validate input
            if not isinstance(candidate_id, int) or candidate_id <= 0:
                raise ValueError(f"Invalid candidate_id: {candidate_id}")
            
            candidate = session.query(Candidate).filter_by(id=candidate_id).first()
            if not candidate:
                raise ValueError(f"Candidate {candidate_id} not found")
            
            # Log analysis start
            logger.info(f"Starting interview analysis for {candidate.name} (ID: {candidate_id})")
            
            # Get structured Q&A pairs with multiple fallback strategies
            qa_pairs = self._extract_qa_pairs(candidate)
            
            if not qa_pairs:
                logger.warning(f"No Q&A data found for candidate {candidate_id}")
                # Set status and return None instead of raising exception
                candidate.interview_ai_analysis_status = 'no_data'
                session.commit()
                return None
            
            # Log Q&A data for debugging
            logger.info(f"Analyzing {len(qa_pairs)} Q&A pairs for {candidate.name}")
            
            # Extract resume content safely
            resume_content = self._extract_resume_key_points(candidate)
            
            # Perform analysis with error handling
            analysis = self._perform_detailed_analysis(
                candidate_name=candidate.name,
                position=candidate.job_title or "Unknown Position",
                qa_pairs=qa_pairs,
                transcript=candidate.interview_transcript or "",
                resume_content=resume_content
            )
            
            # Validate analysis results
            if not self._validate_analysis_results(analysis):
                raise ValueError("Invalid analysis results")
            
            # Store analysis results with safe attribute access
            self._store_analysis_results(candidate, analysis, session)
            
            # Commit transaction
            session.commit()
            logger.info(f"✅ AI analysis completed for {candidate.name} - Score: {analysis['overall_score']}")
            
            return analysis
            
        except Exception as e:
            # Rollback transaction
            session.rollback()
            
            # Log detailed error
            logger.error(f"Error analyzing interview for candidate {candidate_id}: {str(e)}", exc_info=True)
            
            # Update status to failed if candidate exists
            if candidate:
                try:
                    candidate.interview_ai_analysis_status = 'failed'
                    candidate.interview_ai_analysis_error = str(e)[:500]  # Store error message (truncated)
                    session.commit()
                except:
                    logger.error("Failed to update candidate status after error")
            
            # Don't raise in production - return None
            return None
            
        finally:
            session.close()
    
    def _extract_qa_pairs(self, candidate) -> List[Dict]:
        """Extract Q&A pairs with multiple fallback strategies"""
        qa_pairs = []
        
        # Strategy 1: Try structured Q&A pairs
        try:
            if hasattr(candidate, 'interview_qa_pairs'):
                qa_pairs_data = getattr(candidate, 'interview_qa_pairs', '[]')
                if qa_pairs_data:
                    qa_pairs = json.loads(qa_pairs_data)
                    if qa_pairs:
                        logger.info("Using structured Q&A pairs")
                        return qa_pairs
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Failed to parse interview_qa_pairs: {e}")
        
        # Strategy 2: Reconstruct from separate arrays
        try:
            questions = json.loads(candidate.interview_questions_asked or '[]')
            answers = json.loads(candidate.interview_answers_given or '[]')
            
            if questions:
                qa_pairs = []
                for i, question in enumerate(questions):
                    qa_pair = {
                        'question': question.get('text', '') if isinstance(question, dict) else str(question),
                        'answer': '',
                        'question_timestamp': question.get('timestamp', '') if isinstance(question, dict) else '',
                        'answer_timestamp': ''
                    }
                    
                    # Match with answer if available
                    if i < len(answers):
                        answer = answers[i]
                        qa_pair['answer'] = answer.get('text', '') if isinstance(answer, dict) else str(answer)
                        qa_pair['answer_timestamp'] = answer.get('timestamp', '') if isinstance(answer, dict) else ''
                    
                    qa_pairs.append(qa_pair)
                
                logger.info(f"Reconstructed {len(qa_pairs)} Q&A pairs from separate arrays")
                return qa_pairs
                
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Failed to parse questions/answers: {e}")
        
        # Strategy 3: Parse from transcript if available
        if candidate.interview_transcript:
            try:
                qa_pairs = self._parse_qa_from_transcript(candidate.interview_transcript)
                if qa_pairs:
                    logger.info(f"Extracted {len(qa_pairs)} Q&A pairs from transcript")
                    return qa_pairs
            except Exception as e:
                logger.warning(f"Failed to parse transcript: {e}")
        
        return qa_pairs
    
    def _parse_qa_from_transcript(self, transcript: str) -> List[Dict]:
        """Parse Q&A pairs from transcript text"""
        qa_pairs = []
        lines = transcript.strip().split('\n')
        
        current_question = None
        current_answer = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect AI/Interviewer lines (questions)
            if any(marker in line for marker in ['[AI]:', '[Interviewer]:', 'AI:', 'Question:']):
                # Save previous Q&A pair if exists
                if current_question and current_answer:
                    qa_pairs.append({
                        'question': current_question,
                        'answer': ' '.join(current_answer),
                        'question_timestamp': '',
                        'answer_timestamp': ''
                    })
                
                # Extract question text
                for marker in ['[AI]:', '[Interviewer]:', 'AI:', 'Question:']:
                    if marker in line:
                        current_question = line.split(marker, 1)[1].strip()
                        break
                current_answer = []
            
            # Detect Candidate lines (answers)
            elif any(marker in line for marker in ['[Candidate]:', '[User]:', 'Candidate:', 'Answer:']):
                for marker in ['[Candidate]:', '[User]:', 'Candidate:', 'Answer:']:
                    if marker in line:
                        answer_text = line.split(marker, 1)[1].strip()
                        if answer_text:
                            current_answer.append(answer_text)
                        break
            
            # Continue collecting answer text
            elif current_question and not line.startswith('['):
                current_answer.append(line)
        
        # Save last Q&A pair
        if current_question and current_answer:
            qa_pairs.append({
                'question': current_question,
                'answer': ' '.join(current_answer),
                'question_timestamp': '',
                'answer_timestamp': ''
            })
        
        return qa_pairs
    
    def _perform_detailed_analysis(self, candidate_name: str, position: str, 
                                 qa_pairs: List[Dict], transcript: str, 
                                 resume_content: str) -> Dict:
        """Perform detailed analysis of Q&A pairs with production error handling"""
        try:
            # Use AI analysis if available, otherwise fallback
            if self.use_ai and self.openai_key:
                try:
                    return self._openai_analysis(candidate_name, position, qa_pairs, resume_content)
                except Exception as e:
                    logger.warning(f"OpenAI analysis failed, using fallback: {e}")
                    return self._fallback_analysis(candidate_name, position, qa_pairs, transcript)
            else:
                return self._fallback_analysis(candidate_name, position, qa_pairs, transcript)
                
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            # Return safe default values
            return self._get_default_analysis_result(candidate_name, position)
    
    def _fallback_analysis(self, candidate_name: str, position: str, 
                          qa_pairs: List[Dict], transcript: str) -> Dict:
        """Enhanced fallback analysis with better scoring logic"""
        
        # Define evaluation criteria
        technical_keywords = [
            'python', 'javascript', 'java', 'react', 'angular', 'vue', 'node',
            'database', 'sql', 'api', 'rest', 'graphql', 'algorithm', 'data structure',
            'optimization', 'scalability', 'architecture', 'design pattern', 'testing',
            'deployment', 'ci/cd', 'docker', 'kubernetes', 'aws', 'cloud'
        ]
        
        soft_skills_keywords = [
            'team', 'collaborate', 'communication', 'problem', 'solution', 'challenge',
            'learn', 'adapt', 'feedback', 'improve', 'manage', 'leadership', 'mentor'
        ]
        
        problem_solving_keywords = [
            'solve', 'approach', 'analyze', 'debug', 'optimize', 'troubleshoot',
            'investigate', 'research', 'implement', 'design', 'plan', 'strategy'
        ]
        
        # Initialize scores
        scores = {
            'total': 0,
            'technical': 0,
            'communication': 0,
            'problem_solving': 0,
            'cultural_fit': 0
        }
        
        question_analyses = []
        answered_count = 0
        total_questions = len(qa_pairs)
        
        for i, qa in enumerate(qa_pairs):
            question = qa.get('question', '').lower()
            answer = qa.get('answer', '').lower()
            
            # Skip if no answer
            if not answer or answer == 'no answer provided':
                question_analyses.append({
                    "question": qa.get('question', ''),
                    "answer": "No answer provided",
                    "analysis": "Candidate did not provide an answer",
                    "score": 0
                })
                continue
            
            answered_count += 1
            
            # Analyze answer quality
            analysis_result = self._analyze_single_answer(
                question, answer, 
                technical_keywords, soft_skills_keywords, problem_solving_keywords
            )
            
            question_analyses.append(analysis_result)
            
            # Update scores
            scores['total'] += analysis_result['score']
            
            # Categorize question and update category scores
            if any(term in question for term in ['technical', 'code', 'technology', 'experience with']):
                scores['technical'] += analysis_result['score']
            if any(term in question for term in ['team', 'collaborate', 'tell me about']):
                scores['communication'] += analysis_result['score']
            if any(term in question for term in ['problem', 'challenge', 'difficult']):
                scores['problem_solving'] += analysis_result['score']
            if any(term in question for term in ['why', 'interest', 'goals', 'culture']):
                scores['cultural_fit'] += analysis_result['score']
        
        # Calculate normalized scores
        completion_rate = (answered_count / total_questions * 100) if total_questions > 0 else 0
        
        # Normalize scores (0-100)
        overall_score = self._calculate_overall_score(scores, answered_count, completion_rate)
        technical_score = self._normalize_score(scores['technical'], answered_count, 0, 100)
        communication_score = self._normalize_score(scores['communication'], answered_count, 40, 100)
        problem_solving_score = self._normalize_score(scores['problem_solving'], answered_count, 30, 100)
        cultural_fit_score = self._normalize_score(scores['cultural_fit'], answered_count, 40, 100)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            overall_score, completion_rate, answered_count, total_questions
        )
        
        # Generate comprehensive feedback
        feedback = self._generate_comprehensive_feedback(
            overall_score, technical_score, communication_score,
            answered_count, total_questions, question_analyses
        )
        
        return {
            "overall_score": round(overall_score),
            "technical_score": round(technical_score),
            "communication_score": round(communication_score),
            "problem_solving_score": round(problem_solving_score),
            "cultural_fit_score": round(cultural_fit_score),
            "overall_feedback": feedback,
            "recommendation": recommendation,
            "question_analysis": question_analyses,
            "completion_rate": round(completion_rate),
            "questions_asked": total_questions,
            "questions_answered": answered_count
        }
    
    def _analyze_single_answer(self, question: str, answer: str, 
                              tech_keywords: List[str], soft_keywords: List[str], 
                              problem_keywords: List[str]) -> Dict:
        """Analyze a single answer and return scoring"""
        
        # Base score on answer length and quality
        word_count = len(answer.split())
        
        # Length-based scoring
        if word_count < 10:
            base_score = 3
            length_feedback = "Answer is too brief"
        elif word_count < 30:
            base_score = 5
            length_feedback = "Answer could be more detailed"
        elif word_count < 100:
            base_score = 7
            length_feedback = "Good answer length"
        else:
            base_score = 8
            length_feedback = "Comprehensive answer"
        
        # Keyword bonus scoring
        tech_matches = sum(1 for kw in tech_keywords if kw in answer)
        soft_matches = sum(1 for kw in soft_keywords if kw in answer)
        problem_matches = sum(1 for kw in problem_keywords if kw in answer)
        
        # Calculate bonus
        keyword_bonus = min(2, (tech_matches * 0.3 + soft_matches * 0.2 + problem_matches * 0.3))
        
        # Structure and clarity bonus
        structure_bonus = 0
        if '.' in answer and len(answer.split('.')) > 2:  # Multiple sentences
            structure_bonus += 0.5
        if any(indicator in answer for indicator in ['first', 'second', 'finally', 'example']):
            structure_bonus += 0.5
        
        # Calculate final score
        final_score = min(10, base_score + keyword_bonus + structure_bonus)
        
        # Generate analysis feedback
        feedback_parts = [length_feedback]
        
        if tech_matches > 0:
            feedback_parts.append(f"Demonstrates technical knowledge ({tech_matches} technical terms)")
        if soft_matches > 0:
            feedback_parts.append(f"Shows soft skills awareness")
        if problem_matches > 0:
            feedback_parts.append(f"Good problem-solving approach")
        
        return {
            "question": question,
            "answer": answer[:200] + "..." if len(answer) > 200 else answer,
            "analysis": ". ".join(feedback_parts),
            "score": round(final_score, 1)
        }
    
    def _calculate_overall_score(self, scores: Dict, answered_count: int, completion_rate: float) -> float:
        """Calculate overall score with weighted factors"""
        if answered_count == 0:
            return 0
        
        # Base score from answers
        base_score = (scores['total'] / answered_count) * 10
        
        # Completion bonus/penalty
        completion_factor = 1.0
        if completion_rate >= 90:
            completion_factor = 1.1
        elif completion_rate >= 80:
            completion_factor = 1.0
        elif completion_rate >= 60:
            completion_factor = 0.9
        else:
            completion_factor = 0.8
        
        return min(100, base_score * completion_factor)
    
    def _normalize_score(self, raw_score: float, count: int, min_score: float, max_score: float) -> float:
        """Normalize score to a range with minimum threshold"""
        if count == 0:
            return min_score
        
        normalized = (raw_score / count) * 10
        return min(max_score, max(min_score, min_score + normalized))
    
    def _generate_recommendation(self, overall_score: float, completion_rate: float, 
                               answered: int, total: int) -> str:
        """Generate recommendation based on multiple factors"""
        if overall_score >= 75 and completion_rate >= 80:
            return "Strongly Recommended"
        elif overall_score >= 60 and completion_rate >= 70:
            return "Recommended"
        elif overall_score >= 45 or completion_rate >= 60:
            return "Needs Further Review"
        else:
            return "Not Recommended"
    
    def _generate_comprehensive_feedback(self, overall: float, technical: float, 
                                       communication: float, answered: int, 
                                       total: int, analyses: List[Dict]) -> str:
        """Generate detailed feedback"""
        completion_rate = (answered / total * 100) if total > 0 else 0
        
        feedback = f"**Interview Performance Summary**\n\n"
        feedback += f"Overall Score: {overall:.0f}/100\n"
        feedback += f"Questions Answered: {answered}/{total} ({completion_rate:.0f}%)\n\n"
        
        feedback += "**Category Scores:**\n"
        feedback += f"- Technical Skills: {technical:.0f}/100\n"
        feedback += f"- Communication: {communication:.0f}/100\n\n"
        
        feedback += "**Performance Analysis:**\n"
        
        # Overall performance
        if overall >= 80:
            feedback += "Excellent interview performance. The candidate demonstrated strong competencies across all areas. "
        elif overall >= 60:
            feedback += "Good interview performance with room for improvement in some areas. "
        else:
            feedback += "Below average performance with significant areas needing improvement. "
        
        # Technical assessment
        if technical >= 70:
            feedback += "Technical skills appear solid with good understanding of relevant technologies. "
        elif technical >= 50:
            feedback += "Technical skills are adequate but could benefit from deeper expertise. "
        else:
            feedback += "Technical skills need significant improvement. "
        
        # Communication assessment
        if communication >= 70:
            feedback += "Communication was clear and effective throughout the interview. "
        else:
            feedback += "Communication skills need enhancement for better clarity. "
        
        # Completion assessment
        if completion_rate < 70:
            feedback += f"\n\nNote: Candidate only answered {completion_rate:.0f}% of questions, which may impact assessment accuracy."
        
        # Add top strengths and weaknesses
        feedback += "\n\n**Key Observations:**\n"
        
        # Find best and worst answers
        sorted_analyses = sorted(analyses, key=lambda x: x['score'], reverse=True)
        
        if sorted_analyses and sorted_analyses[0]['score'] > 7:
            feedback += f"- Strongest response: {sorted_analyses[0]['analysis']}\n"
        
        if sorted_analyses and sorted_analyses[-1]['score'] < 5:
            feedback += f"- Area for improvement: {sorted_analyses[-1]['analysis']}\n"
        
        return feedback
    
    def _store_analysis_results(self, candidate, analysis: Dict, session) -> None:
        """Safely store analysis results with error handling"""
        try:
            # Store main scores with safe attribute setting
            safe_attrs = {
                'interview_ai_score': analysis.get('overall_score', 0),
                'interview_ai_technical_score': analysis.get('technical_score', 0),
                'interview_ai_communication_score': analysis.get('communication_score', 0),
                'interview_ai_problem_solving_score': analysis.get('problem_solving_score', 0),
                'interview_ai_cultural_fit_score': analysis.get('cultural_fit_score', 0),
                'interview_ai_overall_feedback': analysis.get('overall_feedback', ''),
                'interview_ai_analysis_status': 'completed',
                'interview_final_status': analysis.get('recommendation', 'Needs Review'),
                'interview_ai_analysis_timestamp': datetime.now()
            }
            
            for attr, value in safe_attrs.items():
                if hasattr(candidate, attr):
                    setattr(candidate, attr, value)
            
            # Store question analysis as JSON
            if hasattr(candidate, 'interview_ai_questions_analysis'):
                candidate.interview_ai_questions_analysis = json.dumps(
                    analysis.get('question_analysis', []),
                    ensure_ascii=False
                )
            
            # Store detailed analysis if field exists
            if hasattr(candidate, 'interview_detailed_analysis'):
                detailed_data = {
                    'analysis': analysis,
                    'analyzed_at': datetime.now().isoformat(),
                    'analyzer_version': '2.0',
                    'method': 'ai' if self.use_ai else 'fallback'
                }
                candidate.interview_detailed_analysis = json.dumps(
                    detailed_data,
                    ensure_ascii=False
                )
            
        except Exception as e:
            logger.error(f"Error storing analysis results: {e}")
            # Don't raise - we can still return the analysis even if storage fails
    
    def _validate_analysis_results(self, analysis: Dict) -> bool:
        """Validate that analysis results are within expected ranges"""
        try:
            # Check required fields
            required_fields = [
                'overall_score', 'technical_score', 'communication_score',
                'problem_solving_score', 'cultural_fit_score', 'recommendation'
            ]
            
            for field in required_fields:
                if field not in analysis:
                    logger.error(f"Missing required field: {field}")
                    return False
            
            # Check score ranges
            score_fields = [
                'overall_score', 'technical_score', 'communication_score',
                'problem_solving_score', 'cultural_fit_score'
            ]
            
            for field in score_fields:
                score = analysis.get(field, 0)
                if not isinstance(score, (int, float)) or score < 0 or score > 100:
                    logger.error(f"Invalid score for {field}: {score}")
                    return False
            
            # Check recommendation
            valid_recommendations = [
                "Strongly Recommended", "Recommended", 
                "Needs Further Review", "Not Recommended"
            ]
            
            if analysis.get('recommendation') not in valid_recommendations:
                logger.error(f"Invalid recommendation: {analysis.get('recommendation')}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False
    
    def _get_default_analysis_result(self, candidate_name: str, position: str) -> Dict:
        """Return safe default analysis result"""
        return {
            "overall_score": 0,
            "technical_score": 0,
            "communication_score": 0,
            "problem_solving_score": 0,
            "cultural_fit_score": 0,
            "overall_feedback": f"Analysis could not be completed for {candidate_name}. Manual review recommended.",
            "recommendation": "Needs Further Review",
            "question_analysis": [],
            "completion_rate": 0,
            "questions_asked": 0,
            "questions_answered": 0
        }
    
    def _extract_resume_key_points(self, candidate) -> str:
        """Safely extract key points from resume"""
        try:
            key_points = []
            
            # Add basic info
            if candidate.job_title:
                key_points.append(f"Position: {candidate.job_title}")
            if candidate.ats_score:
                key_points.append(f"ATS Score: {candidate.ats_score}")
            
            # Try to extract from resume file if available
            if hasattr(candidate, 'resume_path') and candidate.resume_path:
                # This would integrate with your resume extraction logic
                # For now, just note that resume exists
                key_points.append("Resume available for review")
            
            return " | ".join(key_points) if key_points else "No resume data available"
            
        except Exception as e:
            logger.error(f"Error extracting resume points: {e}")
            return "Resume extraction failed"
    
    def _openai_analysis(self, candidate_name: str, position: str, 
                        qa_pairs: List[Dict], resume_content: str) -> Dict:
        """OpenAI analysis with production error handling"""
        try:
            # Prepare prompt
            qa_text = "\n\n".join([
                f"Q: {qa['question']}\nA: {qa.get('answer', 'No answer provided')}"
                for qa in qa_pairs[:20]  # Limit to prevent token overflow
            ])
            
            prompt = f"""
            Analyze this technical interview for {position} position.
            
            Candidate: {candidate_name}
            Resume: {resume_content[:500]}
            
            Interview Q&A:
            {qa_text}
            
            Provide a JSON analysis with these exact fields:
            {{
                "overall_score": (0-100),
                "technical_score": (0-100),
                "communication_score": (0-100),
                "problem_solving_score": (0-100),
                "cultural_fit_score": (0-100),
                "overall_feedback": "detailed feedback string",
                "recommendation": "Strongly Recommended|Recommended|Needs Further Review|Not Recommended",
                "question_analysis": [
                    {{"question": "text", "answer": "text", "analysis": "feedback", "score": (0-10)}}
                ]
            }}
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert technical interviewer. Provide analysis in valid JSON format only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            # Parse response
            result_text = response.choices[0].message.content.strip()
            
            # Extract JSON if wrapped in markdown
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(result_text)
            
            # Validate and return
            if self._validate_analysis_results(result):
                return result
            else:
                logger.warning("OpenAI returned invalid results, using fallback")
                return self._fallback_analysis(candidate_name, position, qa_pairs, "")
                
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            return self._fallback_analysis(candidate_name, position, qa_pairs, "")


# Background task function
def analyze_pending_interviews():
    """Find and analyze all pending interview analyses with production error handling"""
    analyzer = InterviewAnalyzer()
    session = SessionLocal()
    
    try:
        # Find completed interviews without analysis
        pending = session.query(Candidate).filter(
            Candidate.interview_completed_at.isnot(None),
            Candidate.interview_ai_analysis_status.in_([None, 'pending', 'failed'])
        ).limit(10).all()  # Process in batches
        
        logger.info(f"Found {len(pending)} interviews pending analysis")
        
        success_count = 0
        failed_count = 0
        
        for candidate in pending:
            try:
                # Mark as processing
                candidate.interview_ai_analysis_status = 'processing'
                session.commit()
                
                # Analyze
                result = analyzer.analyze_interview(candidate.id)
                
                if result:
                    success_count += 1
                    logger.info(f"✅ Analyzed interview for {candidate.name} (ID: {candidate.id})")
                else:
                    failed_count += 1
                    logger.warning(f"⚠️ No result for {candidate.name} (ID: {candidate.id})")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to analyze interview for {candidate.name}: {e}")
                
                # Don't let one failure stop the whole batch
                continue
        
        logger.info(f"Batch complete: {success_count} successful, {failed_count} failed")
        
    except Exception as e:
        logger.error(f"Error in analyze_pending_interviews: {e}", exc_info=True)
    finally:
        session.close()


# Utility function for manual analysis
def analyze_specific_interview(candidate_id: int) -> Optional[Dict]:
    """Manually trigger analysis for a specific interview"""
    analyzer = InterviewAnalyzer()
    return analyzer.analyze_interview(candidate_id)