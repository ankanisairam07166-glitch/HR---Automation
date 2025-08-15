#!/usr/bin/env python3
"""
Environment Setup and Validation Script for TalentFlow AI
This script helps you set up and validate your environment variables.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests

def create_env_file():
    """Create a .env file template if it doesn't exist"""
    env_path = Path(".env")
    
    if env_path.exists():
        print("✅ .env file already exists")
        return True
    
    env_template = """# BambooHR Configuration
BAMBOOHR_DOMAIN=https://greenoceanpm.bamboohr.com
BAMBOOHR_EMAIL=support@smoothoperations.ai
BAMBOOHR_PASSWORD=Password1%
BAMBOOHR_API_KEY=your_bamboohr_api_key_here
BAMBOOHR_SUBDOMAIN=greenoceanpm

# OpenAI Configuration
OPENAI_API_KEY=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

# Testlify Configuration
TESTLIFY_EMAIL=jlau@knlrealty.com
TESTLIFY_2FA_WEBHOOK=https://n8n.greenoceanpropertymanagement.com/webhook/c3681f27-7826-48bf-8059-70d8c1bd1911
TESTLIFY_API_KEY=67593101297393632845404167993723

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=dnnithis@gmail.com
SENDER_PASSWORD=nnlh vsfj yxbj xbto
COMPANY_NAME=Green Ocean Property Management

# Application Settings
DOWNLOAD_DIR=./resumes
ATS_THRESHOLD=70.0
ASSESSMENT_EXPIRY_HOURS=48
ASSESSMENT_REMINDER_HOURS=24
INTERVIEW_DELAY_DAYS=3
MAX_RETRIES=3
RETRY_DELAY=2

# Admin Notifications
ADMIN_EMAIL=mg3labs@gmail.com

# Flask Environment
FLASK_ENV=development
FLASK_DEBUG=True

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/talentflow.log
"""
    
    try:
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(env_template)
        print("✅ Created .env file template")
        print("⚠️  Please edit the .env file and add your actual API keys and credentials")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def load_environment():
    """Load environment variables from .env file"""
    env_path = Path(".env")
    
    if not env_path.exists():
        print("❌ .env file not found")
        return False
    
    try:
        load_dotenv(env_path)
        print("✅ Environment variables loaded")
        return True
    except Exception as e:
        print(f"❌ Failed to load .env file: {e}")
        return False

def validate_required_vars():
    """Validate that all required environment variables are set"""
    required_vars = {
        # Critical for basic functionality
        'BAMBOOHR_DOMAIN': 'BambooHR domain URL',
        'BAMBOOHR_EMAIL': 'BambooHR login email',
        'BAMBOOHR_PASSWORD': 'BambooHR login password',
        'OPENAI_API_KEY': 'OpenAI API key for AI features',
        
        # Important for full functionality
        'BAMBOOHR_API_KEY': 'BambooHR API key (for job fetching)',
        'BAMBOOHR_SUBDOMAIN': 'BambooHR subdomain',
        'TESTLIFY_EMAIL': 'Testlify login email',
        'TESTLIFY_API_KEY': 'Testlify API key',
        
        # Optional but recommended
        'SMTP_SERVER': 'Email server for notifications',
        'SENDER_EMAIL': 'Sender email address',
        'ADMIN_EMAIL': 'Admin notification email'
    }
    
    missing_critical = []
    missing_optional = []
    configured = []
    
    critical_vars = ['BAMBOOHR_DOMAIN', 'BAMBOOHR_EMAIL', 'BAMBOOHR_PASSWORD', 'OPENAI_API_KEY']
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        
        if not value or value.startswith('your_') or value == 'your_api_key_here':
            if var in critical_vars:
                missing_critical.append(f"  - {var}: {description}")
            else:
                missing_optional.append(f"  - {var}: {description}")
        else:
            configured.append(f"  ✅ {var}: {'*' * min(len(value), 20)}...")
    
    print("\n📋 Environment Variables Status:")
    print("=" * 50)
    
    if configured:
        print("✅ Configured variables:")
        for var in configured:
            print(var)
    
    if missing_critical:
        print("\n❌ Missing CRITICAL variables (app won't work without these):")
        for var in missing_critical:
            print(var)
    
    if missing_optional:
        print("\n⚠️  Missing OPTIONAL variables (some features may not work):")
        for var in missing_optional:
            print(var)
    
    return len(missing_critical) == 0

def test_api_connections():
    """Test connections to external APIs"""
    print("\n🔗 Testing API Connections:")
    print("=" * 50)
    
    # Test OpenAI API
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key and not openai_key.startswith('your_'):
        try:
            import openai
            client = openai.OpenAI(api_key=openai_key)
            # Test with a simple request
            response = client.models.list()
            print("✅ OpenAI API: Connected successfully")
        except Exception as e:
            print(f"❌ OpenAI API: Failed - {e}")
    else:
        print("⚠️  OpenAI API: Not configured")
    
    # Test BambooHR API
    bamboo_api_key = os.getenv('BAMBOOHR_API_KEY')
    bamboo_subdomain = os.getenv('BAMBOOHR_SUBDOMAIN')
    
    if bamboo_api_key and bamboo_subdomain and not bamboo_api_key.startswith('your_'):
        try:
            auth = (bamboo_api_key, "x")
            headers = {"Accept": "application/json"}
            url = f"https://api.bamboohr.com/api/gateway.php/{bamboo_subdomain}/v1/meta/users/"
            
            response = requests.get(url, auth=auth, headers=headers, timeout=10)
            if response.status_code == 200:
                print("✅ BambooHR API: Connected successfully")
            else:
                print(f"❌ BambooHR API: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ BambooHR API: Failed - {e}")
    else:
        print("⚠️  BambooHR API: Not configured")
    
    # Test 2FA Webhook
    webhook_url = os.getenv('TESTLIFY_2FA_WEBHOOK')
    api_key = os.getenv('TESTLIFY_API_KEY')
    
    if webhook_url and api_key:
        try:
            headers = {"x-api-key": api_key}
            response = requests.get(webhook_url, headers=headers, timeout=10)
            if response.status_code == 200:
                print("✅ 2FA Webhook: Connected successfully")
            else:
                print(f"⚠️  2FA Webhook: HTTP {response.status_code} (might be normal if no recent codes)")
        except Exception as e:
            print(f"❌ 2FA Webhook: Failed - {e}")
    else:
        print("⚠️  2FA Webhook: Not configured")

def create_directories():
    """Create necessary directories"""
    directories = [
        'resumes',
        'logs',
        'assessment_links'
    ]
    
    print("\n📁 Creating directories:")
    print("=" * 50)
    
    for directory in directories:
        dir_path = Path(directory)
        try:
            dir_path.mkdir(exist_ok=True)
            print(f"✅ {directory}/")
        except Exception as e:
            print(f"❌ Failed to create {directory}/: {e}")

def install_missing_packages():
    """Check and suggest installation of missing packages"""
    required_packages = [
        'python-dotenv',
        'playwright',
        'openai',
        'requests',
        'flask',
        'flask-cors',
        'sqlalchemy'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'python-dotenv':
                import dotenv
            elif package == 'playwright':
                import playwright
            elif package == 'openai':
                import openai
            elif package == 'requests':
                import requests
            elif package == 'flask':
                import flask
            elif package == 'flask-cors':
                import flask_cors
            elif package == 'sqlalchemy':
                import sqlalchemy
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("\n📦 Missing Python packages:")
        print("=" * 50)
        print("Install missing packages with:")
        print(f"pip install {' '.join(missing_packages)}")
        
        if 'playwright' in missing_packages:
            print("\nAfter installing playwright, also run:")
            print("playwright install chromium")
    else:
        print("\n✅ All required packages are installed")

def main():
    """Main setup function"""
    print("🚀 TalentFlow AI - Environment Setup")
    print("=" * 50)
    
    # Step 1: Create .env file if needed
    print("Step 1: Checking .env file...")
    create_env_file()
    
    # Step 2: Load environment
    print("\nStep 2: Loading environment...")
    if not load_environment():
        print("❌ Cannot continue without .env file")
        return False
    
    # Step 3: Validate variables
    print("\nStep 3: Validating environment variables...")
    env_valid = validate_required_vars()
    
    # Step 4: Test API connections
    test_api_connections()
    
    # Step 5: Create directories
    create_directories()
    
    # Step 6: Check packages
    install_missing_packages()
    
    # Summary
    print("\n📊 Setup Summary:")
    print("=" * 50)
    
    if env_valid:
        print("✅ Environment setup is complete!")
        print("✅ All critical variables are configured")
        print("\n🎯 Next steps:")
        print("1. Run: python bamboo_login_test.py (to test login)")
        print("2. Run: python backend.py (to start the application)")
    else:
        print("⚠️  Environment setup needs attention!")
        print("❌ Some critical variables are missing")
        print("\n🎯 Next steps:")
        print("1. Edit the .env file and add your API keys")
        print("2. Run this script again to validate")
        print("3. Then test with: python bamboo_login_test.py")
    
    return env_valid

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)