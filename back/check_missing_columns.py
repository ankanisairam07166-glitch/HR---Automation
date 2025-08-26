#!/usr/bin/env python3
"""Verify interview columns and test access"""

from db import engine, SessionLocal, Candidate
from sqlalchemy import text, inspect
import json

def verify_columns():
    # 1. Check database directly
    print("=== DATABASE COLUMNS ===")
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT name FROM pragma_table_info('candidates') WHERE name LIKE 'interview_%'"
        ))
        db_columns = [row[0] for row in result]
        print(f"Interview columns in DB: {len(db_columns)}")
        for col in sorted(db_columns):
            print(f"  - {col}")
    
    # 2. Check SQLAlchemy model
    print("\n=== SQLALCHEMY MODEL ===")
    mapper = inspect(Candidate)
    model_columns = [col.key for col in mapper.attrs if col.key.startswith('interview_')]
    print(f"Interview columns in model: {len(model_columns)}")
    for col in sorted(model_columns):
        print(f"  - {col}")
    
    # 3. Test actual access
    print("\n=== TESTING ACCESS ===")
    session = SessionLocal()
    try:
        # Get any candidate
        candidate = session.query(Candidate).first()
        if candidate:
            print(f"Testing on candidate: {candidate.name}")
            
            # Try to access the attributes
            test_attrs = [
                'interview_qa_pairs',
                'interview_conversation',
                'interview_questions_asked',
                'interview_answers_given'
            ]
            
            for attr in test_attrs:
                try:
                    value = getattr(candidate, attr, 'NOT_FOUND')
                    print(f"  {attr}: {type(value).__name__} = {str(value)[:50]}...")
                except AttributeError as e:
                    print(f"  {attr}: ❌ AttributeError - {e}")
                except Exception as e:
                    print(f"  {attr}: ❌ Error - {e}")
        else:
            print("No candidates found in database")
            
    finally:
        session.close()

if __name__ == "__main__":
    verify_columns()