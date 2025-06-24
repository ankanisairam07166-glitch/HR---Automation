import os
import asyncio

from scraper import scrape_job  # Async
from clint_recruitment_system import ClintRecruitmentSystem, get_all_candidates_from_db, save_candidate_to_db, send_email_notification
from test_link import extract_invite_link_from_assessment

def get_env_var(name, default=None, cast=None):
    value = os.getenv(name, default)
    if cast and value is not None:
        try: value = cast(value)
        except: value = default
    return value

def main():
    # === 1. SCRAPE from BambooHR ===
    job_id = get_env_var("BAMBOOHR_JOB_ID", input("Enter BambooHR Job ID: "), str)
    asyncio.run(scrape_job(job_id))  # Downloads resumes to your RESUME_FOLDER

    # === 2. RUN ATS PIPELINE ===
    recruitment_system = ClintRecruitmentSystem()
    # Set job requirements from env or hardcode as needed
    recruitment_system.set_job_requirements(
        job_description=get_env_var("JOB_DESCRIPTION", "Python dev..."),
        required_skills=get_env_var("REQUIRED_SKILLS", "Python,Machine Learning,Data Analysis").split(','),
        preferred_skills=get_env_var("PREFERRED_SKILLS", "TensorFlow,PyTorch,scikit-learn,pandas").split(','),
        experience_years=get_env_var("EXPERIENCE_YEARS", 2, int)
    )
    recruitment_system.set_ats_threshold(get_env_var("ATS_THRESHOLD", 75, float))
    recruitment_system.process_all_resumes(use_threads=True)
    recruitment_system.retry_failed_notifications()
    recruitment_system.display_results()

    # === 3. GET TESTLIFY INVITE LINK ===
    assessment_name = get_env_var("ASSESSMENT_NAME", input("Enter Testlify Assessment Name: "), str)
    print(f"Extracting invite link for: {assessment_name}")
    invite_link = asyncio.run(extract_invite_link_from_assessment(assessment_name))
    if not invite_link:
        invite_link = input("Paste invite link manually: ").strip()
    print(f"Invite link: {invite_link}")

    # === 4. UPDATE DB & SEND LINK TO SHORTLISTED ===
    candidates = get_all_candidates_from_db()
    for candidate in candidates:
        if candidate.get("status") == "Shortlisted":
            candidate["testlify_link"] = invite_link
            send_email_notification(candidate, True, candidate.get("ats_score"), candidate.get("score_reasoning"))
            save_candidate_to_db(candidate)
    print("✅ All shortlisted candidates have received the invite link!")

if __name__ == "__main__":
    main()
