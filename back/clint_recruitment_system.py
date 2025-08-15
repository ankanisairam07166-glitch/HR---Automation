import os
import re
import json
# import openai
import docx2txt
import PyPDF2
import smtplib
import logging
from langchain_openai import ChatOpenAI
import shutil
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import time
from dotenv import load_dotenv
from typing import Dict, List, Optional
from langchain_openai import ChatOpenAI

# === DB Imports (make sure your db.py has Candidate, SessionLocal) ===
from db import Candidate, SessionLocal

# LangChain, LangGraph imports
from langchain_core.messages import AIMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from langgraph.graph import END
from langgraph.checkpoint.memory import MemorySaver

from pydantic import BaseModel, Field

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='clint_recruitment.log',
    filemode='a'
)
logger = logging.getLogger('ClintRecruitment')

# PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
# RESUME_FOLDER = os.path.join(PROJECT_DIR, r"C:\Users\DIVYA\Downloads\hr-frontend (2)\hr-frontend\backend\resumes")
RESUME_FOLDER = os.path.join(os.path.dirname(__file__), "resumes")
import os

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

PROCESSED_FOLDER = os.path.join(PROJECT_DIR, "processed_resumes")
for folder in [RESUME_FOLDER, PROCESSED_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)
        logger.info(f"Created folder: {folder}")

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY not found in environment variables")
    raise ValueError("OPENAI_API_KEY not found in environment variables")

# === DB UTILS ===
def get_all_candidates_from_db() -> list:
    session = SessionLocal()
    candidates = session.query(Candidate).all()
    data = [c.__dict__ for c in candidates]
    for d in data:
        d.pop('_sa_instance_state', None)
    session.close()
    return data

def save_candidate_to_db(candidate_info: dict):
    session = SessionLocal()
    try:
        cand = session.query(Candidate).filter_by(email=candidate_info["email"]).first()
        if 'id' in candidate_info:
            del candidate_info['id']
        # Remove created_at if it's None or missing, so SQLAlchemy default is used
        if 'created_at' in candidate_info and not candidate_info['created_at']:
            del candidate_info['created_at']
        if not cand:
            cand = Candidate(**candidate_info)
            session.add(cand)
        else:
            # Only update fields that aren't id
            for k, v in candidate_info.items():
                if k != 'id':
                    setattr(cand, k, v)
        print(">>> About to commit candidate:", cand)
        session.commit()
    except Exception as e:
        print(f"❌ DB error for {candidate_info.get('email')}: {str(e)}")
        session.rollback()
    finally:
        session.close()


def get_llm(temperature=0, model="gpt-4o"):
    return ChatOpenAI(
        temperature=temperature,
        model=model,
        api_key=OPENAI_API_KEY
    )

def extract_text_from_resume(resume_path: str) -> str:
    try:
        if resume_path.lower().endswith('.pdf'):
            with open(resume_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                return text
        elif resume_path.lower().endswith('.docx'):
            return docx2txt.process(resume_path)
        elif resume_path.lower().endswith('.txt'):
            with open(resume_path, 'r', encoding='utf-8') as file:
                return file.read()
        else:
            logger.warning(f"Unsupported file format for {resume_path}")
            return ""
    except Exception as e:
        logger.error(f"Error extracting text from {resume_path}: {str(e)}")
        return ""

def send_email_notification(candidate_info: Dict, is_shortlisted: bool, resume_score: Optional[float] = None,
                            feedback: Optional[str] = None) -> bool:
    try:
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        sender_email = os.getenv("SENDER_EMAIL")
        sender_password = os.getenv("SENDER_PASSWORD")
        company_name = os.getenv("COMPANY_NAME", "Our Company")
        job_title = candidate_info.get("job_title", os.getenv("JOB_TITLE", "Open Position"))
        testlify_link = candidate_info.get("testlify_link") or candidate_info.get("assessment_invite_link") or "https://candidate.testlify.com/invite/DEFAULT"

        if not sender_email or not sender_password:
            print("⚠️ Email credentials not set in environment variables")
            return False

        candidate_name = candidate_info.get("name", "Unknown Candidate")
        candidate_email = candidate_info.get("email", "").replace(" ", "")
        if not candidate_email or "@" not in candidate_email or "." not in candidate_email:
            print(f"⚠️ Invalid email format: {candidate_email}")
            return False

        print(f"✉️ Sending email to: {candidate_email}")
        greeting = f"Dear {candidate_name}" if candidate_name != "Unknown Candidate" else "Dear Candidate"

        if is_shortlisted:
            subject = f"🎉 You've Been Shortlisted for {job_title} at {company_name}!"
            body = f"""{greeting},

We are thrilled to let you know that, after reviewing your application, you've been **shortlisted** for the {job_title} position at {company_name}!

✨ **Why you stood out:**  
Your experience and skills caught our attention and align wonderfully with what we're looking for. We were especially impressed with your background and believe you could make a real impact with us.

**Next Steps:**  
1. **Assessment:** Please complete our assessment using this link:  
   {testlify_link}

2. **Interview:** If you qualify based on your assessment, we'll invite you for a conversation with our team to get to know you even better.

**Your ATS Score:** {resume_score:.1f}/100

{feedback if feedback else ""}

We're excited to move forward together!  
If you have any questions, reply to this email—we're here to help.

With best wishes,  
Recruitment Team | {company_name}
"""
        else:
            subject = f"Your Application for {job_title} at {company_name}"
            body = f"""{greeting},

Thank you for applying for the {job_title} role at {company_name}.

After careful review, we've decided to move forward with other candidates at this time.  
**Your ATS Score:** {resume_score:.1f}/100

Here is some feedback to help with your future applications:
{feedback if feedback else ""}

We appreciate your interest and encourage you to apply for future roles.

Best regards,  
Recruitment Team | {company_name}
"""

        msg = MIMEText(body, 'plain', 'utf-8')
        msg['From'] = sender_email
        msg['To'] = candidate_email
        msg['Subject'] = subject

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, candidate_email, msg.as_string())
        server.quit()
        print(f"✅ Email sent to {candidate_email}")
        return True

    except Exception as e:
        print(f"⚠️ Error sending email: {str(e)}")
        return False
def get_env_int(key, default):
    value = os.getenv(key, "")
    if value.strip() == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default

# === PYDANTIC MODELS (Define these FIRST) ===
class CandidateInfo(BaseModel):
    name: str = Field(default="Unknown Candidate")
    email: str = Field(default="")
    linkedin: str = Field(default="")
    github: str = Field(default="")
    resume_path: str = Field(default="")
    processed_date: str = Field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    notification_sent: bool = Field(default=False)
    ats_score: float = Field(default=0.0)
    status: str = Field(default="")
    score_reasoning: str = Field(default="")
    decision_reason: str = Field(default="")
    job_title: str = Field(default="")
    testlify_link: str = Field(default="")
    assessment_invite_link: str = Field(default="")

class JobRequirements(BaseModel):
    job_id: str = Field(default="")
    title: str = Field(default="")
    description: str = Field(default="")
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    experience_years: int = Field(default=0)

class RecruitmentState(BaseModel):
    candidate: CandidateInfo = Field(default_factory=CandidateInfo)
    job_requirements: JobRequirements = Field(default_factory=JobRequirements)
    resume_text: str = Field(default="")
    ats_threshold: float = Field(default=70.0)
    feedback: str = Field(default="")
    testlify_link: str = Field(default="")

def resume_parser(state: RecruitmentState) -> RecruitmentState:
    logger.info("Resume Parser Agent: Extracting candidate information...")
    print("📄 Resume Parser Agent: Extracting candidate information...")
    if not state.resume_text:
        raise ValueError("Resume text not provided in state")
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert resume parser AI. Extract name, email, linkedin, github."""),
        ("human", "Resume text: {resume_text}\n\nExtract info as JSON: name, email, linkedin, github.")
    ])
    parser = JsonOutputParser()
    parsing_chain = prompt | get_llm() | parser
    try:
        result = parsing_chain.invoke({"resume_text": state.resume_text[:4000]})
        extracted_email = result.get("email", "")
        if extracted_email:
            extracted_email = extracted_email.replace(" ", "").strip().lower()
        state.candidate.name = result.get("name", "Unknown Candidate")
        state.candidate.email = extracted_email
        state.candidate.linkedin = result.get("linkedin", "")
        state.candidate.github = result.get("github", "")
        state.candidate.job_title = state.job_requirements.title
        state.candidate.testlify_link = state.testlify_link
        state.candidate.assessment_invite_link = state.testlify_link
        return state
    except Exception as e:
        logger.error(f"Error in resume parser agent: {str(e)}")
        print(f"❌ Error in resume parser: {str(e)}")
        return state
def ats_scorer(state: RecruitmentState) -> RecruitmentState:
    """Dynamic ATS scorer with automatic job requirements handling"""
    logger.info("ATS Scorer Agent: Calculating ATS score...")
    print("🔍 ATS Scorer Agent: Calculating ATS score...")

    # Debug output
    print(f"ATS Scorer DEBUG - Job ID: {state.job_requirements.job_id}")
    print(f"ATS Scorer DEBUG - Job Title: {state.job_requirements.title}")
    print(f"ATS Scorer DEBUG - Job Desc: {state.job_requirements.description}")
    print(f"ATS Scorer DEBUG - Required Skills: {state.job_requirements.required_skills}")

    # If job requirements are missing, create them automatically
    if not state.job_requirements.required_skills or len(state.job_requirements.required_skills) == 0:
        print("⚠️ No job requirements found, creating them automatically...")

        # Extract required skills from the job description using AI model
        if state.job_requirements.description and state.job_requirements.title:
            try:
                prompt = ChatPromptTemplate.from_messages([
                    ("system", """You are an expert job requirements analyzer. Extract required and preferred skills from the job description.
                    Return as JSON with 'required_skills' (list of 4-6 most important skills) and 'preferred_skills' (list of 3-5 nice-to-have skills).
                    Focus on technical skills, programming languages, frameworks, and tools."""), 
                    ("human", "Job Title: {title}\nJob Description: {desc}")
                ])
                parser = JsonOutputParser()
                skill_chain = prompt | get_llm() | parser
                skills_result = skill_chain.invoke({
                    "title": state.job_requirements.title,
                    "desc": state.job_requirements.description
                })

                state.job_requirements.required_skills = skills_result.get("required_skills", [])[:6]
                state.job_requirements.preferred_skills = skills_result.get("preferred_skills", [])[:5]
                print(f"✅ Extracted {len(state.job_requirements.required_skills)} required skills from job description")
            except Exception as e:
                print(f"⚠️ Could not extract skills from description: {e}")

        # If still no skills, use defaults based on job title (fallback mechanism)
        if not state.job_requirements.required_skills:
            print("📋 Using default skills based on job title...")

            job_title_lower = (state.job_requirements.title or "").lower()

            # Default skills based on job title
            if "ai" in job_title_lower or "machine learning" in job_title_lower or "ml" in job_title_lower:
                state.job_requirements.required_skills = ['Python', 'Machine Learning', 'Data Science', 'TensorFlow/PyTorch', 'Statistics']
                state.job_requirements.preferred_skills = ['Deep Learning', 'NLP', 'Computer Vision', 'MLOps', 'Cloud Platforms']
            elif "data scientist" in job_title_lower:
                state.job_requirements.required_skills = ['Python', 'Statistics', 'Machine Learning', 'SQL', 'Data Analysis']
                state.job_requirements.preferred_skills = ['R', 'Tableau', 'Big Data', 'Spark', 'Deep Learning']
            elif "backend" in job_title_lower:
                state.job_requirements.required_skills = ['Python/Java/Node.js', 'REST APIs', 'Databases', 'Cloud Services', 'Git']
                state.job_requirements.preferred_skills = ['Docker', 'Kubernetes', 'Microservices', 'CI/CD', 'GraphQL']
            elif "frontend" in job_title_lower:
                state.job_requirements.required_skills = ['JavaScript', 'React/Vue/Angular', 'HTML/CSS', 'Responsive Design', 'Git']
                state.job_requirements.preferred_skills = ['TypeScript', 'Testing', 'Performance Optimization', 'State Management', 'Build Tools']
            elif "full stack" in job_title_lower:
                state.job_requirements.required_skills = ['JavaScript', 'Python/Node.js', 'Databases', 'React/Vue', 'APIs']
                state.job_requirements.preferred_skills = ['Cloud Platforms', 'Docker', 'TypeScript', 'DevOps', 'Testing']
            else:
                # Generic technical position
                state.job_requirements.required_skills = ['Programming', 'Problem Solving', 'Software Development', 'Version Control', 'Team Collaboration']
                state.job_requirements.preferred_skills = ['Agile/Scrum', 'Cloud Technologies', 'Testing', 'Documentation', 'Communication']

            if not state.job_requirements.experience_years:
                state.job_requirements.experience_years = 2 if "junior" in job_title_lower else 3

            print(f"✅ Set default requirements for '{state.job_requirements.title or 'Technical Position'}'")


    # FINAL SAFETY: If still no required_skills, set to generic fallback
    if not state.job_requirements.required_skills:
        print("⚠️ Fallback: Setting generic required skills to avoid ValueError.")
        state.job_requirements.required_skills = ['Programming', 'Problem Solving', 'Software Development']
        state.job_requirements.preferred_skills = ['Communication']
        if not state.job_requirements.experience_years:
            state.job_requirements.experience_years = 2

    # Now continue with scoring - requirements are guaranteed to exist
    required_skills = ", ".join(state.job_requirements.required_skills)
    preferred_skills = ", ".join(state.job_requirements.preferred_skills)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert ATS (Applicant Tracking System) AI. Score the resume from 0-100 based on how well it matches the job requirements.

Scoring criteria:
- Required skills match (40 points): How many required skills does the candidate clearly demonstrate?
- Preferred skills match (20 points): Bonus points for preferred skills
- Relevant experience (20 points): Years of experience and relevance to the role
- Education & certifications (10 points): Relevant degrees, certifications, courses
- Overall fit (10 points): Communication, achievements, project relevance

Return JSON with:
- score: number between 0-100
- reasoning: detailed explanation of the score
- matched_skills: list of skills from requirements found in resume
- missing_skills: list of required skills not clearly demonstrated"""),
        ("human", """Resume text: {resume_text}

Job requirements:
Title: {title}
Description: {description}
Required skills: {required_skills}
Preferred skills: {preferred_skills}
Experience years: {experience_years}

Analyze and score this resume.""")
    ])
    parser = JsonOutputParser()
    scoring_chain = prompt | get_llm() | parser

    try:
        result = scoring_chain.invoke({
            "resume_text": state.resume_text[:4000],
            "title": state.job_requirements.title or "Technical Position",
            "description": state.job_requirements.description or f"Position for {state.job_requirements.title}",
            "required_skills": required_skills,
            "preferred_skills": preferred_skills,
            "experience_years": state.job_requirements.experience_years or 0
        })

        score = result.get("score", 50)
        try:
            score = float(score)
        except (ValueError, TypeError):
            score = 50

        score = max(0, min(100, score))
        state.candidate.ats_score = score
        state.candidate.score_reasoning = result.get("reasoning", "No reasoning provided")

        # Add matched/missing skills info if available
        if "matched_skills" in result:
            state.candidate.score_reasoning += f"\n\nMatched skills: {', '.join(result['matched_skills'])}"
        if "missing_skills" in result:
            state.candidate.score_reasoning += f"\nMissing skills: {', '.join(result['missing_skills'])}"

        print(f"✅ Calculated ATS score: {score}")
        return state

    except Exception as e:
        logger.error(f"Error in ATS scorer agent: {str(e)}")
        print(f"❌ Error in ATS scorer: {str(e)}")
        state.candidate.ats_score = 50
        state.candidate.score_reasoning = f"Error occurred during scoring: {str(e)}"
        return state

def decision_maker(state: RecruitmentState) -> RecruitmentState:
    logger.info(f"Decision Maker Agent: Determining status for candidate with score {state.candidate.ats_score}")
    print("⚖️ Decision Maker Agent: Determining candidate status...")
    
    # Simple decision logic based on threshold
    if state.candidate.ats_score >= state.ats_threshold:
        state.candidate.status = "Shortlisted"
        state.candidate.decision_reason = f"The candidate's ATS score of {state.candidate.ats_score} meets or exceeds the threshold of {state.ats_threshold}."
    else:
        state.candidate.status = "Rejected"
        state.candidate.decision_reason = f"The candidate's ATS score of {state.candidate.ats_score} is below the threshold of {state.ats_threshold}."
    
    print(f"✅ Decision for {state.candidate.name}: {state.candidate.status}")
    return state

def feedback_generator(state: RecruitmentState) -> RecruitmentState:
    logger.info("Feedback Generator Agent: Creating personalized feedback...")
    print("💬 Feedback Generator Agent: Creating personalized feedback...")
    if state.candidate.status == "Shortlisted":
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Give positive feedback (3-5 sentences) for a shortlisted candidate. 1-2 small improvements."),
            ("human", """
ATS score: {ats_score}/100.
Resume content: {resume_text}
Score reasoning: {score_reasoning}
""")
        ])
    else:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Give actionable feedback for a rejected candidate (3-5 sentences). 2-3 concrete improvements."),
            ("human", """
ATS score: {ats_score}/100.
Resume content: {resume_text}
Score reasoning: {score_reasoning}
""")
        ])
    feedback_chain = prompt | get_llm()
    try:
        raw = feedback_chain.invoke({
            "ats_score": state.candidate.ats_score,
            "resume_text": state.resume_text[:3000],
            "score_reasoning": state.candidate.score_reasoning
        })
        state.feedback = raw.content if isinstance(raw, AIMessage) else str(raw)
        return state
    except Exception as e:
        logger.error(f"Error in feedback generator agent: {str(e)}")
        print(f"❌ Error in feedback generator: {str(e)}")
        state.feedback = "Feedback could not be generated due to an error."
        return state

def email_notifier(state: RecruitmentState) -> RecruitmentState:
    logger.info("Email Notification Agent: Sending email to candidate...")
    print("✉️ Email Notification Agent: Sending email to candidate...")
    if not state.candidate.email:
        logger.warning("No email available for notification")
        print("⚠️ No email available for notification")
        return state
    candidate_info = {
        "name": state.candidate.name,
        "email": state.candidate.email,
        "job_title": state.job_requirements.title,
        "testlify_link": state.testlify_link,
        "assessment_invite_link": state.testlify_link
    }
    is_shortlisted = (state.candidate.status == "Shortlisted")
    success = send_email_notification(
        candidate_info,
        is_shortlisted,
        state.candidate.ats_score,
        state.feedback
    )
    if success:
        state.candidate.notification_sent = True
        logger.info(f"Email sent to {state.candidate.email}")
        print(f"✅ Email sent to {state.candidate.email}")
    else:
        logger.warning(f"Failed to send email to {state.candidate.email}")
        print(f"⚠️ Failed to send email to {state.candidate.email}")
    return state

class ClintRecruitmentSystem:
    def __init__(self, testlify_link=None):
        self.candidates = []
        self.ats_threshold = float(os.getenv("ATS_THRESHOLD", "70"))
        self.max_workers = get_env_int("MAX_WORKERS", 4)
        self.testlify_link = testlify_link or ""
        self.job_requirements = JobRequirements()
        self._build_workflow()
        logger.info(f"ClintRecruitmentSystem initialized with {len(self.candidates)} existing candidates")
        print(f"🤖 Clint Recruitment System initialized with LangGraph (DB Mode)")


    def _build_workflow(self):
        self.workflow = StateGraph(RecruitmentState)
        self.workflow.add_node("resume_parser", resume_parser)
        self.workflow.add_node("ats_scorer", ats_scorer)
        self.workflow.add_node("decision_maker", decision_maker)
        self.workflow.add_node("feedback_generator", feedback_generator)
        self.workflow.add_node("email_notifier", email_notifier)
        self.workflow.add_edge("resume_parser", "ats_scorer")
        self.workflow.add_edge("ats_scorer", "decision_maker")
        self.workflow.add_edge("decision_maker", "feedback_generator")
        self.workflow.add_edge("feedback_generator", "email_notifier")
        self.workflow.add_edge("email_notifier", END)
        self.workflow.set_entry_point("resume_parser")
        self.graph = self.workflow.compile(checkpointer=None)

    def set_job_requirements(self, job_id, job_title, job_description, required_skills, preferred_skills, experience_years=0):
        self.job_requirements = JobRequirements(
            job_id=str(job_id),
            title=job_title,
            description=job_description,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            experience_years=experience_years
        )
        logger.info(f"Job requirements set for job_id={job_id} with {len(required_skills)} required skills")
        print(f"📋 Job requirements set with {len(required_skills)} required skills")


    def set_ats_threshold(self, threshold):
        if 0 <= threshold <= 100:
            self.ats_threshold = threshold
            logger.info(f"ATS threshold set to {threshold}")
            print(f"🎯 ATS threshold set to {threshold}")
        else:
            logger.warning(f"Invalid threshold value: {threshold}")
            print(f"⚠️ Invalid threshold value: {threshold}")

    def process_resume(self, resume_path):
        try:
            if not os.path.exists(resume_path):
                logger.warning(f"Resume file not found: {resume_path}")
                print(f"⚠️ Resume file not found: {resume_path}")
                return False
            resume_filename = os.path.basename(resume_path)
            for candidate in self.candidates:
                if os.path.basename(candidate.get('resume_path', '')) == resume_filename:
                    logger.info(f"Resume {resume_filename} already processed, skipping...")
                    print(f"⚠️ Resume {resume_filename} already processed, skipping...")
                    return False
            print(f"📄 Processing resume: {resume_path}")
            resume_text = extract_text_from_resume(resume_path)
            if not resume_text:
                logger.warning(f"Could not extract text from {resume_path}")
                print(f"⚠️ Could not extract text from {resume_path}")
                return False
            initial_state = RecruitmentState(
                resume_text=resume_text,
                job_requirements=self.job_requirements,
                ats_threshold=self.ats_threshold
            )
            raw_state = self.graph.invoke(initial_state)
            result_state = raw_state if isinstance(raw_state, RecruitmentState) else RecruitmentState(**raw_state)
            candidate_info = result_state.candidate.model_dump()
            candidate_info["resume_path"] = resume_path

            # === Add assessment fields ===
            deadline_hours = 24  # or change to your desired number of hours
            attendance_deadline = datetime.now() + timedelta(hours=deadline_hours)
            candidate_info["attendance_deadline"] = attendance_deadline.isoformat()
            candidate_info["attended_assessment"] = False
            candidate_info["attended_at"] = None
            candidate_info["exam_expired"] = False

            # Fix: Convert any dict fields to JSON string for DB
            for field in ["score_reasoning", "decision_reason"]:
                if isinstance(candidate_info.get(field), dict):
                    candidate_info[field] = json.dumps(candidate_info[field])

            save_candidate_to_db(candidate_info)
            self.candidates = get_all_candidates_from_db()
            # Move resume to processed folder
            try:
                filename = os.path.basename(resume_path)
                destination = os.path.join(PROCESSED_FOLDER, filename)
                if os.path.exists(destination):
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    name, ext = os.path.splitext(filename)
                    destination = os.path.join(PROCESSED_FOLDER, f"{name}_{timestamp}{ext}")
                shutil.copy2(resume_path, destination)
                os.remove(resume_path)
                for candidate in self.candidates:
                    if candidate.get('resume_path') == resume_path:
                        candidate['resume_path'] = destination
                        save_candidate_to_db(candidate)
                logger.info(f"Moved resume to processed folder: {destination}")
                print(f"📁 Moved resume to: {destination}")
            except Exception as e:
                logger.error(f"Error moving resume: {str(e)}")
                print(f"⚠️ Could not move resume file: {str(e)}")
            logger.info(f"Resume processing complete: {resume_path}")
            print(f"✅ Resume processing complete: {resume_path}")
            return True
        except Exception as e:
            logger.error(f"Error processing resume: {str(e)}")
            print(f"❌ Error processing resume: {str(e)}")
            return False

    def process_all_resumes(self, resume_folder=RESUME_FOLDER, use_threads=True):
        if not os.path.exists(resume_folder):
            logger.warning(f"Folder not found: {resume_folder}")
            print(f"⚠️ Folder not found: {resume_folder}")
            return 0
        resume_files = [
            os.path.join(resume_folder, f)
            for f in os.listdir(resume_folder)
            if f.lower().endswith(('.pdf', '.docx', '.txt'))
        ]
        if not resume_files:
            logger.warning(f"No resume files found in {resume_folder}")
            print(f"⚠️ No resume files found in {resume_folder}")
            return 0
        num_files = len(resume_files)
        logger.info(f"Found {num_files} resume files to process")
        print(f"🔍 Found {num_files} resume files to process")
        start_time = time.time()
        processed_count = 0
        if use_threads and num_files > 1:
            with ThreadPoolExecutor(max_workers=min(self.max_workers, num_files)) as executor:
                results = list(executor.map(self.process_resume, resume_files))
                processed_count = sum(1 for result in results if result)
        else:
            for resume_file in resume_files:
                success = self.process_resume(resume_file)
                if success:
                    processed_count += 1
        elapsed_time = time.time() - start_time
        logger.info(f"Processed {processed_count} out of {num_files} resumes in {elapsed_time:.2f} seconds")
        print(f"🎉 Processed {processed_count} out of {num_files} resumes in {elapsed_time:.2f} seconds")
        return processed_count

    def get_candidates(self, status=None):
        if status:
            return [c for c in self.candidates if c.get("status") == status]
        return self.candidates

    def display_results(self):
        shortlisted = self.get_candidates(status="Shortlisted")
        rejected = self.get_candidates(status="Rejected")
        print("\n📊 RECRUITMENT RESULTS 📊")
        print("=" * 50)
        print(f"\n✅ Shortlisted candidates ({len(shortlisted)}):")
        for candidate in shortlisted:
            print(f"  • {candidate.get('name', 'Unknown')} (Score: {candidate.get('ats_score', 0)})")
            print(f"    Email: {candidate.get('email', 'N/A')}")
            if candidate.get('linkedin'):
                print(f"    LinkedIn: {candidate.get('linkedin')}")
            if candidate.get('github'):
                print(f"    GitHub: {candidate.get('github')}")
            print()
        print(f"\n❌ Rejected candidates ({len(rejected)}):")
        for candidate in rejected:
            print(f"  • {candidate.get('name', 'Unknown')} (Score: {candidate.get('ats_score', 0)})")
        print("\n" + "=" * 50)

    def retry_failed_notifications(self):
        retry_count = 0
        for candidate in self.candidates:
            if candidate.get('email') and not candidate.get('notification_sent', False):
                is_shortlisted = (candidate.get('status') == "Shortlisted")
                ats_score = candidate.get('ats_score')
                state = RecruitmentState(
                    resume_text=extract_text_from_resume(candidate.get('resume_path', '')),
                    ats_threshold=self.ats_threshold,
                    job_requirements=self.job_requirements
                )
                state.candidate.name = candidate.get('name', 'Unknown Candidate')
                state.candidate.email = candidate.get('email', '')
                state.candidate.ats_score = ats_score
                state.candidate.status = candidate.get('status', '')
                state.candidate.score_reasoning = candidate.get('score_reasoning', '')
                updated_state = feedback_generator(state)
                success = send_email_notification(
                    candidate,
                    is_shortlisted,
                    ats_score,
                    updated_state.feedback
                )
                if success:
                    candidate['notification_sent'] = True
                    save_candidate_to_db(candidate)
                    retry_count += 1
        if retry_count > 0:
            logger.info(f"Successfully resent {retry_count} notifications")
            print(f"✅ Successfully resent {retry_count} notifications")
        return retry_count


def main():
    try:
        print("\U0001F680 [MAIN] clint_recruitment_system.main() has started")
        logger.info("\U0001F680 clint_recruitment_system.main() has started")

        print("\U0001F916 Initializing Clint Recruitment System with LangGraph (DB)...")
        recruitment_system = ClintRecruitmentSystem()

        job_description = os.getenv("JOB_DESCRIPTION",
                                    "Python developer with experience in machine learning and data analysis.")
        required_skills = os.getenv("REQUIRED_SKILLS", "Python,Machine Learning,Data Analysis").split(',')
        preferred_skills = os.getenv("PREFERRED_SKILLS", "TensorFlow,PyTorch,scikit-learn,pandas").split(',')
        experience_years = int(os.getenv("EXPERIENCE_YEARS", "2"))

        recruitment_system.set_job_requirements(
            job_description=job_description,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            experience_years=experience_years
        )

        ats_threshold = float(os.getenv("ATS_THRESHOLD", "75"))
        recruitment_system.set_ats_threshold(ats_threshold)

        use_threads = os.getenv("USE_THREADS", "True").lower() == "true"
        processed_count = recruitment_system.process_all_resumes(use_threads=use_threads)

        recruitment_system.retry_failed_notifications()

        if processed_count > 0:
            recruitment_system.display_results()
        else:
            print("\n⚠️ No new resumes were processed. Please add resume files to the 'resumes' folder.")

        print("\n✅ Recruitment processing complete")
        logger.info("✅ Recruitment processing complete")

    except Exception as e:
        logger.error(f"❌ Error in main function: {str(e)}")
        print(f"❌ Error: {str(e)}")



  # import this if it's in a separate file



def run_recruitment_with_invite_link(job_id, job_title, job_desc, invite_link):
    """
    Process all resumes and send invite links to shortlisted candidates
    """
    print(f"🤖 Starting AI-powered recruitment screening for job_id={job_id}, title={job_title}")
    print(f"📧 Using invite link: {invite_link}")
    
    # Check if we have a valid invite link
    if not invite_link or "MANUAL_UPDATE_REQUIRED" in invite_link or "DEFAULT" in invite_link:
        print("⚠️  WARNING: No valid invite link provided. Emails will contain a placeholder link.")
    
    # Initialize the recruitment system WITH the invite link
    recruitment_system = ClintRecruitmentSystem(testlify_link=invite_link)
    
    # Parse job description to extract skills
    required_skills = ["Python", "Machine Learning", "AI"]  # Default for AI engineer
    preferred_skills = ["TensorFlow", "PyTorch", "NLP"]
    
    if job_desc:
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", "Extract required and preferred skills from job description. Return as JSON with 'required_skills' and 'preferred_skills' arrays."),
                ("human", "Job Title: {title}\nJob Description: {desc}")
            ])
            parser = JsonOutputParser()
            skill_chain = prompt | get_llm() | parser
            skills_result = skill_chain.invoke({"title": job_title, "desc": job_desc})
            required_skills = skills_result.get("required_skills", required_skills)[:5]
            preferred_skills = skills_result.get("preferred_skills", preferred_skills)[:5]
            print(f"📋 Extracted skills - Required: {required_skills}, Preferred: {preferred_skills}")
        except Exception as e:
            print(f"⚠️  Could not extract skills from job description: {e}")
            print(f"📋 Using default skills for {job_title}")
    
    # Set job requirements with job_id
    recruitment_system.job_requirements = JobRequirements(
        job_id=str(job_id),
        title=job_title,
        description=job_desc or f"Looking for a talented {job_title}",
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        experience_years=2
    )
    
    # Set ATS threshold
    ats_threshold = float(os.getenv("ATS_THRESHOLD", "70"))
    recruitment_system.set_ats_threshold(ats_threshold)
    
    # Get resume folder path - try multiple locations
    resume_folder = None
    possible_paths = [
        os.path.join(PROJECT_DIR, "resumes"),
        r"D:\hr-frontend\backend\resumes",
        os.path.join(os.path.dirname(__file__), "resumes")
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            resume_folder = path
            break
    
    if not resume_folder:
        print(f"❌ Resume folder not found in any of these locations: {possible_paths}")
        return 0
    
    # Get all resume files
    resume_files = [
        os.path.join(resume_folder, f)
        for f in os.listdir(resume_folder)
        if f.lower().endswith(('.pdf', '.docx', '.txt'))
    ]
    
    if not resume_files:
        print(f"⚠️  No resume files found in {resume_folder}")
        return 0
    
    print(f"📁 Found {len(resume_files)} resume files to process in {resume_folder}")
    
    # Process each resume
    session = SessionLocal()
    processed_count = 0
    shortlisted_count = 0
    
    try:
        for resume_path in resume_files:
            try:
                filename = os.path.basename(resume_path)
                print(f"\n📄 Processing resume: {filename}")
                
                # Check if already processed for this job
                existing = session.query(Candidate).filter_by(
                    resume_path=resume_path,
                    job_id=job_id
                ).first()
                
                if existing and existing.status:
                    print(f"⚠️  Resume already processed for this job: {filename}")
                    continue
                
                # Extract resume text
                resume_text = extract_text_from_resume(resume_path)
                if not resume_text:
                    print(f"⚠️  Could not extract text from {filename}")
                    continue
                
                # Create recruitment state with testlify_link
                initial_state = RecruitmentState(
                    resume_text=resume_text,
                    job_requirements=recruitment_system.job_requirements,
                    ats_threshold=ats_threshold,
                    testlify_link=invite_link  # Pass the invite link here
                )
                
                # Run the LangGraph workflow
                print(f"🔄 Running AI analysis...")
                result = recruitment_system.graph.invoke(initial_state.model_dump())
                final_state = result if isinstance(result, RecruitmentState) else RecruitmentState(**result)
                
                # Prepare candidate data
                candidate_data = {
                    "name": final_state.candidate.name,
                    "email": final_state.candidate.email,
                    "resume_path": resume_path,
                    "job_id": job_id,  # Use the job_id parameter
                    "job_title": job_title,
                    "ats_score": final_state.candidate.ats_score,
                    "status": final_state.candidate.status,
                    "score_reasoning": str(final_state.candidate.score_reasoning)[:500],
                    "assessment_invite_link": invite_link,
                    "notification_sent": final_state.candidate.notification_sent,
                    "processed_date": datetime.now()
                }
                
                # Handle email and link fields for shortlisted candidates
                if final_state.candidate.status == "Shortlisted":
                    candidate_data.update({
                        "exam_link_sent": True,
                        "exam_link_sent_date": datetime.now()
                    })
                    shortlisted_count += 1
                
                # Save or update candidate
                if existing:
                    for key, value in candidate_data.items():
                        if key != 'id':
                            setattr(existing, key, value)
                else:
                    # Check if candidate exists by email
                    existing_by_email = session.query(Candidate).filter_by(
                        email=candidate_data["email"],
                        job_id=job_id
                    ).first()
                    
                    if existing_by_email:
                        for key, value in candidate_data.items():
                            if key != 'id':
                                setattr(existing_by_email, key, value)
                    else:
                        candidate = Candidate(**candidate_data)
                        session.add(candidate)
                
                session.commit()
                processed_count += 1
                
                # Print result
                if final_state.candidate.status == "Shortlisted":
                    print(f"✅ {candidate_data['name']} - SHORTLISTED (Score: {candidate_data['ats_score']:.1f})")
                    print(f"   Email sent: {final_state.candidate.notification_sent}")
                else:
                    print(f"❌ {candidate_data['name']} - REJECTED (Score: {candidate_data['ats_score']:.1f})")
                
            except Exception as e:
                print(f"❌ Error processing resume {filename}: {str(e)}")
                import traceback
                traceback.print_exc()
                session.rollback()
                continue
        
        # Print summary
        print(f"\n" + "="*50)
        print(f"📊 RECRUITMENT SUMMARY")
        print(f"="*50)
        print(f"Total resumes processed: {processed_count}")
        print(f"Shortlisted candidates: {shortlisted_count}")
        print(f"Rejected candidates: {processed_count - shortlisted_count}")
        if invite_link and "MANUAL_UPDATE_REQUIRED" not in invite_link:
            print(f"Assessment link sent: {invite_link}")
        else:
            print(f"⚠️  No valid assessment link - please update manually in database")
        print(f"="*50)
        
    except Exception as e:
        print(f"❌ Critical error in recruitment pipeline: {str(e)}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()
    
    return processed_count  # Return the count, not the invite_linkif __name__ == "__main__":
    print("🤖 Welcome to Clint Agentic AI Recruitment System with LangGraph (DB Mode)")
    print("=" * 50)
    main()
