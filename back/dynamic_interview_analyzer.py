# dynamic_interview_analyzer.py
"""
Production-ready Dynamic Interview Analysis System
Analyzes interview responses in real-time based on actual content
"""

import json
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import hashlib
from textblob import TextBlob
import nltk
from collections import Counter
import numpy as np

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
except:
    pass

logger = logging.getLogger(__name__)

class ResponseQuality(Enum):
    """Quality levels for interview responses"""
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"
    NO_RESPONSE = "no_response"

@dataclass
class AnswerMetrics:
    """Metrics for individual answer analysis"""
    word_count: int
    sentence_count: int
    unique_words: int
    technical_terms: int
    soft_skills_mentioned: int
    examples_provided: int
    structure_score: float
    relevance_score: float
    depth_score: float
    clarity_score: float
    sentiment_score: float
    response_time: float = 0.0

class DynamicInterviewAnalyzer:
    """
    Real-time interview analyzer that evaluates responses dynamically
    based on actual content, not random scores
    """
    
    def __init__(self):
        # Technical keywords by category
        self.technical_keywords = {
            'programming': ['python', 'java', 'javascript', 'c++', 'sql', 'api', 'database', 
                          'algorithm', 'data structure', 'framework', 'library', 'git'],
            'architecture': ['design pattern', 'microservices', 'scalability', 'performance',
                           'optimization', 'cache', 'load balancing', 'distributed'],
            'development': ['agile', 'scrum', 'ci/cd', 'testing', 'debugging', 'deployment',
                          'docker', 'kubernetes', 'cloud', 'aws', 'azure'],
            'ai_ml': ['machine learning', 'deep learning', 'neural network', 'tensorflow',
                     'pytorch', 'nlp', 'computer vision', 'model', 'training']
        }
        
        # Soft skills keywords
        self.soft_skills = {
            'leadership': ['lead', 'mentor', 'guide', 'manage', 'coordinate', 'delegate'],
            'teamwork': ['collaborate', 'team', 'together', 'cooperate', 'support', 'help'],
            'communication': ['explain', 'present', 'discuss', 'communicate', 'articulate'],
            'problem_solving': ['solve', 'analyze', 'troubleshoot', 'debug', 'fix', 'resolve'],
            'learning': ['learn', 'study', 'research', 'explore', 'understand', 'adapt']
        }
        
        # Behavioral indicators
        self.behavioral_indicators = {
            'star_method': ['situation', 'task', 'action', 'result'],
            'specific_examples': ['project', 'worked on', 'implemented', 'developed', 'built'],
            'quantifiable': ['increased', 'decreased', 'improved', 'reduced', '%', 'percent'],
            'time_awareness': ['deadline', 'timeline', 'schedule', 'days', 'weeks', 'months']
        }
        
        # Question type patterns
        self.question_patterns = {
            'technical': r'(implement|code|algorithm|technical|programming|design|architecture)',
            'behavioral': r'(tell me about|describe|situation|time when|example|experience)',
            'situational': r'(what would you|how would you|imagine|scenario|if you)',
            'knowledge': r'(what is|explain|define|difference between|how does)',
            'cultural': r'(why|motivation|interest|team|culture|values|goals)'
        }
    
    def analyze_interview(self, qa_pairs: List[Dict], candidate_info: Dict) -> Dict[str, Any]:
        """
        Main entry point for analyzing interview responses
        
        Args:
            qa_pairs: List of question-answer pairs
            candidate_info: Information about the candidate and position
        
        Returns:
            Comprehensive analysis with scores and feedback
        """
        if not qa_pairs or len(qa_pairs) == 0:
            return self._generate_no_response_analysis()
        
        # Filter out empty responses
        valid_qa_pairs = [qa for qa in qa_pairs if qa.get('answer') and len(qa.get('answer', '').strip()) > 0]
        
        if not valid_qa_pairs:
            return self._generate_no_response_analysis()
        
        # Analyze each Q&A pair
        answer_analyses = []
        for qa in valid_qa_pairs:
            analysis = self._analyze_single_qa(qa, candidate_info)
            answer_analyses.append(analysis)
        
        # Calculate overall scores
        scores = self._calculate_overall_scores(answer_analyses, qa_pairs, candidate_info)
        
        # Generate insights
        insights = self._generate_insights(answer_analyses, scores)
        
        # Generate detailed feedback
        feedback = self._generate_comprehensive_feedback(
            answer_analyses, scores, insights, candidate_info
        )
        
        # Determine final recommendation
        recommendation = self._determine_recommendation(scores, insights)
        
        return {
            'scores': scores,
            'insights': insights,
            'feedback': feedback,
            'recommendation': recommendation,
            'answer_analyses': answer_analyses,
            'metadata': {
                'total_questions': len(qa_pairs),
                'answered_questions': len(valid_qa_pairs),
                'analysis_timestamp': datetime.now().isoformat(),
                'analysis_method': 'dynamic_content_based',
                'confidence': self._calculate_confidence(answer_analyses)
            }
        }
    
    def _analyze_single_qa(self, qa: Dict, candidate_info: Dict) -> Dict:
        """Analyze a single question-answer pair"""
        question = qa.get('question', '')
        answer = qa.get('answer', '')
        
        # Extract metrics
        metrics = self._extract_answer_metrics(answer)
        
        # Determine question type
        question_type = self._identify_question_type(question)
        
        # Calculate quality scores
        quality_scores = self._calculate_quality_scores(answer, question, metrics, question_type)
        
        # Evaluate response quality
        response_quality = self._evaluate_response_quality(metrics, quality_scores)
        
        return {
            'question': question,
            'answer': answer[:200] + '...' if len(answer) > 200 else answer,
            'question_type': question_type,
            'metrics': metrics.__dict__,
            'quality_scores': quality_scores,
            'response_quality': response_quality.value,
            'timestamp': qa.get('timestamp'),
            'response_time': qa.get('response_time', 0)
        }
    
    def _extract_answer_metrics(self, answer: str) -> AnswerMetrics:
        """Extract detailed metrics from an answer"""
        if not answer:
            return AnswerMetrics(0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0)
        
        # Basic text metrics
        words = answer.lower().split()
        sentences = answer.count('.') + answer.count('!') + answer.count('?')
        unique_words = len(set(words))
        
        # Technical terms count
        technical_terms = 0
        for category, keywords in self.technical_keywords.items():
            for keyword in keywords:
                if keyword.lower() in answer.lower():
                    technical_terms += 1
        
        # Soft skills count
        soft_skills = 0
        for category, keywords in self.soft_skills.items():
            for keyword in keywords:
                if keyword.lower() in answer.lower():
                    soft_skills += 1
        
        # Examples and specifics
        examples = 0
        for indicator in self.behavioral_indicators['specific_examples']:
            if indicator.lower() in answer.lower():
                examples += 1
        
        # Structure score (based on STAR method and organization)
        structure_score = self._calculate_structure_score(answer)
        
        # Relevance score (keyword matching and context)
        relevance_score = self._calculate_relevance_score(answer, technical_terms, soft_skills)
        
        # Depth score (detail level and elaboration)
        depth_score = self._calculate_depth_score(len(words), sentences, unique_words, examples)
        
        # Clarity score (readability and coherence)
        clarity_score = self._calculate_clarity_score(answer)
        
        # Sentiment analysis
        try:
            blob = TextBlob(answer)
            sentiment_score = blob.sentiment.polarity  # -1 to 1
        except:
            sentiment_score = 0.0
        
        return AnswerMetrics(
            word_count=len(words),
            sentence_count=max(1, sentences),
            unique_words=unique_words,
            technical_terms=technical_terms,
            soft_skills_mentioned=soft_skills,
            examples_provided=examples,
            structure_score=structure_score,
            relevance_score=relevance_score,
            depth_score=depth_score,
            clarity_score=clarity_score,
            sentiment_score=sentiment_score
        )
    
    def _calculate_structure_score(self, answer: str) -> float:
        """Calculate how well-structured the answer is"""
        score = 50.0  # Base score
        
        # Check for STAR method elements
        star_elements = 0
        for element in self.behavioral_indicators['star_method']:
            if element.lower() in answer.lower():
                star_elements += 1
        score += star_elements * 10
        
        # Check for logical connectors
        connectors = ['first', 'second', 'then', 'finally', 'however', 'therefore', 'because']
        connector_count = sum(1 for c in connectors if c in answer.lower())
        score += min(20, connector_count * 5)
        
        # Check for proper paragraphing (if answer is long enough)
        if len(answer) > 200 and '\n' in answer:
            score += 10
        
        return min(100, score)
    
    def _calculate_relevance_score(self, answer: str, technical_terms: int, soft_skills: int) -> float:
        """Calculate how relevant the answer is"""
        score = 40.0  # Base score
        
        # Technical relevance
        score += min(30, technical_terms * 5)
        
        # Soft skills relevance
        score += min(20, soft_skills * 4)
        
        # Specific examples boost
        if any(word in answer.lower() for word in ['example', 'project', 'experience']):
            score += 10
        
        return min(100, score)
    
    def _calculate_depth_score(self, word_count: int, sentences: int, unique_words: int, examples: int) -> float:
        """Calculate the depth and detail of the answer"""
        score = 0.0
        
        # Word count scoring (optimal range: 50-200 words)
        if word_count < 20:
            score += 10
        elif word_count < 50:
            score += 30
        elif word_count < 100:
            score += 50
        elif word_count < 200:
            score += 40
        else:
            score += 35
        
        # Vocabulary diversity
        if word_count > 0:
            diversity_ratio = unique_words / word_count
            score += min(25, diversity_ratio * 50)
        
        # Examples and specifics
        score += min(25, examples * 10)
        
        return min(100, score)
    
    def _calculate_clarity_score(self, answer: str) -> float:
        """Calculate clarity and readability of the answer"""
        if not answer:
            return 0.0
        
        score = 50.0  # Base score
        
        # Sentence length (optimal: 15-25 words per sentence)
        sentences = answer.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(1, len(sentences))
        
        if 15 <= avg_sentence_length <= 25:
            score += 20
        elif 10 <= avg_sentence_length <= 30:
            score += 10
        
        # Check for clear communication patterns
        clear_patterns = ['my approach', 'i believe', 'in my experience', 'i would']
        clarity_count = sum(1 for p in clear_patterns if p in answer.lower())
        score += min(20, clarity_count * 7)
        
        # Penalize for excessive jargon without explanation
        jargon_penalty = 0
        complex_terms = re.findall(r'\b[A-Z]{2,}\b', answer)  # Acronyms
        if len(complex_terms) > 5:
            jargon_penalty = 10
        score -= jargon_penalty
        
        return max(0, min(100, score))
    
    def _identify_question_type(self, question: str) -> str:
        """Identify the type of question"""
        question_lower = question.lower()
        
        for q_type, pattern in self.question_patterns.items():
            if re.search(pattern, question_lower):
                return q_type
        
        return 'general'
    
    def _calculate_quality_scores(self, answer: str, question: str, 
                                 metrics: AnswerMetrics, question_type: str) -> Dict[str, float]:
        """Calculate quality scores based on question type and answer metrics"""
        scores = {}
        
        if question_type == 'technical':
            # Technical questions focus on accuracy and depth
            scores['technical'] = (
                metrics.technical_terms * 5 +
                metrics.depth_score * 0.4 +
                metrics.clarity_score * 0.2 +
                metrics.structure_score * 0.2
            )
        elif question_type == 'behavioral':
            # Behavioral questions focus on examples and structure
            scores['behavioral'] = (
                metrics.examples_provided * 15 +
                metrics.structure_score * 0.4 +
                metrics.depth_score * 0.3 +
                metrics.soft_skills_mentioned * 5
            )
        elif question_type == 'situational':
            # Situational questions focus on problem-solving approach
            scores['situational'] = (
                metrics.structure_score * 0.4 +
                metrics.clarity_score * 0.3 +
                metrics.depth_score * 0.3
            )
        else:
            # General scoring
            scores['general'] = (
                metrics.relevance_score * 0.4 +
                metrics.clarity_score * 0.3 +
                metrics.depth_score * 0.3
            )
        
        # Normalize scores to 0-100
        for key in scores:
            scores[key] = min(100, max(0, scores[key]))
        
        return scores
    
    def _evaluate_response_quality(self, metrics: AnswerMetrics, 
                                  quality_scores: Dict[str, float]) -> ResponseQuality:
        """Evaluate overall response quality"""
        if metrics.word_count == 0:
            return ResponseQuality.NO_RESPONSE
        
        # Calculate average quality score
        avg_score = sum(quality_scores.values()) / max(1, len(quality_scores))
        
        # Consider multiple factors
        if avg_score >= 80 and metrics.examples_provided > 0:
            return ResponseQuality.EXCELLENT
        elif avg_score >= 60:
            return ResponseQuality.GOOD
        elif avg_score >= 40 or metrics.word_count >= 30:
            return ResponseQuality.AVERAGE
        else:
            return ResponseQuality.POOR
    
    def _calculate_overall_scores(self, answer_analyses: List[Dict], 
                                 all_qa_pairs: List[Dict], 
                                 candidate_info: Dict) -> Dict[str, float]:
        """Calculate overall interview scores"""
        
        # Initialize scores
        scores = {
            'technical': 0,
            'communication': 0,
            'problem_solving': 0,
            'cultural_fit': 0,
            'overall': 0
        }
        
        if not answer_analyses:
            return scores
        
        # Aggregate metrics from all answers
        total_technical_terms = sum(a['metrics']['technical_terms'] for a in answer_analyses)
        total_soft_skills = sum(a['metrics']['soft_skills_mentioned'] for a in answer_analyses)
        total_examples = sum(a['metrics']['examples_provided'] for a in answer_analyses)
        avg_clarity = np.mean([a['metrics']['clarity_score'] for a in answer_analyses])
        avg_depth = np.mean([a['metrics']['depth_score'] for a in answer_analyses])
        avg_structure = np.mean([a['metrics']['structure_score'] for a in answer_analyses])
        
        # Calculate completion rate
        completion_rate = len(answer_analyses) / max(1, len(all_qa_pairs))
        
        # Technical score (based on technical knowledge demonstrated)
        scores['technical'] = self._calculate_technical_score(
            total_technical_terms, avg_depth, answer_analyses
        )
        
        # Communication score (based on clarity and structure)
        scores['communication'] = self._calculate_communication_score(
            avg_clarity, avg_structure, answer_analyses
        )
        
        # Problem-solving score (based on approach and examples)
        scores['problem_solving'] = self._calculate_problem_solving_score(
            total_examples, avg_structure, answer_analyses
        )
        
        # Cultural fit score (based on soft skills and sentiment)
        scores['cultural_fit'] = self._calculate_cultural_fit_score(
            total_soft_skills, answer_analyses, completion_rate
        )
        
        # Overall score (weighted average)
        scores['overall'] = self._calculate_weighted_overall_score(scores, candidate_info)
        
        # Apply completion rate penalty
        if completion_rate < 0.5:
            penalty = (0.5 - completion_rate) * 20
            for key in scores:
                scores[key] = max(0, scores[key] - penalty)
        
        # Ensure all scores are within bounds
        for key in scores:
            scores[key] = round(min(100, max(0, scores[key])), 1)
        
        return scores
    
    def _calculate_technical_score(self, technical_terms: int, avg_depth: float, 
                                  analyses: List[Dict]) -> float:
        """Calculate technical competency score"""
        score = 20  # Base score for attempting
        
        # Technical terminology usage (max 30 points)
        score += min(30, technical_terms * 3)
        
        # Depth of technical responses (max 25 points)
        score += avg_depth * 0.25
        
        # Quality of technical answers specifically
        technical_answers = [a for a in analyses if a['question_type'] == 'technical']
        if technical_answers:
            tech_quality = np.mean([
                a['quality_scores'].get('technical', 50) 
                for a in technical_answers
            ])
            score += tech_quality * 0.25
        
        return score
    
    def _calculate_communication_score(self, avg_clarity: float, avg_structure: float, 
                                      analyses: List[Dict]) -> float:
        """Calculate communication effectiveness score"""
        score = 20  # Base score
        
        # Clarity (max 40 points)
        score += avg_clarity * 0.4
        
        # Structure (max 30 points)
        score += avg_structure * 0.3
        
        # Consistency across answers (max 10 points)
        if len(analyses) > 1:
            clarity_variance = np.var([a['metrics']['clarity_score'] for a in analyses])
            if clarity_variance < 100:  # Consistent clarity
                score += 10
            elif clarity_variance < 200:
                score += 5
        
        return score
    
    def _calculate_problem_solving_score(self, total_examples: int, avg_structure: float, 
                                        analyses: List[Dict]) -> float:
        """Calculate problem-solving ability score"""
        score = 20  # Base score
        
        # Use of examples (max 35 points)
        score += min(35, total_examples * 7)
        
        # Structured approach (max 25 points)
        score += avg_structure * 0.25
        
        # Quality of situational/behavioral answers
        relevant_answers = [
            a for a in analyses 
            if a['question_type'] in ['behavioral', 'situational']
        ]
        if relevant_answers:
            quality = np.mean([
                max(a['quality_scores'].values()) 
                for a in relevant_answers
            ])
            score += quality * 0.20
        
        return score
    
    def _calculate_cultural_fit_score(self, soft_skills: int, analyses: List[Dict], 
                                     completion_rate: float) -> float:
        """Calculate cultural fit score"""
        score = 20  # Base score
        
        # Soft skills demonstration (max 30 points)
        score += min(30, soft_skills * 5)
        
        # Positive sentiment (max 20 points)
        sentiments = [a['metrics']['sentiment_score'] for a in analyses]
        if sentiments:
            avg_sentiment = np.mean(sentiments)
            if avg_sentiment > 0:
                score += avg_sentiment * 20
        
        # Engagement (completion rate) (max 30 points)
        score += completion_rate * 30
        
        return score
    
    def _calculate_weighted_overall_score(self, scores: Dict[str, float], 
                                         candidate_info: Dict) -> float:
        """Calculate weighted overall score based on position requirements"""
        position = candidate_info.get('position', '').lower()
        
        # Default weights
        weights = {
            'technical': 0.35,
            'communication': 0.25,
            'problem_solving': 0.25,
            'cultural_fit': 0.15
        }
        
        # Adjust weights based on position
        if 'senior' in position or 'lead' in position:
            weights['technical'] = 0.30
            weights['communication'] = 0.30
            weights['problem_solving'] = 0.25
            weights['cultural_fit'] = 0.15
        elif 'junior' in position or 'intern' in position:
            weights['technical'] = 0.25
            weights['communication'] = 0.25
            weights['problem_solving'] = 0.20
            weights['cultural_fit'] = 0.30
        elif 'manager' in position:
            weights['technical'] = 0.20
            weights['communication'] = 0.35
            weights['problem_solving'] = 0.30
            weights['cultural_fit'] = 0.15
        
        # Calculate weighted average
        overall = sum(scores[key] * weights[key] for key in weights)
        
        return overall
    
    def _generate_insights(self, analyses: List[Dict], scores: Dict[str, float]) -> Dict:
        """Generate actionable insights from the analysis"""
        insights = {
            'strengths': [],
            'weaknesses': [],
            'recommendations': [],
            'red_flags': []
        }
        
        # Analyze strengths
        if scores['technical'] >= 70:
            insights['strengths'].append("Strong technical knowledge and expertise")
        if scores['communication'] >= 70:
            insights['strengths'].append("Excellent communication and articulation skills")
        if scores['problem_solving'] >= 70:
            insights['strengths'].append("Demonstrated strong problem-solving abilities")
        if scores['cultural_fit'] >= 70:
            insights['strengths'].append("Good cultural alignment and soft skills")
        
        # Analyze weaknesses
        if scores['technical'] < 50:
            insights['weaknesses'].append("Limited technical depth in responses")
        if scores['communication'] < 50:
            insights['weaknesses'].append("Communication skills need improvement")
        if scores['problem_solving'] < 50:
            insights['weaknesses'].append("Lacks concrete examples of problem-solving")
        if scores['cultural_fit'] < 50:
            insights['weaknesses'].append("May not align well with team culture")
        
        # Check for specific patterns
        total_examples = sum(a['metrics']['examples_provided'] for a in analyses)
        if total_examples == 0:
            insights['weaknesses'].append("No specific examples provided")
            insights['recommendations'].append("Follow up with behavioral questions requiring specific examples")
        
        # Response quality analysis
        poor_responses = [a for a in analyses if a['response_quality'] == 'poor']
        if len(poor_responses) > len(analyses) * 0.3:
            insights['red_flags'].append("High percentage of poor quality responses")
        
        no_responses = [a for a in analyses if a['response_quality'] == 'no_response']
        if len(no_responses) > 0:
            insights['red_flags'].append(f"Failed to answer {len(no_responses)} question(s)")
        
        # Generate recommendations
        if scores['overall'] >= 75:
            insights['recommendations'].append("Strong candidate - proceed to next round")
            insights['recommendations'].append("Consider for senior-level responsibilities")
        elif scores['overall'] >= 60:
            insights['recommendations'].append("Promising candidate - conduct technical assessment")
            insights['recommendations'].append("Verify technical skills with coding test")
        elif scores['overall'] >= 45:
            insights['recommendations'].append("Borderline candidate - additional screening recommended")
            insights['recommendations'].append("Consider for junior position or internship")
        else:
            insights['recommendations'].append("Not recommended for current position")
            insights['recommendations'].append("Consider for other roles or future opportunities")
        
        return insights
    
    def _determine_recommendation(self, scores: Dict[str, float], insights: Dict) -> str:
        """Determine final hiring recommendation"""
        overall_score = scores['overall']
        red_flags = len(insights.get('red_flags', []))
        
        if red_flags > 2:
            return "REJECT"
        elif overall_score >= 75 and red_flags == 0:
            return "STRONG_HIRE"
        elif overall_score >= 60:
            return "HIRE"
        elif overall_score >= 45:
            return "MAYBE"
        else:
            return "REJECT"
    
    def _generate_comprehensive_feedback(self, analyses: List[Dict], scores: Dict[str, float], 
                                        insights: Dict, candidate_info: Dict) -> str:
        """Generate detailed feedback report"""
        
        total_questions = len(analyses)
        avg_word_count = np.mean([a['metrics']['word_count'] for a in analyses]) if analyses else 0
        
        feedback = f"""
DYNAMIC INTERVIEW ANALYSIS REPORT
==================================
Candidate: {candidate_info.get('name', 'Unknown')}
Position: {candidate_info.get('position', 'Unknown')}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}

PERFORMANCE SUMMARY
-------------------
Overall Score: {scores['overall']:.1f}/100
Final Recommendation: {self._determine_recommendation(scores, insights)}

DETAILED SCORES
---------------
• Technical Skills: {scores['technical']:.1f}/100
• Communication: {scores['communication']:.1f}/100
• Problem Solving: {scores['problem_solving']:.1f}/100
• Cultural Fit: {scores['cultural_fit']:.1f}/100

RESPONSE METRICS
----------------
• Questions Answered: {total_questions}
• Average Response Length: {avg_word_count:.0f} words
• Response Quality Distribution:
"""
        
        # Add response quality distribution
        quality_dist = Counter(a['response_quality'] for a in analyses)
        for quality, count in quality_dist.items():
            percentage = (count / total_questions) * 100
            feedback += f"  - {quality.replace('_', ' ').title()}: {count} ({percentage:.0f}%)\n"
        
        feedback += f"""
KEY STRENGTHS
-------------
"""
        for strength in insights['strengths'][:3]:
            feedback += f"• {strength}\n"
        
        if not insights['strengths']:
            feedback += "• No significant strengths identified\n"
        
        feedback += f"""
AREAS FOR IMPROVEMENT
---------------------
"""
        for weakness in insights['weaknesses'][:3]:
            feedback += f"• {weakness}\n"
        
        if not insights['weaknesses']:
            feedback += "• No major weaknesses identified\n"
        
        if insights['red_flags']:
            feedback += f"""
CONCERNS
--------
"""
            for flag in insights['red_flags']:
                feedback += f"⚠️ {flag}\n"
        
        feedback += f"""
RECOMMENDATIONS
---------------
"""
        for rec in insights['recommendations'][:3]:
            feedback += f"• {rec}\n"
        
        feedback += f"""
DETAILED ASSESSMENT
-------------------
"""
        
        # Add contextual assessment based on scores
        if scores['overall'] >= 75:
            feedback += """
This candidate demonstrated exceptional performance across all evaluation criteria. 
Their responses showed deep technical knowledge, excellent communication skills, 
and strong problem-solving abilities. They would be an excellent addition to the team.
"""
        elif scores['overall'] >= 60:
            feedback += """
This candidate shows solid potential with good foundational skills. While there are 
areas for improvement, their overall performance suggests they could succeed in this 
role with appropriate support and development.
"""
        elif scores['overall'] >= 45:
            feedback += """
This candidate showed mixed results in the interview. While they demonstrated some 
relevant skills, there are significant gaps that would need to be addressed. Consider 
for a more junior position or provide additional training if hired.
"""
        else:
            feedback += """
Based on the interview responses, this candidate does not appear to meet the minimum 
requirements for this position. Their answers lacked depth, specificity, and failed 
to demonstrate the necessary competencies for success in this role.
"""
        
        return feedback.strip()
    
    def _calculate_confidence(self, analyses: List[Dict]) -> float:
        """Calculate confidence level of the analysis"""
        if not analyses:
            return 0.0
        
        # Factors affecting confidence
        factors = []
        
        # Number of questions answered
        answer_count = len(analyses)
        if answer_count >= 10:
            factors.append(1.0)
        elif answer_count >= 5:
            factors.append(0.8)
        else:
            factors.append(0.5)
        
        # Average response length
        avg_words = np.mean([a['metrics']['word_count'] for a in analyses])
        if avg_words >= 50:
            factors.append(1.0)
        elif avg_words >= 25:
            factors.append(0.7)
        else:
            factors.append(0.4)
        
        # Response quality consistency
        qualities = [a['response_quality'] for a in analyses]
        if len(set(qualities)) == 1:  # All same quality
            factors.append(0.9)
        elif len(set(qualities)) <= 2:
            factors.append(0.7)
        else:
            factors.append(0.5)
        
        return min(1.0, np.mean(factors))
    
    def _generate_no_response_analysis(self) -> Dict[str, Any]:
        """Generate analysis for interviews with no valid responses"""
        return {
            'scores': {
                'technical': 0,
                'communication': 0,
                'problem_solving': 0,
                'cultural_fit': 0,
                'overall': 0
            },
            'insights': {
                'strengths': [],
                'weaknesses': ['No valid responses provided', 'Interview incomplete'],
                'recommendations': ['Schedule a follow-up interview', 'Verify candidate availability'],
                'red_flags': ['Interview not completed']
            },
            'feedback': """
INTERVIEW INCOMPLETE
====================
The candidate did not provide any valid responses during the interview session.
This could be due to technical issues, misunderstanding, or lack of preparation.

RECOMMENDATION: Schedule a follow-up interview to properly assess the candidate.
""",
            'recommendation': 'INCOMPLETE',
            'answer_analyses': [],
            'metadata': {
                'total_questions': 0,
                'answered_questions': 0,
                'analysis_timestamp': datetime.now().isoformat(),
                'analysis_method': 'no_response',
                'confidence': 0.0
            }
        }


def analyze_interview_production(qa_pairs: List[Dict], candidate_info: Dict) -> Dict[str, Any]:
    """
    Production entry point for interview analysis
    
    Args:
        qa_pairs: List of Q&A dictionaries with 'question' and 'answer' keys
        candidate_info: Dictionary with 'name', 'position', etc.
    
    Returns:
        Complete analysis with scores, insights, and recommendations
    """
    analyzer = DynamicInterviewAnalyzer()
    return analyzer.analyze_interview(qa_pairs, candidate_info)


# Integration with your backend
def integrate_with_backend(candidate_id: int):
    """
    Integration function for your Flask backend
    """
    from db import SessionLocal, Candidate
    import json
    
    session = SessionLocal()
    try:
        candidate = session.query(Candidate).filter_by(id=candidate_id).first()
        if not candidate:
            return None
        
        # Extract Q&A pairs
        qa_pairs = []
        if candidate.interview_qa_pairs:
            qa_pairs = json.loads(candidate.interview_qa_pairs)
        
        # Prepare candidate info
        candidate_info = {
            'name': candidate.name,
            'position': candidate.job_title,
            'email': candidate.email,
            'company': 'ABC D'  # Your company name
        }
        
        # Perform analysis
        analysis = analyze_interview_production(qa_pairs, candidate_info)
        
        # Update database with real scores
        candidate.interview_ai_score = analysis['scores']['overall']
        candidate.interview_ai_technical_score = analysis['scores']['technical']
        candidate.interview_ai_communication_score = analysis['scores']['communication']
        candidate.interview_ai_problem_solving_score = analysis['scores']['problem_solving']
        candidate.interview_ai_cultural_fit_score = analysis['scores']['cultural_fit']
        
        # Store insights
        candidate.interview_ai_strengths = json.dumps(analysis['insights']['strengths'])
        candidate.interview_ai_weaknesses = json.dumps(analysis['insights']['weaknesses'])
        candidate.interview_recommendations = json.dumps(analysis['insights']['recommendations'])
        
        # Store feedback
        candidate.interview_ai_overall_feedback = analysis['feedback']
        candidate.interview_final_status = 'Passed' if analysis['scores']['overall'] >= 60 else 'Failed'
        
        # Update confidence and method
        candidate.interview_confidence_score = analysis['metadata']['confidence']
        candidate.interview_scoring_method = 'dynamic_content_analysis'
        
        session.commit()
        
        return analysis
        
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()