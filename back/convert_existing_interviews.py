# convert_existing_interviews.py
from db import SessionLocal, Candidate
import json

def convert_existing_interviews():
    session = SessionLocal()
    try:
        # Get all candidates with interview data
        candidates = session.query(Candidate).filter(
            Candidate.interview_qa_pairs.isnot(None)
        ).all()
        
        for candidate in candidates:
            try:
                # Parse Q&A pairs
                qa_pairs = json.loads(candidate.interview_qa_pairs or '[]')
                
                # Build conversation
                conversation = ""
                for qa in qa_pairs:
                    if qa.get('question'):
                        conversation += f"AI Interviewer: {qa['question']}\n"
                    if qa.get('answer'):
                        conversation += f"{candidate.name}: {qa['answer']}\n"
                
                # Save conversation
                candidate.interview_conversation = conversation
                print(f"Converted interview for {candidate.name}")
                
            except Exception as e:
                print(f"Error converting candidate {candidate.id}: {e}")
        
        session.commit()
        print("Conversion complete!")
        
    finally:
        session.close()

if __name__ == "__main__":
    convert_existing_interviews()