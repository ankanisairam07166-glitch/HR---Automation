import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

def send_email(to_email, subject, body_html, body_text=None):
    """Generic email sending function"""
    try:
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        sender_email = os.getenv("SENDER_EMAIL")
        sender_password = os.getenv("SENDER_PASSWORD")
        
        if not sender_email or not sender_password:
            logger.error("Email credentials not set in environment variables")
            return False
        
        msg = MIMEMultipart('alternative')
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add text and HTML parts
        if body_text:
            text_part = MIMEText(body_text, 'plain')
            msg.attach(text_part)
        
        html_part = MIMEText(body_html, 'html')
        msg.attach(html_part)
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending email to {to_email}: {str(e)}")
        return False


def send_interview_link_email(candidate):
    """Send interview scheduling link to candidate"""
    company_name = os.getenv("COMPANY_NAME", "TalentFlow AI")
    
    # Generate a Google Meet link (in production, integrate with Google Calendar API)
    meeting_link = candidate.interview_link or "https://meet.google.com/abc-defg-hij"
    interview_date = candidate.interview_date or datetime.now()
    
    subject = f"Interview Scheduled - {candidate.job_title} at {company_name}"
    
    body_html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">Interview Confirmation</h2>
                
                <p>Dear {candidate.name},</p>
                
                <p>Congratulations! Based on your excellent performance in the assessment, we're excited to invite you for an interview for the <strong>{candidate.job_title}</strong> position at {company_name}.</p>
                
                <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #1f2937;">Interview Details</h3>
                    <p><strong>Date & Time:</strong> {interview_date.strftime('%B %d, %Y at %I:%M %p')}</p>
                    <p><strong>Duration:</strong> 60 minutes</p>
                    <p><strong>Format:</strong> Video Interview (Google Meet)</p>
                    <p><strong>Meeting Link:</strong> <a href="{meeting_link}" style="color: #2563eb;">{meeting_link}</a></p>
                </div>
                
                <h3>What to Expect</h3>
                <ul>
                    <li>Technical discussion about your experience and skills</li>
                    <li>Problem-solving exercises relevant to the role</li>
                    <li>Discussion about the team and projects</li>
                    <li>Opportunity for you to ask questions</li>
                </ul>
                
                <h3>Preparation Tips</h3>
                <ul>
                    <li>Ensure a stable internet connection</li>
                    <li>Test your camera and microphone beforehand</li>
                    <li>Find a quiet, well-lit space</li>
                    <li>Have a copy of your resume ready</li>
                    <li>Prepare questions about the role and company</li>
                </ul>
                
                <p>If you need to reschedule, please reply to this email at least 24 hours in advance.</p>
                
                <p>We look forward to speaking with you!</p>
                
                <p>Best regards,<br>
                {company_name} Recruitment Team</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
                <p style="font-size: 12px; color: #6b7280;">
                    This is an automated message from {company_name}. If you have any questions, please reply to this email.
                </p>
            </div>
        </body>
    </html>
    """
    
    body_text = f"""
    Dear {candidate.name},
    
    Congratulations! Based on your excellent performance in the assessment, we're excited to invite you for an interview for the {candidate.job_title} position at {company_name}.
    
    Interview Details:
    - Date & Time: {interview_date.strftime('%B %d, %Y at %I:%M %p')}
    - Duration: 60 minutes
    - Format: Video Interview (Google Meet)
    - Meeting Link: {meeting_link}
    
    What to Expect:
    - Technical discussion about your experience and skills
    - Problem-solving exercises relevant to the role
    - Discussion about the team and projects
    - Opportunity for you to ask questions
    
    Preparation Tips:
    - Ensure a stable internet connection
    - Test your camera and microphone beforehand
    - Find a quiet, well-lit space
    - Have a copy of your resume ready
    - Prepare questions about the role and company
    
    If you need to reschedule, please reply to this email at least 24 hours in advance.
    
    We look forward to speaking with you!
    
    Best regards,
    {company_name} Recruitment Team
    """
    
    success = send_email(candidate.email, subject, body_html, body_text)
    return meeting_link if success else None


def send_rejection_email(candidate):
    """Send rejection email to candidate"""
    company_name = os.getenv("COMPANY_NAME", "TalentFlow AI")
    
    subject = f"Update on Your Application - {candidate.job_title} at {company_name}"
    
    body_html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <p>Dear {candidate.name},</p>
                
                <p>Thank you for your interest in the <strong>{candidate.job_title}</strong> position at {company_name} and for taking the time to complete our assessment.</p>
                
                <p>After careful consideration, we have decided to move forward with other candidates whose qualifications more closely match our current needs.</p>
                
                <p>We were impressed by many aspects of your background, and we encourage you to apply for future positions that match your skills and experience. We will keep your resume on file for future opportunities.</p>
                
                <p>We appreciate your interest in {company_name} and wish you the best in your job search.</p>
                
                <p>Best regards,<br>
                {company_name} Recruitment Team</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
                <p style="font-size: 12px; color: #6b7280;">
                    This is an automated message from {company_name}. While we cannot provide individual feedback due to the volume of applications, we appreciate your understanding.
                </p>
            </div>
        </body>
    </html>
    """
    
    body_text = f"""
    Dear {candidate.name},
    
    Thank you for your interest in the {candidate.job_title} position at {company_name} and for taking the time to complete our assessment.
    
    After careful consideration, we have decided to move forward with other candidates whose qualifications more closely match our current needs.
    
    We were impressed by many aspects of your background, and we encourage you to apply for future positions that match your skills and experience. We will keep your resume on file for future opportunities.
    
    We appreciate your interest in {company_name} and wish you the best in your job search.
    
    Best regards,
    {company_name} Recruitment Team
    """
    
    return send_email(candidate.email, subject, body_html, body_text)


def send_assessment_reminder(candidate, hours_remaining=24):
    """Send assessment reminder email"""
    company_name = os.getenv("COMPANY_NAME", "TalentFlow AI")
    
    subject = f"Reminder: Complete Your Assessment - {candidate.job_title} at {company_name}"
    
    body_html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <p>Dear {candidate.name},</p>
                
                <p>This is a friendly reminder that you have <strong>{hours_remaining} hours</strong> remaining to complete your assessment for the <strong>{candidate.job_title}</strong> position at {company_name}.</p>
                
                <div style="background-color: #fef3c7; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p style="margin: 0;"><strong>⏰ Time Remaining:</strong> {hours_remaining} hours</p>
                </div>
                
                <p>Click the link below to complete your assessment:</p>
                <p><a href="{candidate.assessment_invite_link}" style="display: inline-block; background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">Complete Assessment</a></p>
                
                <p>Don't miss this opportunity to showcase your skills!</p>
                
                <p>Best regards,<br>
                {company_name} Recruitment Team</p>
            </div>
        </body>
    </html>
    """
    
    return send_email(candidate.email, subject, body_html)