# import requests
# import time
# import re
# from bs4 import BeautifulSoup
# import json
# import logging

# # Setup logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

# # Configuration
# BAMBOOHR_DOMAIN = "https://greenoceanpm.bamboohr.com"
# LOGIN_URL = f"{BAMBOOHR_DOMAIN}/login.php"
# BAMBOOHR_EMAIL = "support@smoothoperations.ai"
# BAMBOOHR_PASSWORD = "Password1%"

# class BambooDebugger:
#     def __init__(self):
#         self.session = requests.Session()
#         self.session.headers.update({
#             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
#             'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
#             'Accept-Language': 'en-US,en;q=0.5',
#             'Accept-Encoding': 'gzip, deflate, br',
#             'Connection': 'keep-alive',
#             'Upgrade-Insecure-Requests': '1',
#         })
    
#     def analyze_login_page(self):
#         """Analyze the login page structure in detail"""
#         try:
#             logger.info("=== ANALYZING LOGIN PAGE ===")
#             response = self.session.get(LOGIN_URL)
            
#             logger.info(f"Response status: {response.status_code}")
#             logger.info(f"Response URL: {response.url}")
#             logger.info(f"Response headers: {dict(response.headers)}")
            
#             # Save the raw HTML for inspection
#             with open("login_page_debug.html", "w", encoding="utf-8") as f:
#                 f.write(response.text)
#             logger.info("Saved raw HTML to: login_page_debug.html")
            
#             soup = BeautifulSoup(response.content, 'html.parser')
            
#             # Find all forms
#             forms = soup.find_all('form')
#             logger.info(f"Found {len(forms)} forms on the page")
            
#             for i, form in enumerate(forms):
#                 logger.info(f"\n--- FORM {i+1} ---")
#                 logger.info(f"Action: {form.get('action')}")
#                 logger.info(f"Method: {form.get('method')}")
#                 logger.info(f"ID: {form.get('id')}")
#                 logger.info(f"Class: {form.get('class')}")
                
#                 # Find all inputs in this form
#                 inputs = form.find_all('input')
#                 logger.info(f"Inputs in form {i+1}:")
#                 for input_tag in inputs:
#                     logger.info(f"  - Type: {input_tag.get('type')}, Name: {input_tag.get('name')}, Value: {input_tag.get('value')}, Placeholder: {input_tag.get('placeholder')}")
                
#                 # Find all buttons in this form
#                 buttons = form.find_all('button')
#                 logger.info(f"Buttons in form {i+1}:")
#                 for button in buttons:
#                     logger.info(f"  - Type: {button.get('type')}, Text: {button.get_text(strip=True)}, Class: {button.get('class')}")
            
#             # Look for the "Log in with Email and Password" button
#             email_buttons = soup.find_all(text=re.compile(r"Log in with Email", re.I))
#             logger.info(f"\nFound {len(email_buttons)} 'Log in with Email' text elements")
            
#             # Look for Google login button (to understand the structure)
#             google_buttons = soup.find_all(text=re.compile(r"Log in with Google", re.I))
#             logger.info(f"Found {len(google_buttons)} 'Log in with Google' text elements")
            
#             # Look for all buttons on the page
#             all_buttons = soup.find_all('button')
#             logger.info(f"\nAll buttons on page ({len(all_buttons)}):")
#             for i, button in enumerate(all_buttons):
#                 logger.info(f"  Button {i+1}: '{button.get_text(strip=True)}' - Class: {button.get('class')} - Type: {button.get('type')}")
            
#             # Check if there are any JavaScript redirects or special handling
#             scripts = soup.find_all('script')
#             logger.info(f"\nFound {len(scripts)} script tags")
            
#             return response
            
#         except Exception as e:
#             logger.error(f"Error analyzing login page: {e}")
#             return None
    
#     def test_direct_login_forms(self, response):
#         """Test different login form configurations"""
#         soup = BeautifulSoup(response.content, 'html.parser')
#         forms = soup.find_all('form')
        
#         for i, form in enumerate(forms):
#             logger.info(f"\n=== TESTING FORM {i+1} ===")
            
#             # Get form action and method
#             action = form.get('action') or LOGIN_URL
#             method = form.get('method', 'POST').upper()
            
#             if action.startswith('/'):
#                 action_url = BAMBOOHR_DOMAIN + action
#             elif action.startswith('http'):
#                 action_url = action
#             else:
#                 action_url = LOGIN_URL
            
#             logger.info(f"Form action URL: {action_url}")
#             logger.info(f"Form method: {method}")
            
#             # Collect all form data
#             form_data = {}
#             inputs = form.find_all('input')
            
#             for input_tag in inputs:
#                 input_type = input_tag.get('type', 'text')
#                 input_name = input_tag.get('name')
#                 input_value = input_tag.get('value', '')
                
#                 if input_name:
#                     if input_type.lower() == 'email' or input_name.lower() in ['email', 'username', 'user']:
#                         form_data[input_name] = BAMBOOHR_EMAIL
#                         logger.info(f"Set {input_name} = {BAMBOOHR_EMAIL}")
#                     elif input_type.lower() == 'password' or input_name.lower() == 'password':
#                         form_data[input_name] = BAMBOOHR_PASSWORD
#                         logger.info(f"Set {input_name} = [PASSWORD]")
#                     elif input_type.lower() in ['hidden', 'csrf', 'token']:
#                         form_data[input_name] = input_value
#                         logger.info(f"Set {input_name} = {input_value}")
#                     else:
#                         # For other inputs, use existing value or empty
#                         form_data[input_name] = input_value
#                         logger.info(f"Set {input_name} = {input_value}")
            
#             # Skip if no email/password fields found
#             if not any(key.lower() in ['email', 'username', 'user', 'password'] for key in form_data.keys()):
#                 logger.info("Skipping form - no email/password fields found")
#                 continue
            
#             # Try submitting this form
#             try:
#                 logger.info(f"Submitting form data: {form_data}")
                
#                 headers = {
#                     'Content-Type': 'application/x-www-form-urlencoded',
#                     'Referer': LOGIN_URL,
#                     'Origin': BAMBOOHR_DOMAIN
#                 }
                
#                 if method == 'POST':
#                     form_response = self.session.post(action_url, data=form_data, headers=headers, allow_redirects=True)
#                 else:
#                     form_response = self.session.get(action_url, params=form_data, headers=headers, allow_redirects=True)
                
#                 logger.info(f"Form response status: {form_response.status_code}")
#                 logger.info(f"Form response URL: {form_response.url}")
                
#                 # Check for success indicators
#                 content = form_response.text.lower()
#                 if any(indicator in form_response.url.lower() for indicator in ['home', 'dashboard', 'hiring', 'employee']):
#                     logger.info("🎉 SUCCESS! Login appears to have worked!")
#                     return True
#                 elif any(phrase in content for phrase in ['verification code', 'authenticator', '2fa', 'two-factor']):
#                     logger.info("🔐 2FA required - partial success!")
#                     return True
#                 elif any(phrase in content for phrase in ['invalid', 'incorrect', 'failed', 'error']):
#                     logger.warning("❌ Login failed - invalid credentials")
#                 else:
#                     logger.info("❓ Unclear result")
                
#                 # Save response for debugging
#                 with open(f"form_{i+1}_response.html", "w", encoding="utf-8") as f:
#                     f.write(form_response.text)
#                 logger.info(f"Saved response to: form_{i+1}_response.html")
                
#             except Exception as e:
#                 logger.error(f"Error submitting form {i+1}: {e}")
        
#         return False
    
#     def check_alternative_endpoints(self):
#         """Check for alternative login endpoints"""
#         logger.info("\n=== CHECKING ALTERNATIVE ENDPOINTS ===")
        
#         endpoints_to_try = [
#             "/login.php",
#             "/login",
#             "/auth/login",
#             "/authenticate",
#             "/api/login",
#             "/sessions",
#             "/signin"
#         ]
        
#         for endpoint in endpoints_to_try:
#             url = BAMBOOHR_DOMAIN + endpoint
#             try:
#                 response = self.session.get(url)
#                 logger.info(f"{endpoint}: Status {response.status_code}, URL: {response.url}")
                
#                 if response.status_code == 200 and 'login' in response.text.lower():
#                     logger.info(f"  → Potential login page found at {endpoint}")
                    
#             except Exception as e:
#                 logger.debug(f"Error checking {endpoint}: {e}")
    
#     def test_api_key_approach(self):
#         """Test if we can use API key instead of web login"""
#         logger.info("\n=== TESTING API KEY APPROACH ===")
        
#         # Try common API key locations
#         api_endpoints = [
#             "/api/gateway.php/greenoceanpm/v1/meta/users/",
#             "/api/v1/employees",
#             "/api/v1/meta/users"
#         ]
        
#         # You would need to get your actual API key for this
#         # For now, just test if the endpoints exist
#         for endpoint in api_endpoints:
#             url = f"https://api.bamboohr.com{endpoint}"
#             try:
#                 response = self.session.get(url)
#                 logger.info(f"API endpoint {endpoint}: Status {response.status_code}")
#                 if response.status_code == 401:
#                     logger.info(f"  → API endpoint exists but needs authentication")
#             except Exception as e:
#                 logger.debug(f"API endpoint {endpoint} error: {e}")

# def main():
#     """Main debug function"""
#     logger.info("🔍 BambooHR Login Debug Tool")
#     logger.info("=" * 50)
    
#     debugger = BambooDebugger()
    
#     # Step 1: Analyze the login page
#     response = debugger.analyze_login_page()
    
#     if response:
#         # Step 2: Test all forms found
#         success = debugger.test_direct_login_forms(response)
        
#         if not success:
#             # Step 3: Check alternative endpoints
#             debugger.check_alternative_endpoints()
            
#             # Step 4: Check API approach
#             debugger.test_api_key_approach()
    
#     logger.info("\n" + "=" * 50)
#     logger.info("Debug complete. Check the generated HTML files:")
#     logger.info("- login_page_debug.html (original login page)")
#     logger.info("- form_*_response.html (form submission responses)")
#     logger.info("Look for clues about the correct login method!")

# if __name__ == "__main__":
#     main()
import requests
import time
import re
from bs4 import BeautifulSoup
import json
import logging
from urllib.parse import urljoin

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
BAMBOOHR_DOMAIN = "https://greenoceanpm.bamboohr.com"
LOGIN_URL = f"{BAMBOOHR_DOMAIN}/login.php"
BAMBOOHR_EMAIL = "support@smoothoperations.ai"
BAMBOOHR_PASSWORD = "Password1%"

# 2FA Webhook
TWOFA_WEBHOOK_URL = "https://n8n.greenoceanpropertymanagement.com/webhook/2f1b815e-31d5-4f0f-b2f6-b07e7637ecf5"
TWOFA_API_KEY = "67593101297393632845404167993723"

class BambooHRClientFixed:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def get_2fa_code(self):
        """Get 2FA code from webhook"""
        try:
            headers = {"x-api-key": TWOFA_API_KEY}
            response = self.session.get(TWOFA_WEBHOOK_URL, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    token = data[0].get('output', {}).get('token') or data[0].get('token')
                elif isinstance(data, dict):
                    token = data.get('token')
                else:
                    token = None
                    
                if token:
                    logger.info(f"Got 2FA code: {token}")
                    return str(token)
                    
        except Exception as e:
            logger.error(f"Error getting 2FA code: {e}")
        return None
    
    def step1_get_initial_form(self):
        """Step 1: Get the initial login page"""
        try:
            logger.info("Step 1: Getting initial login page...")
            response = self.session.get(LOGIN_URL)
            response.raise_for_status()
            
            logger.info(f"Initial page status: {response.status_code}")
            
            # Parse the page
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the form and extract data
            form = soup.find('form', class_='sso-login')
            if not form:
                form = soup.find('form')
            
            if not form:
                logger.error("No form found on login page")
                return None, None
            
            # Extract form data
            form_data = {}
            inputs = form.find_all('input')
            for input_tag in inputs:
                name = input_tag.get('name')
                value = input_tag.get('value', '')
                if name:
                    form_data[name] = value
            
            logger.info(f"Initial form data: {form_data}")
            return form_data, response
            
        except Exception as e:
            logger.error(f"Error in step 1: {e}")
            return None, None
    
    def step2_request_email_login(self, form_data):
        """Step 2: Click 'Log in with Email and Password' to get the full form"""
        try:
            logger.info("Step 2: Requesting email/password login form...")
            
            # Prepare the data for requesting email login
            # This mimics clicking the "Log in with Email and Password" button
            login_request_data = form_data.copy()
            login_request_data['username'] = BAMBOOHR_EMAIL
            
            # Add timezone (common requirement)
            login_request_data['tz'] = 'America/New_York'  # or get from system
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': LOGIN_URL,
                'Origin': BAMBOOHR_DOMAIN,
                'X-Requested-With': 'XMLHttpRequest'  # Might be an AJAX request
            }
            
            # First, try to trigger the email login form
            response = self.session.post(LOGIN_URL, data=login_request_data, headers=headers, allow_redirects=False)
            
            logger.info(f"Email login request status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            # Check if we got redirected or if the response contains a password field
            if response.status_code == 302:
                # Follow redirect
                redirect_url = response.headers.get('Location')
                if redirect_url:
                    if redirect_url.startswith('/'):
                        redirect_url = BAMBOOHR_DOMAIN + redirect_url
                    logger.info(f"Following redirect to: {redirect_url}")
                    response = self.session.get(redirect_url)
            
            # Parse the response to see if we now have a password field
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for password field
            password_field = soup.find('input', {'type': 'password'})
            if password_field:
                logger.info("✅ Password field found! Email login form activated.")
                return self.extract_full_form_data(soup), response
            else:
                logger.info("No password field yet, trying alternative approach...")
                return self.try_alternative_approach(login_request_data)
                
        except Exception as e:
            logger.error(f"Error in step 2: {e}")
            return None, None
    
    def try_alternative_approach(self, initial_data):
        """Try alternative approach - submit with both username and password directly"""
        try:
            logger.info("Trying direct username/password submission...")
            
            # Try submitting with both username and password directly
            full_data = initial_data.copy()
            full_data.update({
                'username': BAMBOOHR_EMAIL,
                'password': BAMBOOHR_PASSWORD,
                'tz': 'America/New_York'
            })
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': LOGIN_URL,
                'Origin': BAMBOOHR_DOMAIN
            }
            
            response = self.session.post(LOGIN_URL, data=full_data, headers=headers, allow_redirects=True)
            
            logger.info(f"Direct login attempt status: {response.status_code}")
            logger.info(f"Final URL: {response.url}")
            
            return full_data, response
            
        except Exception as e:
            logger.error(f"Error in alternative approach: {e}")
            return None, None
    
    def extract_full_form_data(self, soup):
        """Extract all form data including password field"""
        form_data = {}
        
        form = soup.find('form')
        if form:
            inputs = form.find_all('input')
            for input_tag in inputs:
                name = input_tag.get('name')
                value = input_tag.get('value', '')
                input_type = input_tag.get('type', 'text')
                
                if name:
                    if input_type == 'password' or name == 'password':
                        form_data[name] = BAMBOOHR_PASSWORD
                    elif name == 'username' or name == 'email':
                        form_data[name] = BAMBOOHR_EMAIL
                    else:
                        form_data[name] = value
        
        # Ensure we have the required fields
        if 'username' not in form_data:
            form_data['username'] = BAMBOOHR_EMAIL
        if 'password' not in form_data:
            form_data['password'] = BAMBOOHR_PASSWORD
        if 'tz' not in form_data:
            form_data['tz'] = 'America/New_York'
            
        return form_data
    
    def step3_submit_credentials(self, form_data, response):
        """Step 3: Submit the complete credentials"""
        try:
            logger.info("Step 3: Submitting credentials...")
            logger.info(f"Submitting form data: {form_data}")
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': response.url,
                'Origin': BAMBOOHR_DOMAIN
            }
            
            final_response = self.session.post(LOGIN_URL, data=form_data, headers=headers, allow_redirects=True)
            
            logger.info(f"Final login status: {final_response.status_code}")
            logger.info(f"Final URL: {final_response.url}")
            
            # Check for success
            if any(indicator in final_response.url.lower() for indicator in ['home', 'dashboard', 'hiring', 'employee']):
                logger.info("✅ Login successful!")
                return 'success', final_response
            
            # Check for 2FA
            content = final_response.text.lower()
            if any(phrase in content for phrase in ['verification code', 'authenticator', '2fa', 'two-factor', 'enter code']):
                logger.info("🔐 2FA required")
                return 'needs_2fa', final_response
            
            # Check for errors
            if any(phrase in content for phrase in ['invalid', 'incorrect', 'failed', 'error']):
                logger.error("❌ Invalid credentials")
                return 'failed', final_response
            
            logger.warning("❓ Unclear login result")
            return 'unknown', final_response
            
        except Exception as e:
            logger.error(f"Error in step 3: {e}")
            return 'error', None
    
    def handle_2fa(self, response):
        """Handle 2FA if required"""
        try:
            logger.info("Handling 2FA...")
            
            # Get 2FA code
            twofa_code = self.get_2fa_code()
            if not twofa_code:
                logger.error("Failed to get 2FA code")
                return False
            
            # Parse 2FA page
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find 2FA form
            form = soup.find('form')
            if not form:
                logger.error("No 2FA form found")
                return False
            
            # Prepare 2FA data
            twofa_data = {'code': twofa_code}
            
            # Add hidden fields
            inputs = form.find_all('input', type='hidden')
            for input_tag in inputs:
                name = input_tag.get('name')
                value = input_tag.get('value', '')
                if name:
                    twofa_data[name] = value
            
            # Get form action
            action = form.get('action', '')
            if action.startswith('/'):
                twofa_url = BAMBOOHR_DOMAIN + action
            elif action.startswith('http'):
                twofa_url = action
            else:
                twofa_url = response.url
            
            # Submit 2FA
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': response.url,
                'Origin': BAMBOOHR_DOMAIN
            }
            
            twofa_response = self.session.post(twofa_url, data=twofa_data, headers=headers, allow_redirects=True)
            
            logger.info(f"2FA response status: {twofa_response.status_code}")
            logger.info(f"2FA final URL: {twofa_response.url}")
            
            # Check 2FA success
            if any(indicator in twofa_response.url.lower() for indicator in ['home', 'dashboard', 'hiring', 'employee']):
                logger.info("✅ 2FA successful!")
                return True
            
            logger.error("❌ 2FA failed")
            return False
            
        except Exception as e:
            logger.error(f"Error handling 2FA: {e}")
            return False
    
    def login(self):
        """Complete login process"""
        try:
            logger.info("🚀 Starting BambooHR login process...")
            
            # Step 1: Get initial form
            form_data, response = self.step1_get_initial_form()
            if not form_data:
                return False
            
            # Step 2: Request email login form (or try direct login)
            full_form_data, login_response = self.step2_request_email_login(form_data)
            if not full_form_data:
                return False
            
            # Step 3: Submit credentials
            status, final_response = self.step3_submit_credentials(full_form_data, login_response)
            
            if status == 'success':
                logger.info("✅ Login completed successfully!")
                return True
            elif status == 'needs_2fa':
                logger.info("🔐 Handling 2FA...")
                return self.handle_2fa(final_response)
            else:
                logger.error(f"❌ Login failed with status: {status}")
                
                # Save response for debugging
                with open("failed_login_response.html", "w", encoding="utf-8") as f:
                    f.write(final_response.text if final_response else "No response")
                logger.info("Failed response saved to: failed_login_response.html")
                
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    def get_job_candidates(self, job_id):
        """Get candidates for a specific job"""
        try:
            job_url = f"{BAMBOOHR_DOMAIN}/hiring/jobs/{job_id}"
            logger.info(f"Getting candidates for job {job_id}...")
            
            response = self.session.get(job_url)
            response.raise_for_status()
            
            # Parse the page to find candidate links
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for candidate links
            candidate_links = soup.find_all('a', href=re.compile(r'/hiring/candidates/\d+'))
            
            candidates = []
            for link in candidate_links:
                href = link.get('href')
                name = link.get_text(strip=True)
                
                # Extract candidate ID
                match = re.search(r'/hiring/candidates/(\d+)', href)
                if match:
                    candidate_id = match.group(1)
                    candidates.append({
                        'id': candidate_id,
                        'name': name,
                        'url': href
                    })
            
            # Remove duplicates
            unique_candidates = {c['id']: c for c in candidates}.values()
            candidates = list(unique_candidates)
            
            logger.info(f"Found {len(candidates)} candidates")
            return candidates
            
        except Exception as e:
            logger.error(f"Error getting candidates: {e}")
            return []

def test_fixed_login():
    """Test the fixed login process"""
    logger.info("🧪 Testing Fixed BambooHR Login")
    logger.info("=" * 50)
    
    client = BambooHRClientFixed()
    
    # Test login
    if client.login():
        logger.info("🎉 LOGIN SUCCESSFUL!")
        
        # Test getting candidates
        candidates = client.get_job_candidates("67")
        
        if candidates:
            logger.info(f"✅ Found {len(candidates)} candidates:")
            for candidate in candidates:
                logger.info(f"  - {candidate['name']} (ID: {candidate['id']})")
        else:
            logger.info("No candidates found for job 67")
            
        return True
    else:
        logger.error("❌ LOGIN FAILED!")
        return False

if __name__ == "__main__":
    test_fixed_login()