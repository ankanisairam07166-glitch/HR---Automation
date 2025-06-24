# import asyncio
# import os
# import re
# import logging
# from pathlib import Path
# from typing import List, Dict, Optional
# from playwright.async_api import async_playwright, Page, BrowserContext
# import json
# from datetime import datetime
# import sys
# import time
# import shutil

# # Configuration
# CONFIG = {
#     'TIMEOUT': 120_000,  # Fixed timeout value
#     'RETRY_DELAY': 2,
#     'MAX_RETRIES': 2,
#     'MIN_PDF_SIZE': 1000,
#     'HEADLESS': False,
#     'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
# }

# # Environment variables with fallbacks
# BAMBOOHR_DOMAIN = os.getenv("BAMBOOHR_DOMAIN", "https://greenoceanpm.bamboohr.com")
# DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", os.path.abspath("resumes"))
# LOGIN_URL = BAMBOOHR_DOMAIN + "/login.php"

# # Setup logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler('bamboohr_scraper.log', encoding='utf-8'),
#         logging.StreamHandler()
#     ]
# )
# logger = logging.getLogger(__name__)

# # Configure console output for Windows
# if sys.platform == "win32":
#     os.environ["PYTHONIOENCODING"] = "utf-8"
#     if hasattr(sys.stdout, 'reconfigure'):
#         sys.stdout.reconfigure(encoding='utf-8')
#     if hasattr(sys.stderr, 'reconfigure'):
#         sys.stderr.reconfigure(encoding='utf-8')


# def get_unique_browser_profile_dir():
#     """Generate a unique browser profile directory to avoid conflicts."""
#     base_dir = "./pw_user_data"
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     unique_dir = f"{base_dir}_{timestamp}_{os.getpid()}"
#     return unique_dir


# def cleanup_old_browser_profiles():
#     """Clean up old browser profile directories."""
#     try:
#         base_dir = "./pw_user_data"
#         for item in Path(".").glob("pw_user_data_*"):
#             if item.is_dir():
#                 try:
#                     # Check if directory is older than 1 hour
#                     mtime = item.stat().st_mtime
#                     if time.time() - mtime > 3600:  # 1 hour
#                         shutil.rmtree(item)
#                         logger.info(f"Cleaned up old browser profile: {item}")
#                 except Exception as e:
#                     logger.debug(f"Could not clean up {item}: {e}")
#     except Exception as e:
#         logger.debug(f"Error during cleanup: {e}")


# def sanitize_filename(name: str) -> str:
#     """Sanitize filename by removing/replacing invalid characters."""
#     sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
#     sanitized = re.sub(r'\s+', '_', sanitized.strip())
#     return sanitized[:50]


# def validate_job_id(job_id) -> bool:
#     """Validate that job_id is numeric."""
#     job_id_str = str(job_id) if isinstance(job_id, (int, str)) else ""
#     return job_id_str.isdigit() and len(job_id_str) > 0


# async def wait_for_login(page: Page) -> bool:
#     """Wait for user to complete login and return success status."""
#     try:
#         logger.info("→ Please complete login and 2FA in the browser...")
        
#         # Create a non-blocking wait for user input
#         loop = asyncio.get_event_loop()
#         await loop.run_in_executor(None, input, "   👉 Press ENTER after login & 2FA completion: ")
        
#         await page.wait_for_load_state("networkidle", timeout=10_000)
        
#         current_url = page.url
#         if "login" in current_url.lower():
#             logger.warning("Still on login page - login may have failed")
#             return False
            
#         logger.info(f"Login appears successful")
#         return True
        
#     except Exception as e:
#         logger.error(f"Login verification failed: {e}")
#         return False


# async def get_candidates_for_job(page: Page, job_id: str) -> List[Dict[str, str]]:
#     """Extract candidate information for a specific job."""
#     try:
#         job_url = f"{BAMBOOHR_DOMAIN}/hiring/jobs/{job_id}"
#         logger.info(f"→ Navigating to job page: {job_url}")
        
#         await page.goto(job_url, timeout=CONFIG['TIMEOUT'])
#         await page.wait_for_load_state("networkidle", timeout=CONFIG['TIMEOUT'])
#         await asyncio.sleep(2)
        
#         try:
#             await page.wait_for_selector("a[href*='/hiring/candidates/']", timeout=30_000)
#         except:
#             logger.warning("No candidate links found - job may have no applicants")
#             return []
        
#         candidates = []
#         links = await page.locator("a[href*='/hiring/candidates/']").all()
        
#         logger.info(f"Found {len(links)} candidate links")
        
#         for link in links:
#             try:
#                 href = await link.get_attribute("href")
#                 name = (await link.inner_text()).strip()
                
#                 if not href or not name:
#                     continue
                    
#                 match = re.search(r'/hiring/candidates/(\d+)', href)
#                 if match:
#                     candidate_id = match.group(1)
#                     candidates.append({
#                         "id": candidate_id, 
#                         "name": name,
#                         "url": href
#                     })
                    
#             except Exception as e:
#                 logger.warning(f"Error processing candidate link: {e}")
#                 continue
        
#         unique_candidates = {c["id"]: c for c in candidates}.values()
#         candidates = list(unique_candidates)
        
#         logger.info(f"Found {len(candidates)} unique candidates")
#         for candidate in candidates:
#             logger.info(f"   - {candidate['name']} (ID: {candidate['id']})")
            
#         return candidates
        
#     except Exception as e:
#         logger.error(f"Error getting candidates for job {job_id}: {e}")
#         return []


# async def download_resume(context: BrowserContext, page: Page, candidate: Dict[str, str]) -> bool:
#     """Download resume PDF for a specific candidate."""
#     try:
#         candidate_url = f"{BAMBOOHR_DOMAIN}/hiring/candidates/{candidate['id']}?list_type=jobs&ats-info"
#         logger.info(f"   → Processing {candidate['name']} ({candidate['id']})")
        
#         await page.goto(candidate_url, timeout=CONFIG['TIMEOUT'])
#         await page.wait_for_load_state("networkidle", timeout=CONFIG['TIMEOUT'])
#         await asyncio.sleep(1)
        
#         try:
#             await page.wait_for_selector("a[href*='/files/download.php?id=']", timeout=30_000)
#         except:
#             logger.warning(f"      ⚠️  No resume download link found for {candidate['name']}")
#             return False
        
#         download_link = page.locator("a[href*='/files/download.php?id=']").first
#         href = await download_link.get_attribute("href")
        
#         if not href:
#             logger.warning(f"      ⚠️  Download link href is empty for {candidate['name']}")
#             return False
        
#         pdf_url = f"{BAMBOOHR_DOMAIN}{href}" if href.startswith('/') else href
#         logger.debug(f"      Downloading from: {pdf_url}")
        
#         response = await context.request.get(pdf_url)
        
#         if not response.ok:
#             logger.error(f"      ❌ HTTP {response.status} fetching PDF for {candidate['name']}")
#             return False
        
#         content_type = response.headers.get('content-type', '').lower()
#         if 'pdf' not in content_type and 'application/octet-stream' not in content_type:
#             logger.warning(f"      ⚠️  Unexpected content type '{content_type}' for {candidate['name']}")
        
#         content = await response.body()
        
#         if len(content) < CONFIG['MIN_PDF_SIZE']:
#             logger.warning(f"      ⚠️  Suspiciously small file ({len(content)} bytes) for {candidate['name']}")
        
#         safe_name = sanitize_filename(candidate["name"])
#         timestamp = datetime.now().strftime("%Y%m%d")
#         filename = f"{safe_name}_{candidate['id']}_{timestamp}.pdf"
#         output_path = Path(DOWNLOAD_DIR) / filename
        
#         output_path.parent.mkdir(parents=True, exist_ok=True)
        
#         with open(output_path, "wb") as f:
#             f.write(content)
        
#         logger.info(f"      ✅ Saved {output_path} ({len(content):,} bytes)")
#         return True
        
#     except asyncio.TimeoutError:
#         logger.error(f"      ❌ Timeout downloading resume for {candidate['name']}")
#         return False
#     except Exception as e:
#         logger.error(f"      ❌ Error downloading resume for {candidate['name']}: {e}")
#         return False


# async def save_candidate_metadata(candidates: List[Dict], job_id: str):
#     """Save candidate metadata to JSON file."""
#     try:
#         metadata = {
#             "job_id": job_id,
#             "scraped_at": datetime.now().isoformat(),
#             "total_candidates": len(candidates),
#             "candidates": candidates
#         }
        
#         metadata_path = Path(DOWNLOAD_DIR) / f"job_{job_id}_metadata.json"
#         with open(metadata_path, "w", encoding="utf-8") as f:
#             json.dump(metadata, f, indent=2, ensure_ascii=False)
        
#         logger.info(f"Saved metadata to {metadata_path}")
        
#     except Exception as e:
#         logger.error(f"Error saving metadata: {e}")


# async def scrape_job(job_id):
#     """Main function to scrape resumes for a specific job."""
#     job_id = str(job_id)
    
#     if not validate_job_id(job_id):
#         logger.error("Invalid job ID. Please provide a numeric job ID.")
#         raise ValueError("Invalid job ID")
    
#     Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)
    
#     logger.info(f"🚀 Starting BambooHR resume scraper for job ID: {job_id}")
#     logger.info(f"📁 Download directory: {DOWNLOAD_DIR}")
    
#     # Clean up old browser profiles
#     cleanup_old_browser_profiles()
    
#     # Get unique browser profile directory
#     browser_profile_dir = get_unique_browser_profile_dir()
    
#     browser = None
#     context = None
    
#     try:
#         async with async_playwright() as playwright:
#             try:
#                 # Try to launch browser with error handling
#                 logger.info(f"Launching browser with profile: {browser_profile_dir}")
                
#                 # First try with persistent context
#                 try:
#                     context = await playwright.chromium.launch_persistent_context(
#                         user_data_dir=browser_profile_dir,
#                         headless=CONFIG['HEADLESS'],
#                         user_agent=CONFIG['USER_AGENT'],
#                         viewport={'width': 1920, 'height': 1080},
#                         args=['--no-sandbox', '--disable-setuid-sandbox']  # Added for better compatibility
#                     )
#                 except Exception as e:
#                     logger.warning(f"Failed to launch persistent context: {e}")
#                     logger.info("Falling back to regular browser launch...")
                    
#                     # Fallback to regular browser launch
#                     browser = await playwright.chromium.launch(
#                         headless=CONFIG['HEADLESS'],
#                         args=['--no-sandbox', '--disable-setuid-sandbox']
#                     )
#                     context = await browser.new_context(
#                         user_agent=CONFIG['USER_AGENT'],
#                         viewport={'width': 1920, 'height': 1080}
#                     )
                
#                 page = await context.new_page()
                
#                 # Navigate to login page
#                 logger.info(f"Navigating to login page: {LOGIN_URL}")
#                 await page.goto(LOGIN_URL, timeout=CONFIG['TIMEOUT'])
                
#                 # Wait for manual login
#                 login_success = await wait_for_login(page)
#                 if not login_success:
#                     logger.error("Login failed or was not completed properly")
#                     raise Exception("Login failed")
                
#                 # Get candidates for the job
#                 candidates = await get_candidates_for_job(page, job_id)
                
#                 if not candidates:
#                     logger.warning("No candidates found for this job ID")
#                     return
                
#                 # Save candidate metadata
#                 await save_candidate_metadata(candidates, job_id)
                
#                 # Download resumes
#                 logger.info(f"Starting download of {len(candidates)} resumes...")
#                 failed_candidates = []
#                 successful_downloads = 0
                
#                 for i, candidate in enumerate(candidates, 1):
#                     logger.info(f"[{i}/{len(candidates)}] Processing {candidate['name']}")
                    
#                     success = await download_resume(context, page, candidate)
#                     if success:
#                         successful_downloads += 1
#                     else:
#                         failed_candidates.append(candidate)
                    
#                     if i < len(candidates):
#                         await asyncio.sleep(CONFIG['RETRY_DELAY'])
                
#                 # Retry failed downloads
#                 if failed_candidates and CONFIG['MAX_RETRIES'] > 0:
#                     logger.info(f"Retrying {len(failed_candidates)} failed downloads...")
#                     still_failed = []
                    
#                     for candidate in failed_candidates:
#                         logger.info(f"Retrying {candidate['name']}")
#                         success = await download_resume(context, page, candidate)
#                         if success:
#                             successful_downloads += 1
#                         else:
#                             still_failed.append(candidate)
                        
#                         await asyncio.sleep(CONFIG['RETRY_DELAY'])
                    
#                     failed_candidates = still_failed
                
#                 # Final summary
#                 logger.info("\n" + "="*50)
#                 logger.info("SCRAPING SUMMARY")
#                 logger.info("="*50)
#                 logger.info(f"Job ID: {job_id}")
#                 logger.info(f"Total candidates: {len(candidates)}")
#                 logger.info(f"Successful downloads: {successful_downloads}")
#                 logger.info(f"Failed downloads: {len(failed_candidates)}")
                
#                 if failed_candidates:
#                     logger.warning("\nFailed downloads:")
#                     for candidate in failed_candidates:
#                         logger.warning(f"   - {candidate['name']} (ID: {candidate['id']})")
#                 else:
#                     logger.info("\nAll resumes downloaded successfully!")
                
#                 logger.info(f"Files saved to: {DOWNLOAD_DIR}")
                
#             except Exception as e:
#                 logger.error(f"Error during scraping: {e}")
#                 raise
#             finally:
#                 # Cleanup
#                 try:
#                     if context:
#                         await context.close()
#                     if browser:
#                         await browser.close()
#                     logger.info("Browser closed")
                    
#                     # Try to remove the temporary browser profile
#                     if os.path.exists(browser_profile_dir):
#                         try:
#                             shutil.rmtree(browser_profile_dir)
#                             logger.info(f"Cleaned up browser profile: {browser_profile_dir}")
#                         except:
#                             pass
#                 except Exception as e:
#                     logger.debug(f"Error during cleanup: {e}")
                    
#     except Exception as e:
#         logger.error(f"Fatal error: {e}")
#         raise


# def main():
#     """Entry point for the script."""
#     print("BambooHR Resume Scraper")
#     print("=" * 30)
    
#     try:
#         job_id = input("Enter job ID to scrape: ").strip()
        
#         if not job_id:
#             print("No job ID provided")
#             return
        
#         if not validate_job_id(job_id):
#             print("Invalid job ID. Please provide a numeric value.")
#             return
        
#         asyncio.run(scrape_job(job_id))
        
#     except KeyboardInterrupt:
#         logger.info("\nScraping interrupted by user")
#     except Exception as e:
#         logger.error(f"Error in main: {e}")


# if __name__ == "__main__":
#     main()
# import asyncio
# import os
# import re
# import logging
# from pathlib import Path
# from typing import List, Dict, Optional
# from playwright.async_api import async_playwright, Page, BrowserContext
# import json
# from datetime import datetime
# import sys
# import time
# import shutil
# import requests

# # Configuration
# CONFIG = {
#     'TIMEOUT': 60_000,  # Reduced from 120s to 60s
#     'RETRY_DELAY': 3,   # Increased from 2s to 3s
#     'MAX_RETRIES': 3,   # Increased from 2 to 3
#     'MIN_PDF_SIZE': 1000,
#     'HEADLESS': False,
#     'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
# }

# # Environment variables with fallbacks
# BAMBOOHR_DOMAIN = os.getenv("BAMBOOHR_DOMAIN", "https://greenoceanpm.bamboohr.com")
# DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", os.path.abspath("resumes"))
# LOGIN_URL = BAMBOOHR_DOMAIN + "/login.php"

# # BambooHR Credentials
# BAMBOOHR_EMAIL = os.getenv("BAMBOOHR_EMAIL", "support@smoothoperations.ai")
# BAMBOOHR_PASSWORD = os.getenv("BAMBOOHR_PASSWORD", "Password1%")

# # 2FA Webhook Configuration
# TWOFA_WEBHOOK_URL = "https://n8n.greenoceanpropertymanagement.com/webhook/2f1b815e-31d5-4f0f-b2f6-b07e7637ecf5"
# TWOFA_API_KEY = "67593101297393632845404167993723"

# # Setup enhanced logging
# def setup_logging():
#     """Setup enhanced logging with proper formatting"""
#     logger = logging.getLogger(__name__)
#     logger.setLevel(logging.INFO)
    
#     # Clear existing handlers
#     for handler in logger.handlers[:]:
#         logger.removeHandler(handler)
    
#     # File handler
#     file_handler = logging.FileHandler('bamboohr_scraper.log', encoding='utf-8')
#     file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
#     file_handler.setFormatter(file_formatter)
    
#     # Console handler
#     console_handler = logging.StreamHandler()
#     console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
#     console_handler.setFormatter(console_formatter)
    
#     logger.addHandler(file_handler)
#     logger.addHandler(console_handler)
    
#     return logger

# logger = setup_logging()

# def get_2fa_code():
#     """Fetch 2FA code from the webhook endpoint with retry logic"""
#     max_attempts = 3
#     for attempt in range(max_attempts):
#         try:
#             logger.info(f"Fetching 2FA code from webhook (attempt {attempt + 1}/{max_attempts})...")
            
#             headers = {
#                 "x-api-key": TWOFA_API_KEY,
#                 "User-Agent": CONFIG['USER_AGENT']
#             }
            
#             response = requests.get(TWOFA_WEBHOOK_URL, headers=headers, timeout=15)
            
#             if response.status_code == 200:
#                 data = response.json()
                
#                 # Handle different response formats
#                 if isinstance(data, list) and len(data) > 0:
#                     token = data[0].get('output', {}).get('token') or data[0].get('token')
#                     seconds_remaining = data[0].get('output', {}).get('secondsRemaining') or data[0].get('secondsRemaining')
#                 elif isinstance(data, dict):
#                     token = data.get('token')
#                     seconds_remaining = data.get('secondsRemaining')
#                 else:
#                     token = None
                
#                 if token:
#                     logger.info(f"✅ Got 2FA code: {token} (valid for {seconds_remaining}s)")
#                     return str(token)
#                 else:
#                     logger.warning("2FA token not found in response")
#             else:
#                 logger.error(f"Failed to get 2FA code. Status: {response.status_code}")
                
#         except requests.exceptions.Timeout:
#             logger.warning(f"Timeout on attempt {attempt + 1}")
#         except Exception as e:
#             logger.error(f"Error fetching 2FA code (attempt {attempt + 1}): {e}")
        
#         if attempt < max_attempts - 1:
#             time.sleep(2)
    
#     return None

# async def wait_for_page_load(page: Page, timeout: int = 30000):
#     """Enhanced page load waiting with multiple strategies"""
#     try:
#         # Strategy 1: Wait for network idle
#         await page.wait_for_load_state("networkidle", timeout=timeout)
#         await asyncio.sleep(1)
#         return True
#     except:
#         try:
#             # Strategy 2: Wait for DOM content loaded
#             await page.wait_for_load_state("domcontentloaded", timeout=timeout)
#             await asyncio.sleep(2)
#             return True
#         except:
#             # Strategy 3: Just wait a bit
#             await asyncio.sleep(3)
#             return False

# async def automated_login(page: Page) -> bool:
#     """Enhanced automated login with better error handling and debugging"""
#     try:
#         logger.info("Starting automated login process...")
        
#         # Navigate to login page with retry
#         for attempt in range(3):
#             try:
#                 logger.info(f"Navigating to login page (attempt {attempt + 1}/3): {LOGIN_URL}")
#                 await page.goto(LOGIN_URL, timeout=CONFIG['TIMEOUT'])
#                 await wait_for_page_load(page)
#                 break
#             except Exception as e:
#                 logger.warning(f"Navigation attempt {attempt + 1} failed: {e}")
#                 if attempt == 2:
#                     raise
#                 await asyncio.sleep(3)
        
#         # Take a screenshot for debugging
#         await page.screenshot(path="login_page.png")
#         logger.info("Screenshot saved: login_page.png")
        
#         # Click "Log in with Email and Password" button
#         email_login_selectors = [
#             "button.js-normalLoginLink",
#             "button:has-text('Log in with Email and Password')",
#             ".js-normalLoginLink",
#             "button[class*='normalLoginLink']"
#         ]
        
#         email_login_button = None
#         for selector in email_login_selectors:
#             try:
#                 email_login_button = await page.wait_for_selector(selector, timeout=10000)
#                 if email_login_button and await email_login_button.is_visible():
#                     break
#             except:
#                 continue
        
#         if not email_login_button:
#             logger.error("Could not find email login button")
#             await page.screenshot(path="no_login_button.png")
#             # Try to continue anyway - maybe we're already on the login form
#         else:
#             await email_login_button.click()
#             logger.info("Clicked 'Log in with Email and Password'")
#             await wait_for_page_load(page)
        
#         # Wait a bit more for the form to appear
#         await asyncio.sleep(3)
        
#         # Enhanced email input finding
#         email_input = None
#         email_selectors = [
#             "input[name='email']",
#             "input[type='email']",
#             "input[id='email']",
#             "input[placeholder*='email']",
#             "input[placeholder*='Email']"
#         ]
        
#         # Check main page first
#         for selector in email_selectors:
#             try:
#                 email_input = await page.wait_for_selector(selector, timeout=5000)
#                 if email_input and await email_input.is_visible():
#                     logger.info(f"Found email input on main page with selector: {selector}")
#                     break
#             except:
#                 continue
        
#         # If not found on main page, check frames
#         if not email_input:
#             logger.info("Email input not found on main page, checking frames...")
#             for idx, frame in enumerate(page.frames):
#                 try:
#                     logger.info(f"Checking frame {idx}: {frame.url}")
#                     for selector in email_selectors:
#                         try:
#                             email_input = await frame.wait_for_selector(selector, timeout=3000)
#                             if email_input and await email_input.is_visible():
#                                 logger.info(f"Found email input in frame {idx} with selector: {selector}")
#                                 # Use the frame's page object for subsequent operations
#                                 page = frame
#                                 break
#                         except:
#                             continue
#                     if email_input:
#                         break
#                 except Exception as e:
#                     logger.warning(f"Error checking frame {idx}: {e}")
        
#         if not email_input:
#             logger.error("Could not find email input anywhere")
#             await page.screenshot(path="no_email_input.png")
#             # Log page content for debugging
#             content = await page.content()
#             logger.debug(f"Page content: {content[:1000]}...")
#             raise Exception("Email input not found")
        
#         # Clear and fill email
#         await email_input.click()
#         await email_input.fill("")
#         await email_input.type(BAMBOOHR_EMAIL, delay=100)
#         logger.info(f"Entered email: {BAMBOOHR_EMAIL}")
        
#         # Find password input
#         password_selectors = [
#             "input[name='password']",
#             "input[type='password']",
#             "input[id='password']"
#         ]
        
#         password_input = None
#         for selector in password_selectors:
#             try:
#                 password_input = await page.wait_for_selector(selector, timeout=5000)
#                 if password_input and await password_input.is_visible():
#                     break
#             except:
#                 continue
        
#         if not password_input:
#             logger.error("Could not find password input")
#             await page.screenshot(path="no_password_input.png")
#             raise Exception("Password input not found")
        
#         # Clear and fill password
#         await password_input.click()
#         await password_input.fill("")
#         await password_input.type(BAMBOOHR_PASSWORD, delay=100)
#         logger.info("Entered password")
        
#         # Find and click login button
#         login_button_selectors = [
#             "button[type='submit']",
#             "input[type='submit']",
#             "button:has-text('Log in')",
#             "button:has-text('Sign in')",
#             ".login-button"
#         ]
        
#         login_button = None
#         for selector in login_button_selectors:
#             try:
#                 login_button = await page.wait_for_selector(selector, timeout=5000)
#                 if login_button and await login_button.is_visible():
#                     break
#             except:
#                 continue
        
#         if not login_button:
#             logger.warning("Could not find login button, trying Enter key")
#             await password_input.press("Enter")
#         else:
#             await login_button.click()
#             logger.info("Clicked login button")
        
#         # Wait for navigation or response
#         await wait_for_page_load(page, timeout=15000)
#         await asyncio.sleep(3)
        
#         # Check for 2FA requirement
#         current_url = page.url
#         logger.info(f"Current URL after login: {current_url}")
        
#         # Check if we need 2FA
#         twofa_indicators = ["two-factor", "2fa", "verify", "authentication"]
#         needs_2fa = any(indicator in current_url.lower() for indicator in twofa_indicators)
        
#         if not needs_2fa:
#             # Also check page content for 2FA indicators
#             try:
#                 await page.wait_for_selector("input[type='text'], input[type='number']", timeout=3000)
#                 page_text = await page.inner_text("body")
#                 if any(phrase in page_text.lower() for phrase in ["verification code", "authenticator", "2fa", "two-factor"]):
#                     needs_2fa = True
#             except:
#                 pass
        
#         if needs_2fa:
#             logger.info("2FA page detected, fetching code...")
            
#             # Get 2FA code
#             twofa_code = get_2fa_code()
            
#             if not twofa_code:
#                 logger.error("Failed to get 2FA code")
#                 return False
            
#             # Find 2FA input
#             twofa_selectors = [
#                 "input[type='text']",
#                 "input[type='number']",
#                 "input[name*='code']",
#                 "input[id*='code']",
#                 "input[placeholder*='code']"
#             ]
            
#             twofa_input = None
#             for selector in twofa_selectors:
#                 try:
#                     twofa_input = await page.wait_for_selector(selector, timeout=5000)
#                     if twofa_input and await twofa_input.is_visible():
#                         break
#                 except:
#                     continue
            
#             if not twofa_input:
#                 logger.error("Could not find 2FA input")
#                 await page.screenshot(path="no_2fa_input.png")
#                 return False
            
#             # Enter 2FA code
#             await twofa_input.click()
#             await twofa_input.fill("")
#             await twofa_input.type(twofa_code, delay=100)
#             logger.info(f"Entered 2FA code: {twofa_code}")
            
#             # Submit 2FA
#             try:
#                 submit_btn = await page.wait_for_selector("button[type='submit']", timeout=5000)
#                 await submit_btn.click()
#                 logger.info("Clicked 2FA submit button")
#             except:
#                 logger.info("Submit button not found, trying Enter key")
#                 await twofa_input.press("Enter")
            
#             # Wait for 2FA processing
#             await wait_for_page_load(page, timeout=20000)
#             await asyncio.sleep(5)
        
#         # Verify login success
#         current_url = page.url
#         logger.info(f"Final URL: {current_url}")
        
#         # Check for login success indicators
#         success_indicators = ["home", "dashboard", "hiring", "employees"]
#         login_successful = any(indicator in current_url.lower() for indicator in success_indicators)
        
#         if not login_successful:
#             # Also check for specific elements that indicate successful login
#             try:
#                 # Look for common BambooHR navigation elements
#                 nav_selectors = [
#                     "a[href*='/hiring']",
#                     "a[href*='/employees']",
#                     ".navigation",
#                     ".main-nav",
#                     "[data-test='navigation']"
#                 ]
                
#                 for selector in nav_selectors:
#                     try:
#                         await page.wait_for_selector(selector, timeout=3000)
#                         login_successful = True
#                         logger.info(f"Found navigation element: {selector}")
#                         break
#                     except:
#                         continue
#             except:
#                 pass
        
#         if login_successful:
#             logger.info("✅ Login successful!")
#             await page.screenshot(path="login_success.png")
#             return True
#         else:
#             logger.error("❌ Login verification failed")
#             await page.screenshot(path="login_failed.png")
            
#             # Log page content for debugging
#             try:
#                 page_text = await page.inner_text("body")
#                 logger.debug(f"Page text after login: {page_text[:500]}...")
#             except:
#                 pass
            
#             return False
        
#     except Exception as e:
#         logger.error(f"Error during automated login: {e}")
#         await page.screenshot(path="login_error.png")
#         return False

# async def get_candidates_for_job(page: Page, job_id: str) -> List[Dict[str, str]]:
#     """Enhanced candidate extraction with better error handling"""
#     try:
#         job_url = f"{BAMBOOHR_DOMAIN}/hiring/jobs/{job_id}"
#         logger.info(f"→ Navigating to job page: {job_url}")
        
#         # Navigate with retry
#         for attempt in range(3):
#             try:
#                 await page.goto(job_url, timeout=CONFIG['TIMEOUT'])
#                 await wait_for_page_load(page)
#                 break
#             except Exception as e:
#                 logger.warning(f"Navigation to job page attempt {attempt + 1} failed: {e}")
#                 if attempt == 2:
#                     raise
#                 await asyncio.sleep(3)
        
#         await asyncio.sleep(2)
        
#         # Look for candidates with multiple strategies
#         candidate_selectors = [
#             "a[href*='/hiring/candidates/']",
#             "a[href*='/candidate/']",
#             "[data-test*='candidate'] a",
#             ".candidate-link"
#         ]
        
#         candidates = []
        
#         for selector in candidate_selectors:
#             try:
#                 await page.wait_for_selector(selector, timeout=10000)
#                 links = await page.locator(selector).all()
                
#                 logger.info(f"Found {len(links)} candidate links with selector: {selector}")
                
#                 for link in links:
#                     try:
#                         href = await link.get_attribute("href")
#                         name = (await link.inner_text()).strip()
                        
#                         if not href or not name:
#                             continue
                            
#                         # Extract candidate ID from URL
#                         match = re.search(r'/hiring/candidates/(\d+)', href) or re.search(r'/candidate/(\d+)', href)
#                         if match:
#                             candidate_id = match.group(1)
#                             candidates.append({
#                                 "id": candidate_id, 
#                                 "name": name,
#                                 "url": href
#                             })
                            
#                     except Exception as e:
#                         logger.warning(f"Error processing candidate link: {e}")
#                         continue
                
#                 if candidates:
#                     break
                    
#             except Exception as e:
#                 logger.debug(f"Selector {selector} failed: {e}")
#                 continue
        
#         if not candidates:
#             logger.warning("No candidate links found - job may have no applicants")
#             await page.screenshot(path=f"no_candidates_job_{job_id}.png")
#             return []
        
#         # Remove duplicates
#         unique_candidates = {c["id"]: c for c in candidates}.values()
#         candidates = list(unique_candidates)
        
#         logger.info(f"Found {len(candidates)} unique candidates")
#         for candidate in candidates:
#             logger.info(f"   - {candidate['name']} (ID: {candidate['id']})")
            
#         return candidates
        
#     except Exception as e:
#         logger.error(f"Error getting candidates for job {job_id}: {e}")
#         await page.screenshot(path=f"error_candidates_job_{job_id}.png")
#         return []

# def sanitize_filename(name: str) -> str:
#     """Sanitize filename by removing/replacing invalid characters"""
#     if not name:
#         return "unknown"
    
#     # Remove/replace invalid characters
#     sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
#     sanitized = re.sub(r'\s+', '_', sanitized.strip())
#     sanitized = re.sub(r'[^\w\-_.]', '', sanitized)
    
#     # Limit length
#     return sanitized[:50] if sanitized else "unknown"

# async def download_resume(context: BrowserContext, page: Page, candidate: Dict[str, str]) -> bool:
#     """Enhanced resume download with better error handling"""
#     try:
#         candidate_url = f"{BAMBOOHR_DOMAIN}/hiring/candidates/{candidate['id']}?list_type=jobs&ats-info"
#         logger.info(f"   → Processing {candidate['name']} ({candidate['id']})")
        
#         # Navigate to candidate page
#         for attempt in range(3):
#             try:
#                 await page.goto(candidate_url, timeout=CONFIG['TIMEOUT'])
#                 await wait_for_page_load(page)
#                 break
#             except Exception as e:
#                 logger.warning(f"Navigation to candidate page attempt {attempt + 1} failed: {e}")
#                 if attempt == 2:
#                     raise
#                 await asyncio.sleep(2)
        
#         await asyncio.sleep(1)
        
#         # Look for download links with multiple selectors
#         download_selectors = [
#             "a[href*='/files/download.php?id=']",
#             "a[href*='download']",
#             "a[download]",
#             ".download-link",
#             "[data-test*='download']"
#         ]
        
#         download_link = None
#         for selector in download_selectors:
#             try:
#                 download_link = await page.wait_for_selector(selector, timeout=5000)
#                 if download_link and await download_link.is_visible():
#                     break
#             except:
#                 continue
        
#         if not download_link:
#             logger.warning(f"      ⚠️  No resume download link found for {candidate['name']}")
#             await page.screenshot(path=f"no_download_link_{candidate['id']}.png")
#             return False
        
#         href = await download_link.get_attribute("href")
        
#         if not href:
#             logger.warning(f"      ⚠️  Download link href is empty for {candidate['name']}")
#             return False
        
#         # Construct full URL
#         if href.startswith('/'):
#             pdf_url = f"{BAMBOOHR_DOMAIN}{href}"
#         elif href.startswith('http'):
#             pdf_url = href
#         else:
#             pdf_url = f"{BAMBOOHR_DOMAIN}/{href}"
        
#         logger.debug(f"      Downloading from: {pdf_url}")
        
#         # Download with retry
#         content = None
#         for attempt in range(3):
#             try:
#                 response = await context.request.get(pdf_url, timeout=30000)
                
#                 if response.ok:
#                     content = await response.body()
#                     break
#                 else:
#                     logger.warning(f"      HTTP {response.status} on attempt {attempt + 1}")
                    
#             except Exception as e:
#                 logger.warning(f"      Download attempt {attempt + 1} failed: {e}")
                
#             if attempt < 2:
#                 await asyncio.sleep(2)
        
#         if not content:
#             logger.error(f"      ❌ Failed to download after 3 attempts for {candidate['name']}")
#             return False
        
#         # Validate content
#         if len(content) < CONFIG['MIN_PDF_SIZE']:
#             logger.warning(f"      ⚠️  Suspiciously small file ({len(content)} bytes) for {candidate['name']}")
        
#         # Generate filename
#         safe_name = sanitize_filename(candidate["name"])
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M")
#         filename = f"{safe_name}_{candidate['id']}_{timestamp}.pdf"
#         output_path = Path(DOWNLOAD_DIR) / filename
        
#         # Ensure directory exists
#         output_path.parent.mkdir(parents=True, exist_ok=True)
        
#         # Save file
#         with open(output_path, "wb") as f:
#             f.write(content)
        
#         logger.info(f"      ✅ Saved {output_path} ({len(content):,} bytes)")
#         return True
        
#     except Exception as e:
#         logger.error(f"      ❌ Error downloading resume for {candidate['name']}: {e}")
#         return False

# async def save_candidate_metadata(candidates: List[Dict], job_id: str):
#     """Save candidate metadata to JSON file"""
#     try:
#         metadata = {
#             "job_id": job_id,
#             "scraped_at": datetime.now().isoformat(),
#             "total_candidates": len(candidates),
#             "candidates": candidates,
#             "scraper_version": "2.0.0"
#         }
        
#         metadata_path = Path(DOWNLOAD_DIR) / f"job_{job_id}_metadata.json"
#         with open(metadata_path, "w", encoding="utf-8") as f:
#             json.dump(metadata, f, indent=2, ensure_ascii=False)
        
#         logger.info(f"Saved metadata to {metadata_path}")
        
#     except Exception as e:
#         logger.error(f"Error saving metadata: {e}")

# def cleanup_browser_data():
#     """Clean up browser data and temporary files"""
#     try:
#         browser_dirs = ["./pw_user_data", "./pw_user_data_*"]
#         for pattern in browser_dirs:
#             for path in Path(".").glob(pattern):
#                 if path.is_dir() and "pw_user_data" in str(path):
#                     try:
#                         shutil.rmtree(path)
#                         logger.info(f"Cleaned up: {path}")
#                     except Exception as e:
#                         logger.debug(f"Could not clean up {path}: {e}")
#     except Exception as e:
#         logger.debug(f"Cleanup error: {e}")

# def validate_job_id(job_id) -> bool:
#     """Validate that job_id is numeric"""
#     job_id_str = str(job_id) if isinstance(job_id, (int, str)) else ""
#     return job_id_str.isdigit() and len(job_id_str) > 0

# async def scrape_job(job_id):
#     """Main function to scrape resumes for a specific job with enhanced error handling"""
#     job_id = str(job_id)
    
#     if not validate_job_id(job_id):
#         logger.error("Invalid job ID. Please provide a numeric job ID.")
#         raise ValueError("Invalid job ID")
    
#     # Ensure download directory exists
#     Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)
    
#     logger.info(f"🚀 Starting BambooHR resume scraper for job ID: {job_id}")
#     logger.info(f"📁 Download directory: {DOWNLOAD_DIR}")
    
#     # Clean up old browser data
#     cleanup_browser_data()
    
#     browser = None
#     context = None
    
#     try:
#         async with async_playwright() as playwright:
#             try:
#                 # Launch browser with enhanced configuration
#                 logger.info("Launching browser...")
                
#                 browser = await playwright.chromium.launch(
#                     headless=CONFIG['HEADLESS'],
#                     args=[
#                         '--no-sandbox',
#                         '--disable-setuid-sandbox',
#                         '--disable-dev-shm-usage',
#                         '--disable-web-security',
#                         '--disable-features=VizDisplayCompositor',
#                         '--disable-gpu',
#                         '--no-first-run',
#                         '--no-default-browser-check'
#                     ]
#                 )
                
#                 context = await browser.new_context(
#                     user_agent=CONFIG['USER_AGENT'],
#                     viewport={'width': 1920, 'height': 1080},
#                     ignore_https_errors=True
#                 )
                
#                 # Set default timeouts
#                 context.set_default_timeout(CONFIG['TIMEOUT'])
                
#                 page = await context.new_page()
                
#                 # Enable request/response logging for debugging
#                 page.on("response", lambda response: logger.debug(f"Response: {response.url} - {response.status}"))
                
#                 # Perform automated login
#                 login_success = await automated_login(page)
                
#                 if not login_success:
#                     logger.error("Automated login failed!")
#                     raise Exception("Login failed")
                
#                 # Get candidates for the job
#                 candidates = await get_candidates_for_job(page, job_id)
                
#                 if not candidates:
#                     logger.warning("No candidates found for this job ID")
#                     await save_candidate_metadata([], job_id)
#                     return
                
#                 # Save candidate metadata
#                 await save_candidate_metadata(candidates, job_id)
                
#                 # Download resumes
#                 logger.info(f"Starting download of {len(candidates)} resumes...")
#                 failed_candidates = []
#                 successful_downloads = 0
                
#                 for i, candidate in enumerate(candidates, 1):
#                     logger.info(f"[{i}/{len(candidates)}] Processing {candidate['name']}")
                    
#                     success = await download_resume(context, page, candidate)
#                     if success:
#                         successful_downloads += 1
#                     else:
#                         failed_candidates.append(candidate)
                    
#                     # Add delay between downloads
#                     if i < len(candidates):
#                         await asyncio.sleep(CONFIG['RETRY_DELAY'])
                
#                 # Retry failed downloads
#                 if failed_candidates and CONFIG['MAX_RETRIES'] > 0:
#                     logger.info(f"Retrying {len(failed_candidates)} failed downloads...")
#                     still_failed = []
                    
#                     for candidate in failed_candidates:
#                         logger.info(f"Retrying {candidate['name']}")
#                         success = await download_resume(context, page, candidate)
#                         if success:
#                             successful_downloads += 1
#                         else:
#                             still_failed.append(candidate)
                        
#                         await asyncio.sleep(CONFIG['RETRY_DELAY'])
                    
#                     failed_candidates = still_failed
                
#                 # Final summary
#                 logger.info("\n" + "="*60)
#                 logger.info("SCRAPING SUMMARY")
#                 logger.info("="*60)
#                 logger.info(f"Job ID: {job_id}")
#                 logger.info(f"Total candidates: {len(candidates)}")
#                 logger.info(f"Successful downloads: {successful_downloads}")
#                 logger.info(f"Failed downloads: {len(failed_candidates)}")
#                 logger.info(f"Success rate: {(successful_downloads/len(candidates)*100):.1f}%")
                
#                 if failed_candidates:
#                     logger.warning("\nFailed downloads:")
#                     for candidate in failed_candidates:
#                         logger.warning(f"   - {candidate['name']} (ID: {candidate['id']})")
#                 else:
#                     logger.info("\n🎉 All resumes downloaded successfully!")
                
#                 logger.info(f"Files saved to: {DOWNLOAD_DIR}")
#                 logger.info("="*60)
                
#             except Exception as e:
#                 logger.error(f"Error during scraping: {e}")
#                 raise
#             finally:
#                 # Enhanced cleanup
#                 try:
#                     if page:
#                         await page.close()
#                     if context:
#                         await context.close()
#                     if browser:
#                         await browser.close()
#                     logger.info("Browser closed successfully")
#                 except Exception as e:
#                     logger.debug(f"Error during browser cleanup: {e}")
                
#                 # Clean up temporary files
#                 cleanup_browser_data()
                    
#     except Exception as e:
#         logger.error(f"Fatal error: {e}")
#         raise

# def main():
#     """Entry point for the script"""
#     print("🔧 BambooHR Resume Scraper v2.0")
#     print("=" * 50)
    
#     try:
#         job_id = input("Enter job ID to scrape: ").strip()
import asyncio
import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Page, BrowserContext
import json
from datetime import datetime
import sys
import time
import shutil
import requests

# Configuration
CONFIG = {
    'TIMEOUT': 60_000,  # Reduced from 120s to 60s
    'RETRY_DELAY': 3,   # Increased from 2s to 3s
    'MAX_RETRIES': 3,   # Increased from 2 to 3
    'MIN_PDF_SIZE': 1000,
    'HEADLESS': False,
    'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# Environment variables with fallbacks
BAMBOOHR_DOMAIN = os.getenv("BAMBOOHR_DOMAIN", "https://greenoceanpm.bamboohr.com")
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", os.path.abspath("resumes"))
LOGIN_URL = BAMBOOHR_DOMAIN + "/login.php"

# BambooHR Credentials
BAMBOOHR_EMAIL = os.getenv("BAMBOOHR_EMAIL", "support@smoothoperations.ai")
BAMBOOHR_PASSWORD = os.getenv("BAMBOOHR_PASSWORD", "Password1%")

# 2FA Webhook Configuration
TWOFA_WEBHOOK_URL = "https://n8n.greenoceanpropertymanagement.com/webhook/2f1b815e-31d5-4f0f-b2f6-b07e7637ecf5"
TWOFA_API_KEY = "67593101297393632845404167993723"

# Setup enhanced logging
def setup_logging():
    """Setup enhanced logging with proper formatting"""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # File handler
    file_handler = logging.FileHandler('bamboohr_scraper.log', encoding='utf-8')
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

def get_2fa_code():
    """Fetch 2FA code from the webhook endpoint with retry logic"""
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            logger.info(f"Fetching 2FA code from webhook (attempt {attempt + 1}/{max_attempts})...")
            
            headers = {
                "x-api-key": TWOFA_API_KEY,
                "User-Agent": CONFIG['USER_AGENT']
            }
            
            response = requests.get(TWOFA_WEBHOOK_URL, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle different response formats
                if isinstance(data, list) and len(data) > 0:
                    token = data[0].get('output', {}).get('token') or data[0].get('token')
                    seconds_remaining = data[0].get('output', {}).get('secondsRemaining') or data[0].get('secondsRemaining')
                elif isinstance(data, dict):
                    token = data.get('token')
                    seconds_remaining = data.get('secondsRemaining')
                else:
                    token = None
                
                if token:
                    logger.info(f"✅ Got 2FA code: {token} (valid for {seconds_remaining}s)")
                    return str(token)
                else:
                    logger.warning("2FA token not found in response")
            else:
                logger.error(f"Failed to get 2FA code. Status: {response.status_code}")
                
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout on attempt {attempt + 1}")
        except Exception as e:
            logger.error(f"Error fetching 2FA code (attempt {attempt + 1}): {e}")
        
        if attempt < max_attempts - 1:
            time.sleep(2)
    
    return None

async def wait_for_page_load(page: Page, timeout: int = 30000):
    """Enhanced page load waiting with multiple strategies"""
    try:
        # Strategy 1: Wait for network idle
        await page.wait_for_load_state("networkidle", timeout=timeout)
        await asyncio.sleep(1)
        return True
    except:
        try:
            # Strategy 2: Wait for DOM content loaded
            await page.wait_for_load_state("domcontentloaded", timeout=timeout)
            await asyncio.sleep(2)
            return True
        except:
            # Strategy 3: Just wait a bit
            await asyncio.sleep(3)
            return False

async def automated_login(page: Page) -> bool:
    """Enhanced automated login specifically designed for BambooHR structure"""
    try:
        logger.info("Starting automated login process...")
        
        # Navigate to login page with retry
        for attempt in range(3):
            try:
                logger.info(f"Navigating to login page (attempt {attempt + 1}/3): {LOGIN_URL}")
                await page.goto(LOGIN_URL, timeout=CONFIG['TIMEOUT'])
                await wait_for_page_load(page)
                break
            except Exception as e:
                logger.warning(f"Navigation attempt {attempt + 1} failed: {e}")
                if attempt == 2:
                    raise
                await asyncio.sleep(3)
        
        # Take a screenshot for debugging
        await page.screenshot(path="01_initial_login_page.png")
        logger.info("Screenshot saved: 01_initial_login_page.png")
        
        # Click "Log in with Email and Password" button
        email_login_selectors = [
            "button.js-normalLoginLink",
            "button:has-text('Log in with Email and Password')",
            ".js-normalLoginLink",
            "button[class*='normalLoginLink']",
            "button:has-text('Log in with Google') + * button",  # Sometimes it's the second button
            ".btn:has-text('Email')"
        ]
        
        email_login_button = None
        for i, selector in enumerate(email_login_selectors):
            try:
                logger.info(f"Trying selector {i+1}: {selector}")
                email_login_button = await page.wait_for_selector(selector, timeout=8000)
                if email_login_button and await email_login_button.is_visible():
                    logger.info(f"Found email login button with selector: {selector}")
                    break
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue
        
        if not email_login_button:
            logger.warning("Could not find email login button, checking if form is already visible")
            await page.screenshot(path="02_no_login_button.png")
            
            # Check if email form is already visible
            try:
                await page.wait_for_selector("input[type='email'], input[name='email']", timeout=3000)
                logger.info("Email form already visible, proceeding...")
            except:
                logger.error("Email form not found and login button not found")
                raise Exception("Cannot find login form or button")
        else:
            await email_login_button.click()
            logger.info("Clicked 'Log in with Email and Password'")
            
            # Wait for form to appear
            await asyncio.sleep(3)
            await wait_for_page_load(page)
        
        # Take screenshot after clicking
        await page.screenshot(path="03_after_email_button_click.png")
        
        # Now look for the email input with specific BambooHR structure
        email_input = None
        email_selectors = [
            "input[name='email']",
            "input[type='email']",
            "input[id='femail']",  # From the HTML structure visible in screenshot
            "input[placeholder*='Email']",
            ".fab-TextInput input",  # From the CSS classes visible
            "div.fab-InputWrapper input",
            "input[data-placeholder-trigger='keydown']"  # From the HTML attributes
        ]
        
        logger.info("Looking for email input field...")
        for i, selector in enumerate(email_selectors):
            try:
                logger.info(f"Trying email selector {i+1}: {selector}")
                email_input = await page.wait_for_selector(selector, timeout=8000)
                if email_input and await email_input.is_visible():
                    logger.info(f"Found email input with selector: {selector}")
                    break
            except Exception as e:
                logger.debug(f"Email selector {selector} failed: {e}")
                continue
        
        # If still not found, try more aggressive approach
        if not email_input:
            logger.info("Email input not found with standard selectors, trying iframe approach...")
            
            # Check for iframes
            frames = page.frames
            logger.info(f"Found {len(frames)} frames")
            
            for idx, frame in enumerate(frames):
                try:
                    logger.info(f"Checking frame {idx}: {frame.url}")
                    for selector in email_selectors:
                        try:
                            email_input = await frame.wait_for_selector(selector, timeout=3000)
                            if email_input and await email_input.is_visible():
                                logger.info(f"Found email input in frame {idx} with selector: {selector}")
                                # Switch to working with the frame
                                page = frame
                                break
                        except:
                            continue
                    if email_input:
                        break
                except Exception as e:
                    logger.debug(f"Error checking frame {idx}: {e}")
        
        if not email_input:
            logger.error("Could not find email input anywhere")
            await page.screenshot(path="04_no_email_input.png")
            
            # Log page HTML for debugging
            try:
                html_content = await page.content()
                with open("debug_page_content.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                logger.info("Page HTML saved to debug_page_content.html")
            except:
                pass
            
            raise Exception("Email input not found")
        
        # Clear and fill email with more robust approach
        logger.info(f"Filling email: {BAMBOOHR_EMAIL}")
        try:
            # Focus the input
            await email_input.focus()
            await asyncio.sleep(0.5)
            
            # Clear existing value
            await email_input.click()
            await page.keyboard.press("Control+a")
            await asyncio.sleep(0.2)
            
            # Type the email
            await email_input.type(BAMBOOHR_EMAIL, delay=150)
            await asyncio.sleep(0.5)
            
            # Verify email was entered
            email_value = await email_input.input_value()
            logger.info(f"Email field value: {email_value}")
            
        except Exception as e:
            logger.error(f"Error filling email: {e}")
            raise
        
        # Find password input
        password_selectors = [
            "input[name='password']",
            "input[type='password']",
            "input[id='password']",
            ".fab-TextInput input[type='password']"
        ]
        
        password_input = None
        for i, selector in enumerate(password_selectors):
            try:
                logger.info(f"Trying password selector {i+1}: {selector}")
                password_input = await page.wait_for_selector(selector, timeout=5000)
                if password_input and await password_input.is_visible():
                    logger.info(f"Found password input with selector: {selector}")
                    break
            except Exception as e:
                logger.debug(f"Password selector {selector} failed: {e}")
                continue
        
        if not password_input:
            logger.error("Could not find password input")
            await page.screenshot(path="05_no_password_input.png")
            raise Exception("Password input not found")
        
        # Fill password
        logger.info("Filling password")
        try:
            await password_input.focus()
            await asyncio.sleep(0.5)
            await password_input.click()
            await page.keyboard.press("Control+a")
            await asyncio.sleep(0.2)
            await password_input.type(BAMBOOHR_PASSWORD, delay=150)
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"Error filling password: {e}")
            raise
        
        # Take screenshot before submitting
        await page.screenshot(path="06_before_submit.png")
        
        # Find and click login button
        login_button_selectors = [
            "button[type='submit']",
            "input[type='submit']",
            "button:has-text('Log In')",
            "button:has-text('Log in')",
            "button:has-text('Sign in')",
            ".btn-primary",
            ".login-button"
        ]
        
        login_button = None
        for i, selector in enumerate(login_button_selectors):
            try:
                logger.info(f"Trying login button selector {i+1}: {selector}")
                login_button = await page.wait_for_selector(selector, timeout=5000)
                if login_button and await login_button.is_visible() and await login_button.is_enabled():
                    logger.info(f"Found login button with selector: {selector}")
                    break
            except Exception as e:
                logger.debug(f"Login button selector {selector} failed: {e}")
                continue
        
        if not login_button:
            logger.warning("Could not find login button, trying Enter key")
            await password_input.press("Enter")
        else:
            await login_button.click()
            logger.info("Clicked login button")
        
        # Wait for navigation or response
        logger.info("Waiting for login response...")
        try:
            # Wait for either navigation or specific elements
            await page.wait_for_load_state("networkidle", timeout=20000)
        except:
            # If networkidle times out, just wait a bit
            await asyncio.sleep(5)
        
        # Take screenshot after login attempt
        await page.screenshot(path="07_after_login_attempt.png")
        
        # Check current URL and page state
        current_url = page.url
        logger.info(f"Current URL after login: {current_url}")
        
        # Check if we need 2FA
        twofa_indicators = ["two-factor", "2fa", "verify", "authentication", "code"]
        needs_2fa = any(indicator in current_url.lower() for indicator in twofa_indicators)
        
        if not needs_2fa:
            # Also check page content for 2FA indicators
            try:
                page_text = await page.inner_text("body")
                if any(phrase in page_text.lower() for phrase in ["verification code", "authenticator", "2fa", "two-factor", "enter the code"]):
                    needs_2fa = True
                    logger.info("2FA detected from page content")
            except:
                pass
        
        if needs_2fa:
            logger.info("2FA page detected, processing...")
            await page.screenshot(path="08_2fa_page.png")
            
            # Get 2FA code
            twofa_code = get_2fa_code()
            
            if not twofa_code:
                logger.error("Failed to get 2FA code")
                return False
            
            # Find 2FA input
            twofa_selectors = [
                "input[type='text']",
                "input[type='number']",
                "input[name*='code']",
                "input[id*='code']",
                "input[placeholder*='code']",
                "input[placeholder*='Code']"
            ]
            
            twofa_input = None
            for selector in twofa_selectors:
                try:
                    twofa_input = await page.wait_for_selector(selector, timeout=5000)
                    if twofa_input and await twofa_input.is_visible():
                        logger.info(f"Found 2FA input with selector: {selector}")
                        break
                except:
                    continue
            
            if not twofa_input:
                logger.error("Could not find 2FA input")
                await page.screenshot(path="09_no_2fa_input.png")
                return False
            
            # Enter 2FA code
            await twofa_input.focus()
            await twofa_input.fill("")
            await twofa_input.type(twofa_code, delay=100)
            logger.info(f"Entered 2FA code: {twofa_code}")
            
            # Submit 2FA
            try:
                submit_btn = await page.wait_for_selector("button[type='submit']", timeout=5000)
                await submit_btn.click()
                logger.info("Clicked 2FA submit button")
            except:
                logger.info("Submit button not found, trying Enter key")
                await twofa_input.press("Enter")
            
            # Wait for 2FA processing
            await wait_for_page_load(page, timeout=20000)
            await asyncio.sleep(3)
            await page.screenshot(path="10_after_2fa.png")
        
        # Verify login success
        current_url = page.url
        logger.info(f"Final URL: {current_url}")
        
        # Check for login success indicators
        success_indicators = ["home", "dashboard", "hiring", "employees", "reports"]
        login_successful = any(indicator in current_url.lower() for indicator in success_indicators)
        
        if not login_successful:
            # Also check for specific elements that indicate successful login
            try:
                nav_selectors = [
                    "a[href*='/hiring']",
                    "a[href*='/employees']",
                    "nav",
                    ".navigation",
                    ".main-nav",
                    "[data-test='navigation']",
                    ".header-nav"
                ]
                
                for selector in nav_selectors:
                    try:
                        nav_element = await page.wait_for_selector(selector, timeout=3000)
                        if nav_element:
                            login_successful = True
                            logger.info(f"Found navigation element: {selector}")
                            break
                    except:
                        continue
            except:
                pass
        
        # Final verification screenshot
        await page.screenshot(path="11_final_state.png")
        
        if login_successful:
            logger.info("✅ Login successful!")
            return True
        else:
            logger.error("❌ Login verification failed")
            
            # Log page content for debugging
            try:
                page_text = await page.inner_text("body")
                logger.info(f"Page text after login: {page_text[:500]}...")
                
                # Check for error messages
                if "invalid" in page_text.lower() or "incorrect" in page_text.lower():
                    logger.error("Login credentials appear to be invalid")
                
            except:
                pass
            
            return False
        
    except Exception as e:
        logger.error(f"Error during automated login: {e}")
        await page.screenshot(path="99_login_error.png")
        return False

async def get_candidates_for_job(page: Page, job_id: str) -> List[Dict[str, str]]:
    """Enhanced candidate extraction with better error handling"""
    try:
        job_url = f"{BAMBOOHR_DOMAIN}/hiring/jobs/{job_id}"
        logger.info(f"→ Navigating to job page: {job_url}")
        
        # Navigate with retry
        for attempt in range(3):
            try:
                await page.goto(job_url, timeout=CONFIG['TIMEOUT'])
                await wait_for_page_load(page)
                break
            except Exception as e:
                logger.warning(f"Navigation to job page attempt {attempt + 1} failed: {e}")
                if attempt == 2:
                    raise
                await asyncio.sleep(3)
        
        await asyncio.sleep(2)
        
        # Look for candidates with multiple strategies
        candidate_selectors = [
            "a[href*='/hiring/candidates/']",
            "a[href*='/candidate/']",
            "[data-test*='candidate'] a",
            ".candidate-link"
        ]
        
        candidates = []
        
        for selector in candidate_selectors:
            try:
                await page.wait_for_selector(selector, timeout=10000)
                links = await page.locator(selector).all()
                
                logger.info(f"Found {len(links)} candidate links with selector: {selector}")
                
                for link in links:
                    try:
                        href = await link.get_attribute("href")
                        name = (await link.inner_text()).strip()
                        
                        if not href or not name:
                            continue
                            
                        # Extract candidate ID from URL
                        match = re.search(r'/hiring/candidates/(\d+)', href) or re.search(r'/candidate/(\d+)', href)
                        if match:
                            candidate_id = match.group(1)
                            candidates.append({
                                "id": candidate_id, 
                                "name": name,
                                "url": href
                            })
                            
                    except Exception as e:
                        logger.warning(f"Error processing candidate link: {e}")
                        continue
                
                if candidates:
                    break
                    
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue
        
        if not candidates:
            logger.warning("No candidate links found - job may have no applicants")
            await page.screenshot(path=f"no_candidates_job_{job_id}.png")
            return []
        
        # Remove duplicates
        unique_candidates = {c["id"]: c for c in candidates}.values()
        candidates = list(unique_candidates)
        
        logger.info(f"Found {len(candidates)} unique candidates")
        for candidate in candidates:
            logger.info(f"   - {candidate['name']} (ID: {candidate['id']})")
            
        return candidates
        
    except Exception as e:
        logger.error(f"Error getting candidates for job {job_id}: {e}")
        await page.screenshot(path=f"error_candidates_job_{job_id}.png")
        return []

def sanitize_filename(name: str) -> str:
    """Sanitize filename by removing/replacing invalid characters"""
    if not name:
        return "unknown"
    
    # Remove/replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
    sanitized = re.sub(r'\s+', '_', sanitized.strip())
    sanitized = re.sub(r'[^\w\-_.]', '', sanitized)
    
    # Limit length
    return sanitized[:50] if sanitized else "unknown"

async def download_resume(context: BrowserContext, page: Page, candidate: Dict[str, str]) -> bool:
    """Enhanced resume download with better error handling"""
    try:
        candidate_url = f"{BAMBOOHR_DOMAIN}/hiring/candidates/{candidate['id']}?list_type=jobs&ats-info"
        logger.info(f"   → Processing {candidate['name']} ({candidate['id']})")
        
        # Navigate to candidate page
        for attempt in range(3):
            try:
                await page.goto(candidate_url, timeout=CONFIG['TIMEOUT'])
                await wait_for_page_load(page)
                break
            except Exception as e:
                logger.warning(f"Navigation to candidate page attempt {attempt + 1} failed: {e}")
                if attempt == 2:
                    raise
                await asyncio.sleep(2)
        
        await asyncio.sleep(1)
        
        # Look for download links with multiple selectors
        download_selectors = [
            "a[href*='/files/download.php?id=']",
            "a[href*='download']",
            "a[download]",
            ".download-link",
            "[data-test*='download']"
        ]
        
        download_link = None
        for selector in download_selectors:
            try:
                download_link = await page.wait_for_selector(selector, timeout=5000)
                if download_link and await download_link.is_visible():
                    break
            except:
                continue
        
        if not download_link:
            logger.warning(f"      ⚠️  No resume download link found for {candidate['name']}")
            await page.screenshot(path=f"no_download_link_{candidate['id']}.png")
            return False
        
        href = await download_link.get_attribute("href")
        
        if not href:
            logger.warning(f"      ⚠️  Download link href is empty for {candidate['name']}")
            return False
        
        # Construct full URL
        if href.startswith('/'):
            pdf_url = f"{BAMBOOHR_DOMAIN}{href}"
        elif href.startswith('http'):
            pdf_url = href
        else:
            pdf_url = f"{BAMBOOHR_DOMAIN}/{href}"
        
        logger.debug(f"      Downloading from: {pdf_url}")
        
        # Download with retry
        content = None
        for attempt in range(3):
            try:
                response = await context.request.get(pdf_url, timeout=30000)
                
                if response.ok:
                    content = await response.body()
                    break
                else:
                    logger.warning(f"      HTTP {response.status} on attempt {attempt + 1}")
                    
            except Exception as e:
                logger.warning(f"      Download attempt {attempt + 1} failed: {e}")
                
            if attempt < 2:
                await asyncio.sleep(2)
        
        if not content:
            logger.error(f"      ❌ Failed to download after 3 attempts for {candidate['name']}")
            return False
        
        # Validate content
        if len(content) < CONFIG['MIN_PDF_SIZE']:
            logger.warning(f"      ⚠️  Suspiciously small file ({len(content)} bytes) for {candidate['name']}")
        
        # Generate filename
        safe_name = sanitize_filename(candidate["name"])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"{safe_name}_{candidate['id']}_{timestamp}.pdf"
        output_path = Path(DOWNLOAD_DIR) / filename
        
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save file
        with open(output_path, "wb") as f:
            f.write(content)
        
        logger.info(f"      ✅ Saved {output_path} ({len(content):,} bytes)")
        return True
        
    except Exception as e:
        logger.error(f"      ❌ Error downloading resume for {candidate['name']}: {e}")
        return False

async def save_candidate_metadata(candidates: List[Dict], job_id: str):
    """Save candidate metadata to JSON file"""
    try:
        metadata = {
            "job_id": job_id,
            "scraped_at": datetime.now().isoformat(),
            "total_candidates": len(candidates),
            "candidates": candidates,
            "scraper_version": "2.0.0"
        }
        
        metadata_path = Path(DOWNLOAD_DIR) / f"job_{job_id}_metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved metadata to {metadata_path}")
        
    except Exception as e:
        logger.error(f"Error saving metadata: {e}")

def cleanup_browser_data():
    """Clean up browser data and temporary files"""
    try:
        browser_dirs = ["./pw_user_data", "./pw_user_data_*"]
        for pattern in browser_dirs:
            for path in Path(".").glob(pattern):
                if path.is_dir() and "pw_user_data" in str(path):
                    try:
                        shutil.rmtree(path)
                        logger.info(f"Cleaned up: {path}")
                    except Exception as e:
                        logger.debug(f"Could not clean up {path}: {e}")
    except Exception as e:
        logger.debug(f"Cleanup error: {e}")

def validate_job_id(job_id) -> bool:
    """Validate that job_id is numeric"""
    job_id_str = str(job_id) if isinstance(job_id, (int, str)) else ""
    return job_id_str.isdigit() and len(job_id_str) > 0

async def scrape_job(job_id):
    """Main function to scrape resumes for a specific job with enhanced error handling"""
    job_id = str(job_id)
    
    if not validate_job_id(job_id):
        logger.error("Invalid job ID. Please provide a numeric job ID.")
        raise ValueError("Invalid job ID")
    
    # Ensure download directory exists
    Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)
    
    logger.info(f"🚀 Starting BambooHR resume scraper for job ID: {job_id}")
    logger.info(f"📁 Download directory: {DOWNLOAD_DIR}")
    
    # Clean up old browser data
    cleanup_browser_data()
    
    browser = None
    context = None
    
    try:
        async with async_playwright() as playwright:
            try:
                # Launch browser with enhanced configuration
                logger.info("Launching browser...")
                
                browser = await playwright.chromium.launch(
                    headless=CONFIG['HEADLESS'],
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor',
                        '--disable-gpu',
                        '--no-first-run',
                        '--no-default-browser-check'
                    ]
                )
                
                context = await browser.new_context(
                    user_agent=CONFIG['USER_AGENT'],
                    viewport={'width': 1920, 'height': 1080},
                    ignore_https_errors=True
                )
                
                # Set default timeouts
                context.set_default_timeout(CONFIG['TIMEOUT'])
                
                page = await context.new_page()
                
                # Enable request/response logging for debugging
                page.on("response", lambda response: logger.debug(f"Response: {response.url} - {response.status}"))
                
                # Perform automated login
                login_success = await automated_login(page)
                
                if not login_success:
                    logger.error("Automated login failed!")
                    raise Exception("Login failed")
                
                # Get candidates for the job
                candidates = await get_candidates_for_job(page, job_id)
                
                if not candidates:
                    logger.warning("No candidates found for this job ID")
                    await save_candidate_metadata([], job_id)
                    return
                
                # Save candidate metadata
                await save_candidate_metadata(candidates, job_id)
                
                # Download resumes
                logger.info(f"Starting download of {len(candidates)} resumes...")
                failed_candidates = []
                successful_downloads = 0
                
                for i, candidate in enumerate(candidates, 1):
                    logger.info(f"[{i}/{len(candidates)}] Processing {candidate['name']}")
                    
                    success = await download_resume(context, page, candidate)
                    if success:
                        successful_downloads += 1
                    else:
                        failed_candidates.append(candidate)
                    
                    # Add delay between downloads
                    if i < len(candidates):
                        await asyncio.sleep(CONFIG['RETRY_DELAY'])
                
                # Retry failed downloads
                if failed_candidates and CONFIG['MAX_RETRIES'] > 0:
                    logger.info(f"Retrying {len(failed_candidates)} failed downloads...")
                    still_failed = []
                    
                    for candidate in failed_candidates:
                        logger.info(f"Retrying {candidate['name']}")
                        success = await download_resume(context, page, candidate)
                        if success:
                            successful_downloads += 1
                        else:
                            still_failed.append(candidate)
                        
                        await asyncio.sleep(CONFIG['RETRY_DELAY'])
                    
                    failed_candidates = still_failed
                
                # Final summary
                logger.info("\n" + "="*60)
                logger.info("SCRAPING SUMMARY")
                logger.info("="*60)
                logger.info(f"Job ID: {job_id}")
                logger.info(f"Total candidates: {len(candidates)}")
                logger.info(f"Successful downloads: {successful_downloads}")
                logger.info(f"Failed downloads: {len(failed_candidates)}")
                logger.info(f"Success rate: {(successful_downloads/len(candidates)*100):.1f}%")
                
                if failed_candidates:
                    logger.warning("\nFailed downloads:")
                    for candidate in failed_candidates:
                        logger.warning(f"   - {candidate['name']} (ID: {candidate['id']})")
                else:
                    logger.info("\n🎉 All resumes downloaded successfully!")
                
                logger.info(f"Files saved to: {DOWNLOAD_DIR}")
                logger.info("="*60)
                
            except Exception as e:
                logger.error(f"Error during scraping: {e}")
                raise
            finally:
                # Enhanced cleanup
                try:
                    if page:
                        await page.close()
                    if context:
                        await context.close()
                    if browser:
                        await browser.close()
                    logger.info("Browser closed successfully")
                except Exception as e:
                    logger.debug(f"Error during browser cleanup: {e}")
                
                # Clean up temporary files
                cleanup_browser_data()
                    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

def main():
    """Entry point for the script"""
    print("🔧 BambooHR Resume Scraper v2.0")
    print("="*50)

    try:
        job_id = input("Enter job ID to scrape: ").strip()

        if not job_id:
            print("No job ID provided")
            return

        if not validate_job_id(job_id):
            print("Invalid job ID. Please provide a numeric value.")
            return

        asyncio.run(scrape_job(job_id))

    except KeyboardInterrupt:
        logger.info("🚫 Scraping interrupted by user")
    except Exception as e:
        logger.error(f"❌ Error in main: {e}")
    # (no finally needed if you have no cleanup to do)

if __name__ == "__main__":
    main()
