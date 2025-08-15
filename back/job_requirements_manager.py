# job_requirements_manager.py

import re
import json
from typing import List, Dict, Optional
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobRequirementsManager:
    """Production-ready job requirements manager with intelligent parsing and caching"""
    
    def __init__(self, db_session):
        self.session = db_session
        self._cache = {}
        self._skill_patterns = self._compile_skill_patterns()
    
    def _compile_skill_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Compile regex patterns for skill extraction"""
        return {
            'programming_languages': [
                re.compile(r'\b(python|java|javascript|typescript|c\+\+|c#|ruby|go|rust|scala|kotlin|swift|php|r|matlab)\b', re.I),
            ],
            'ml_frameworks': [
                re.compile(r'\b(tensorflow|pytorch|keras|scikit-learn|sklearn|xgboost|lightgbm|catboost|mlflow|kubeflow)\b', re.I),
            ],
            'ai_concepts': [
                re.compile(r'\b(machine learning|deep learning|neural network|nlp|natural language processing|computer vision|reinforcement learning|gan|transformer|bert|gpt|lstm|cnn|rnn)\b', re.I),
            ],
            'databases': [
                re.compile(r'\b(sql|mysql|postgresql|mongodb|redis|cassandra|elasticsearch|dynamodb|oracle|sqlite)\b', re.I),
            ],
            'cloud_platforms': [
                re.compile(r'\b(aws|azure|gcp|google cloud|kubernetes|docker|openshift|terraform|ansible)\b', re.I),
            ],
            'web_frameworks': [
                re.compile(r'\b(django|flask|fastapi|express|react|angular|vue|spring|rails|laravel)\b', re.I),
            ],
            'data_tools': [
                re.compile(r'\b(pandas|numpy|spark|hadoop|kafka|airflow|dbt|tableau|power bi|looker)\b', re.I),
            ]
        }
    
    def extract_skills_from_text(self, text: str) -> List[str]:
        """Extract skills from job description using NLP patterns"""
        skills = set()
        
        # Extract using patterns
        for category, patterns in self._skill_patterns.items():
            for pattern in patterns:
                matches = pattern.findall(text)
                skills.update([match.title() for match in matches])
        
        # Extract from common requirement patterns
        requirement_patterns = [
            r'(?:experience with|knowledge of|proficient in|familiar with|expertise in)\s+([^,.;]+)',
            r'(?:required skills?|must have|requirements?):\s*([^.]+)',
            r'(?:technologies?|tools?):\s*([^.]+)',
        ]
        
        for pattern in requirement_patterns:
            matches = re.findall(pattern, text, re.I)
            for match in matches:
                # Clean and split potential skill lists
                potential_skills = re.split(r'[,;/]|\band\b|\bor\b', match)
                for skill in potential_skills:
                    skill = skill.strip()
                    if 2 < len(skill) < 50:  # Reasonable skill name length
                        skills.add(skill.title())
        
        return list(skills)
    
    def parse_experience_requirements(self, text: str) -> Dict[str, int]:
        """Extract experience requirements from text"""
        experience = {
            'minimum': 0,
            'maximum': None,
            'preferred': None
        }
        
        # Patterns for experience extraction
        patterns = [
            (r'(\d+)\+?\s*years?\s*(?:of\s*)?experience', 'minimum'),
            (r'(?:minimum|at least)\s*(\d+)\s*years?', 'minimum'),
            (r'(\d+)\s*-\s*(\d+)\s*years?', 'range'),
            (r'(?:up to|maximum)\s*(\d+)\s*years?', 'maximum'),
            (r'(?:preferred|ideal)\s*(\d+)\s*years?', 'preferred'),
        ]
        
        for pattern, type_ in patterns:
            matches = re.findall(pattern, text, re.I)
            if matches:
                if type_ == 'range' and len(matches[0]) == 2:
                    experience['minimum'] = int(matches[0][0])
                    experience['maximum'] = int(matches[0][1])
                elif type_ in experience and matches[0]:
                    experience[type_] = int(matches[0])
        
        return experience
    
    def get_job_requirements(self, job_id: str, job_title: str = None, job_description: str = None) -> Dict:
        """Get job requirements with intelligent fallback mechanisms"""
        
        # Check cache first
        cache_key = f"job_{job_id}"
        if cache_key in self._cache:
            logger.info(f"Returning cached requirements for job {job_id}")
            return self._cache[cache_key]
        
        # Try database first (if you have a jobs table)
        try:
            result = self.session.execute(
                text("""
                    SELECT id, title, description, required_skills, nice_to_have_skills,
                           minimum_experience, maximum_experience
                    FROM jobs 
                    WHERE id = :job_id
                """),
                {"job_id": job_id}
            ).fetchone()
            
            if result and result.required_skills:
                requirements = self._parse_db_requirements(result)
                self._cache[cache_key] = requirements
                return requirements
        except Exception as e:
            logger.debug(f"No job found in DB for id {job_id}: {e}")
        
        # Extract from description if available
        if job_description:
            extracted_skills = self.extract_skills_from_text(job_description)
            experience = self.parse_experience_requirements(job_description)
            
            if extracted_skills:
                requirements = {
                    'job_id': job_id,
                    'title': job_title or "Unknown Position",
                    'description': job_description,
                    'required_skills': extracted_skills[:8],  # Top 8 skills
                    'preferred_skills': extracted_skills[8:12] if len(extracted_skills) > 8 else [],
                    'experience_years': experience['minimum']
                }
                self._cache[cache_key] = requirements
                return requirements
        
        # Fallback: Create based on job title
        if job_title:
            return self._create_intelligent_requirements(job_id, job_title)
        
        # Ultimate fallback
        return self._get_fallback_requirements(job_title or "Software Engineer")
    
    def _parse_db_requirements(self, db_row) -> Dict:
        """Parse database row into structured requirements"""
        
        # Parse skills from comma-separated or JSON format
        required_skills = []
        if db_row.required_skills:
            try:
                # Try JSON first
                required_skills = json.loads(db_row.required_skills)
            except:
                # Fall back to comma-separated
                required_skills = [s.strip() for s in db_row.required_skills.split(',') if s.strip()]
        
        nice_to_have = []
        if hasattr(db_row, 'nice_to_have_skills') and db_row.nice_to_have_skills:
            try:
                nice_to_have = json.loads(db_row.nice_to_have_skills)
            except:
                nice_to_have = [s.strip() for s in db_row.nice_to_have_skills.split(',') if s.strip()]
        
        return {
            'job_id': db_row.id,
            'title': db_row.title,
            'description': db_row.description or f"Position for {db_row.title}",
            'required_skills': required_skills,
            'preferred_skills': nice_to_have,
            'experience_years': db_row.minimum_experience or 0
        }
    
    def _create_intelligent_requirements(self, job_id: str, job_title: str) -> Dict:
        """Create intelligent job requirements based on job title"""
        
        # Define role templates
        role_templates = {
            'ai': {
                'keywords': ['ai', 'artificial intelligence', 'machine learning', 'ml', 'deep learning', 'data scientist'],
                'required_skills': ['Python', 'Machine Learning', 'Deep Learning', 'TensorFlow/PyTorch', 
                                  'Mathematics', 'Statistics', 'Data Analysis', 'NumPy', 'Pandas'],
                'preferred_skills': ['Docker', 'Kubernetes', 'AWS/GCP/Azure', 'MLOps', 'Git', 'SQL', 
                               'Computer Vision', 'NLP', 'Transformers', 'BERT/GPT'],
                'min_experience': 0
            },
            'backend': {
                'keywords': ['backend', 'server', 'api', 'platform', 'systems'],
                'required_skills': ['Python/Java/Go', 'REST APIs', 'Databases', 'SQL', 'Git', 
                                  'Software Architecture', 'Testing', 'Linux'],
                'preferred_skills': ['Docker', 'Kubernetes', 'Microservices', 'Message Queues', 
                               'Redis', 'GraphQL', 'CI/CD'],
                'min_experience': 1
            },
            'frontend': {
                'keywords': ['frontend', 'ui', 'ux', 'react', 'angular', 'vue'],
                'required_skills': ['JavaScript', 'HTML/CSS', 'React/Angular/Vue', 'Responsive Design', 
                                  'Git', 'REST APIs', 'TypeScript'],
                'preferred_skills': ['Node.js', 'Webpack', 'Testing', 'GraphQL', 'Performance Optimization',
                               'Accessibility', 'Design Systems'],
                'min_experience': 1
            },
            'fullstack': {
                'keywords': ['fullstack', 'full stack', 'full-stack'],
                'required_skills': ['JavaScript', 'Python/Java/Node.js', 'React/Angular/Vue', 
                                  'Databases', 'REST APIs', 'Git', 'HTML/CSS'],
                'preferred_skills': ['Docker', 'Cloud Platforms', 'CI/CD', 'Microservices', 
                               'TypeScript', 'GraphQL', 'Testing'],
                'min_experience': 2
            },
            'python': {
                'keywords': ['python developer', 'python engineer', 'python programmer'],
                'required_skills': ['Python', 'Django/Flask', 'REST APIs', 'SQL', 'Git', 
                                  'Object-Oriented Programming', 'Testing'],
                'preferred_skills': ['Docker', 'Redis', 'Celery', 'PostgreSQL', 'MongoDB', 
                               'AWS', 'Microservices'],
                'min_experience': 1
            }
        }
        
        # Determine role type from job title
        job_title_lower = job_title.lower()
        selected_template = None
        
        for role, template in role_templates.items():
            if any(keyword in job_title_lower for keyword in template['keywords']):
                selected_template = template
                break
        
        # Default template
        if not selected_template:
            selected_template = {
                'required_skills': ['Programming', 'Problem Solving', 'Communication', 
                                  'Team Collaboration', 'Git', 'Agile Methodology'],
                'preferred_skills': ['Cloud Platforms', 'Docker', 'Testing', 'CI/CD'],
                'min_experience': 0
            }
        
        # Adjust for seniority
        if 'senior' in job_title_lower:
            selected_template['min_experience'] += 3
        elif 'lead' in job_title_lower or 'principal' in job_title_lower:
            selected_template['min_experience'] += 5
        elif 'junior' in job_title_lower or 'entry' in job_title_lower:
            selected_template['min_experience'] = 0
        
        requirements = {
            'job_id': job_id,
            'title': job_title,
            'description': f"We are looking for a talented {job_title} to join our team.",
            'required_skills': selected_template['required_skills'][:8],
            'preferred_skills': selected_template.get('preferred_skills', [])[:5],
            'experience_years': selected_template['min_experience']
        }
        
        self._cache[cache_key] = requirements
        return requirements
    
    def _get_fallback_requirements(self, job_title: str) -> Dict:
        """Ultimate fallback requirements"""
        return {
            'job_id': 'unknown',
            'title': job_title,
            'description': f'Position for {job_title}',
            'required_skills': ['Programming', 'Problem Solving', 'Communication', 'Team Work'],
            'preferred_skills': [],
            'experience_years': 0
        }