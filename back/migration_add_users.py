# migration_add_users.py
from db import engine, Base, User
from sqlalchemy import text

def create_users_table():
    """Create users table if it doesn't exist"""
    Base.metadata.create_all(engine)
    print("Users table created successfully")

if __name__ == "__main__":
    create_users_table()