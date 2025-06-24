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
#     'TIMEOUT': 120_000,
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

# # BambooHR Credentials
# BAMBOOHR_EMAIL = os.getenv("BAMBOOHR_EMAIL", "support@smoothoperations.ai")
# BAMBOOHR_PASSWORD = os.getenv("BAMBOOHR_PASSWORD", "Password1%")

# # 2FA Webhook Configuration
# TWOFA_WEBHOOK_URL = "https://n8n.greenoceanpropertymanagement.com/webhook/2f1b815e-31d5-4f0f-b2f6-b07e7637ecf5"
# TWOFA_API_KEY = "67593101297393632845404167993723"

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


# def get_2fa_code():
#     """Fetch 2FA code from the webhook endpoint"""
#     try:
#         logger.info("Fetching 2FA code from webhook...")
        
#         headers = {
#             "x-api-key": TWOFA_API_KEY
#         }
        
#         response = requests.get(TWOFA_WEBHOOK_URL, headers=headers, timeout=1000)
        
#         if response.status_code == 200:
#             data = response.json()
#             token = data.get('token')
#             seconds_remaining = data.get('secondsRemaining')
            
#             logger.info(f"✅ Got 2FA code: {token} (valid for {seconds_remaining}s)")
#             return token
#         else:
#             logger.error(f"Failed to get 2FA code. Status: {response.status_code}")
#             return None
            
#     except Exception as e:
#         logger.error(f"Error fetching 2FA code: {e}")
#         return None


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

# async def automated_login(page: Page) -> bool:
#     """Manual login helper: prompts the user to complete BambooHR login and 2FA."""
#     logger.info("🔑 Starting manual login flow...")

#     # Navigate to BambooHR login page
#     await page.goto(LOGIN_URL, timeout=CONFIG['TIMEOUT'])
#     await page.wait_for_load_state("networkidle")

#     # Prompt user to login manually
#     print("\n⚠️  Please complete the BambooHR login and any 2FA in the browser window.")
#     input("Once you're on the BambooHR dashboard, press ENTER to continue...")

#     # Wait for page to settle post-login
#     await page.wait_for_load_state("networkidle")
#     logger.info("✅ Manual login confirmed; proceeding with subsequent steps.")
#     return True

        
#     #     # Verify we're logged in by checking URL or looking for dashboard elements
#     # current_url = page.url
#     #     if "home" in current_url or "dashboard" in current_url or "hiring" in current_url:
#     #         logger.info("✅ Login successful - on dashboard/home page")
#     #         return True
        
#     #     # Also check for typical dashboard elements
#     #     try:
#     #         await page.wait_for_selector("a[href*='/hiring']", timeout=50000)
#     #         logger.info("✅ Login successful - found hiring link")
#     #         return True
#     #     except:
#     #         pass
        
#     #     logger.error(f"Login verification failed. Current URL: {current_url}")
#     #     return False
        
#     # except Exception as e:
#     #     logger.error(f"Error during automated login: {e}")
#     #     return False


# async def get_candidates_for_job(page: Page, job_id: str) -> List[Dict[str, str]]:
#     """Extract candidate information for a specific job."""
#     try:
#         job_url = f"{BAMBOOHR_DOMAIN}/hiring/jobs/{job_id}"
#         logger.info(f"→ Navigating to job page: {job_url}")
        
#         await page.goto(job_url, timeout=CONFIG['TIMEOUT'])
#         await page.wait_for_load_state("networkidle", timeout=CONFIG['TIMEOUT'])
#         await asyncio.sleep(4)
        
#         try:
#             await page.wait_for_selector("a[href*='/hiring/candidates/']", timeout=30_0000)
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
#             await page.wait_for_selector("a[href*='/files/download.php?id=']", timeout=15_0000)
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
    
#     # # Clean up old browser profiles
#     # cleanup_old_browser_profiles()
    
#     # Get unique browser profile directory
#     browser_profile_dir = "./pw_user_data"
#     os.makedirs(browser_profile_dir, exist_ok=True)
    
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
#                         args=['--no-sandbox', '--disable-setuid-sandbox']
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
                
#                 # Perform automated login
#                 login_success = await automated_login(page)
                
#                 if not login_success:
#                     logger.error("Automated login failed!")
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
#     print("BambooHR Resume Scraper with Automated Login")
#     print("=" * 50)
    
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
#     'TIMEOUT': 120_000,
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

# # BambooHR Credentials
# BAMBOOHR_EMAIL = os.getenv("BAMBOOHR_EMAIL", "support@smoothoperations.ai")
# BAMBOOHR_PASSWORD = os.getenv("BAMBOOHR_PASSWORD", "Password1%")

# # Browser profile directory for session persistence
# BROWSER_PROFILE_DIR = "./bamboohr_user_data"

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

# def sanitize_filename(name: str) -> str:
#     """Sanitize filename by removing/replacing invalid characters."""
#     sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
#     sanitized = re.sub(r'\s+', '_', sanitized.strip())
#     return sanitized[:50]

# def validate_job_id(job_id) -> bool:
#     """Validate that job_id is numeric."""
#     job_id_str = str(job_id) if isinstance(job_id, (int, str)) else ""
#     return job_id_str.isdigit() and len(job_id_str) > 0

# async def check_if_logged_in(page: Page) -> bool:
#     """Check if already logged in to BambooHR"""
#     try:
#         logger.info("Checking if already logged in...")
        
#         # Try to navigate to a protected page to test login status
#         await page.goto(f"{BAMBOOHR_DOMAIN}/home", wait_until="networkidle", timeout=50000)
#         await asyncio.sleep(2)
        
#         current_url = page.url.lower()
        
#         # Check if we're on a protected page (not redirected to login)
#         if any(indicator in current_url for indicator in ['home', 'dashboard', 'hiring', 'employees']):
#             logger.info("✅ Already logged in to BambooHR!")
#             return True
        
#         # Check for navigation elements that indicate we're logged in
#         try:
#             await page.wait_for_selector("a[href*='/hiring'], a[href*='/employees'], .navigation", timeout=1500000)
#             logger.info("✅ Found navigation elements - already logged in!")
#             return True
#         except:
#             pass
        
#         logger.info("Not logged in - will need manual login")
#         return False
        
#     except Exception as e:
#         logger.debug(f"Login check failed: {e}")
#         return False

# async def manual_login_to_bamboohr(page: Page) -> bool:
#     """Manual login helper: prompts the user to complete BambooHR login and 2FA."""
#     logger.info("🔑 Starting manual BambooHR login flow...")

#     try:
#         # Navigate to BambooHR login page
#         await page.goto(LOGIN_URL, timeout=CONFIG['TIMEOUT'])
#         await page.wait_for_load_state("networkidle")
#         await asyncio.sleep(2)

#         # Take a screenshot to help user see the page
#         await page.screenshot(path="bamboohr_login_page.png")
#         logger.info("Screenshot saved: bamboohr_login_page.png")

#         # Prompt user to login manually
#         print("\n" + "="*60)
#         print("🔐 BAMBOOHR MANUAL LOGIN REQUIRED")
#         print("="*60)
#         print("Please complete the BambooHR login in the browser window:")
#         print("1. Enter your email and password")
#         print("2. Complete any 2FA if required")
#         print("3. Wait until you see the BambooHR dashboard/home page")
#         print("4. Then come back here and press ENTER")
#         print("="*60)
        
#         input("Press ENTER after you're successfully logged in to BambooHR: ")

#         # Wait for page to settle post-login
#         await page.wait_for_load_state("networkidle")
#         await asyncio.sleep(3)
        
#         # Verify login was successful
#         if await check_if_logged_in(page):
#             logger.info("✅ Manual login confirmed and session saved!")
#             print("✅ Login successful! Your session has been saved for future use.")
#             return True
#         else:
#             logger.error("❌ Login verification failed")
#             print("❌ Login verification failed. Please try again.")
#             return False

#     except Exception as e:
#         logger.error(f"Error during manual login: {e}")
#         return False
# # Fix for browser window collapsing issue in scraper.py

# # Replace the browser launch section in your scraper.py with this:

# async def scrape_job(job_id):
#     """Main function to scrape resumes for a specific job with session persistence."""
#     job_id = str(job_id)
    
#     if not validate_job_id(job_id):
#         logger.error("Invalid job ID. Please provide a numeric job ID.")
#         raise ValueError("Invalid job ID")
    
#     Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)
#     os.makedirs(BROWSER_PROFILE_DIR, exist_ok=True)
    
#     logger.info(f"🚀 Starting BambooHR resume scraper for job ID: {job_id}")
#     logger.info(f"📁 Download directory: {DOWNLOAD_DIR}")
#     logger.info(f"🔐 Browser profile: {BROWSER_PROFILE_DIR}")
    
#     context = None
#     browser = None
    
#     try:
#         async with async_playwright() as playwright:
#             try:
#                 # Enhanced browser launch with window management
#                 logger.info(f"Launching browser with persistent session...")
                
#                 # Check if headless mode is preferred from environment
#                 headless_mode = os.getenv('PW_HEADLESS', 'False').lower() == 'true'
                
#                 context = await playwright.chromium.launch_persistent_context(
#                     user_data_dir=BROWSER_PROFILE_DIR,
#                     headless=headless_mode,
#                     user_agent=CONFIG['USER_AGENT'],
#                     viewport={'width': 1920, 'height': 1080},
#                     args=[
#                         '--no-sandbox', 
#                         '--disable-setuid-sandbox',
#                         '--disable-dev-shm-usage',
#                         '--disable-gpu',
#                         '--no-first-run',
#                         '--disable-background-timer-throttling',
#                         '--disable-backgrounding-occluded-windows',
#                         '--disable-renderer-backgrounding',
#                         '--start-maximized',  # Start maximized
#                         '--disable-features=TranslateUI',
#                         '--disable-ipc-flooding-protection',
#                         '--window-position=0,0',  # Position at top-left
#                         '--window-size=1920,1080'  # Set explicit window size
#                     ]
#                 )
                
#                 page = context.pages[0] if context.pages else await context.new_page()
                
#                 # Bring window to front and maximize
#                 try:
#                     await page.bring_to_front()
#                     await page.set_viewport_size({'width': 1920, 'height': 1080})
                    
#                     # Use JavaScript to ensure window stays focused
#                     await page.evaluate("""
#                         () => {
#                             window.focus();
#                             // Prevent window from losing focus
#                             window.addEventListener('blur', () => {
#                                 setTimeout(() => window.focus(), 100);
#                             });
#                         }
#                     """)
                    
#                     logger.info("✅ Browser window focused and maximized")
#                 except Exception as e:
#                     logger.debug(f"Window management warning: {e}")
                
#                 # Add a small delay to let window settle
#                 await asyncio.sleep(2)
                
#                 # Check if already logged in
#                 if await check_if_logged_in(page):
#                     logger.info("🎉 Using saved session - no login required!")
#                 else:
#                     # Perform manual login
#                     login_success = await manual_login_to_bamboohr(page)
                    
#                     if not login_success:
#                         logger.error("BambooHR login failed!")
#                         raise Exception("Login failed")
                
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
                    
#                     # Keep window active during processing
#                     try:
#                         await page.bring_to_front()
#                     except:
#                         pass
                    
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
                        
#                         # Keep window active during retry
#                         try:
#                             await page.bring_to_front()
#                         except:
#                             pass
                            
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
                
#                 if len(candidates) > 0:
#                     logger.info(f"Success rate: {(successful_downloads/len(candidates)*100):.1f}%")
                
#                 if failed_candidates:
#                     logger.warning("\nFailed downloads:")
#                     for candidate in failed_candidates:
#                         logger.warning(f"   - {candidate['name']} (ID: {candidate['id']})")
#                 else:
#                     logger.info("\n🎉 All resumes downloaded successfully!")
                
#                 logger.info(f"Files saved to: {DOWNLOAD_DIR}")
#                 logger.info(f"Session saved to: {BROWSER_PROFILE_DIR}")
#                 logger.info("="*60)
                
#             except Exception as e:
#                 logger.error(f"Error during scraping: {e}")
#                 raise
#             finally:
#                 # Keep session by not closing context abruptly
#                 try:
#                     if context:
#                         # Add a small delay before closing to ensure session is saved
#                         await asyncio.sleep(2)
#                         await context.close()
#                     logger.info("Browser session saved for future use")
#                 except Exception as e:
#                     logger.debug(f"Error during cleanup: {e}")
                    
#     except Exception as e:
#         logger.error(f"Fatal error: {e}")
#         raise


# # Additional helper function to add to your scraper.py:

# async def keep_window_active(page: Page):
#     """Keep the browser window active and prevent it from minimizing"""
#     try:
#         await page.bring_to_front()
#         await page.evaluate("""
#             () => {
#                 window.focus();
#                 // Scroll slightly to keep page active
#                 window.scrollBy(0, 1);
#                 window.scrollBy(0, -1);
#             }
#         """)
#     except Exception as e:
#         logger.debug(f"Window activation warning: {e}")


# # Update your get_candidates_for_job function:

# async def get_candidates_for_job(page: Page, job_id: str) -> List[Dict[str, str]]:
#     """Extract candidate information for a specific job."""
#     try:
#         job_url = f"{BAMBOOHR_DOMAIN}/hiring/jobs/{job_id}"
#         logger.info(f"→ Navigating to job page: {job_url}")
        
#         # Keep window active
#         await keep_window_active(page)
        
#         await page.goto(job_url, timeout=CONFIG['TIMEOUT'])
#         await page.wait_for_load_state("networkidle", timeout=CONFIG['TIMEOUT'])
        
#         # Keep window active after navigation
#         await keep_window_active(page)
#         await asyncio.sleep(4)
        
#         try:
#             await page.wait_for_selector("a[href*='/hiring/candidates/']", timeout=30000)
#         except:
#             logger.warning("No candidate links found - job may have no applicants")
#             return []
        
#         # Keep window active before processing
#         await keep_window_active(page)
        
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


# # Environment variable option - Add to your .env file:
# # PW_HEADLESS=False  # Set to True to run in headless mode (no window issues)
# # async def get_candidates_for_job(page: Page, job_id: str) -> List[Dict[str, str]]:
# #     """Extract candidate information for a specific job."""
# #     try:
# #         job_url = f"{BAMBOOHR_DOMAIN}/hiring/jobs/{job_id}"
# #         logger.info(f"→ Navigating to job page: {job_url}")
        
# #         await page.goto(job_url, timeout=CONFIG['TIMEOUT'])
# #         await page.wait_for_load_state("networkidle", timeout=CONFIG['TIMEOUT'])
# #         await asyncio.sleep(4)
        
# #         try:
# #             await page.wait_for_selector("a[href*='/hiring/candidates/']", timeout=300000)
# #         except:
# #             logger.warning("No candidate links found - job may have no applicants")
# #             return []
        
# #         candidates = []
# #         links = await page.locator("a[href*='/hiring/candidates/']").all()
        
# #         logger.info(f"Found {len(links)} candidate links")
        
# #         for link in links:
# #             try:
# #                 href = await link.get_attribute("href")
# #                 name = (await link.inner_text()).strip()
                
# #                 if not href or not name:
# #                     continue
                    
# #                 match = re.search(r'/hiring/candidates/(\d+)', href)
# #                 if match:
# #                     candidate_id = match.group(1)
# #                     candidates.append({
# #                         "id": candidate_id, 
# #                         "name": name,
# #                         "url": href
# #                     })
                    
# #             except Exception as e:
# #                 logger.warning(f"Error processing candidate link: {e}")
# #                 continue
        
# #         unique_candidates = {c["id"]: c for c in candidates}.values()
# #         candidates = list(unique_candidates)
        
# #         logger.info(f"Found {len(candidates)} unique candidates")
# #         for candidate in candidates:
# #             logger.info(f"   - {candidate['name']} (ID: {candidate['id']})")
            
# #         return candidates
        
# #     except Exception as e:
# #         logger.error(f"Error getting candidates for job {job_id}: {e}")
# #         return []

# async def download_resume(context: BrowserContext, page: Page, candidate: Dict[str, str]) -> bool:
#     """Download resume PDF for a specific candidate."""
#     try:
#         candidate_url = f"{BAMBOOHR_DOMAIN}/hiring/candidates/{candidate['id']}?list_type=jobs&ats-info"
#         logger.info(f"   → Processing {candidate['name']} ({candidate['id']})")
        
#         await page.goto(candidate_url, timeout=CONFIG['TIMEOUT'])
#         await page.wait_for_load_state("networkidle", timeout=CONFIG['TIMEOUT'])
#         await asyncio.sleep(1)
        
#         try:
#             await page.wait_for_selector("a[href*='/files/download.php?id=']", timeout=1500000)
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
#             "candidates": candidates,
#             "scraper_version": "2.0.0_with_session_persistence"
#         }
        
#         metadata_path = Path(DOWNLOAD_DIR) / f"job_{job_id}_metadata.json"
#         with open(metadata_path, "w", encoding="utf-8") as f:
#             json.dump(metadata, f, indent=2, ensure_ascii=False)
        
#         logger.info(f"Saved metadata to {metadata_path}")
        
#     except Exception as e:
#         logger.error(f"Error saving metadata: {e}")

# async def scrape_job(job_id):
#     """Main function to scrape resumes for a specific job with session persistence."""
#     job_id = str(job_id)
    
#     if not validate_job_id(job_id):
#         logger.error("Invalid job ID. Please provide a numeric job ID.")
#         raise ValueError("Invalid job ID")
    
#     Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)
#     os.makedirs(BROWSER_PROFILE_DIR, exist_ok=True)
    
#     logger.info(f"🚀 Starting BambooHR resume scraper for job ID: {job_id}")
#     logger.info(f"📁 Download directory: {DOWNLOAD_DIR}")
#     logger.info(f"🔐 Browser profile: {BROWSER_PROFILE_DIR}")
    
#     context = None
#     browser = None
    
#     try:
#         async with async_playwright() as playwright:
#             try:
#                 # Launch browser with persistent context for session saving
#                 logger.info(f"Launching browser with persistent session...")
                
#                 context = await playwright.chromium.launch_persistent_context(
#                     user_data_dir=BROWSER_PROFILE_DIR,
#                     headless=CONFIG['HEADLESS'],
#                     user_agent=CONFIG['USER_AGENT'],
#                     viewport={'width': 1920, 'height': 1080},
#                     args=[
#                         '--no-sandbox', 
#                         '--disable-setuid-sandbox',
#                         '--disable-dev-shm-usage'
#                     ]
#                 )
                
#                 page = context.pages[0] if context.pages else await context.new_page()
                
#                 # Check if already logged in
#                 if await check_if_logged_in(page):
#                     logger.info("🎉 Using saved session - no login required!")
#                 else:
#                     # Perform manual login
#                     login_success = await manual_login_to_bamboohr(page)
                    
#                     if not login_success:
#                         logger.error("BambooHR login failed!")
#                         raise Exception("Login failed")
                
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
#                 logger.info(f"Session saved to: {BROWSER_PROFILE_DIR}")
#                 logger.info("="*60)
                
#             except Exception as e:
#                 logger.error(f"Error during scraping: {e}")
#                 raise
#             finally:
#                 # Keep session by not closing context abruptly
#                 try:
#                     if context:
#                         await context.close()
#                     logger.info("Browser session saved for future use")
#                 except Exception as e:
#                     logger.debug(f"Error during cleanup: {e}")
                    
#     except Exception as e:
#         logger.error(f"Fatal error: {e}")
#         raise

# def clear_saved_session():
#     """Clear the saved browser session"""
#     try:
#         if os.path.exists(BROWSER_PROFILE_DIR):
#             shutil.rmtree(BROWSER_PROFILE_DIR)
#             logger.info(f"✅ Cleared saved session: {BROWSER_PROFILE_DIR}")
#             print(f"✅ Cleared saved session. Next login will require manual authentication.")
#         else:
#             logger.info("No saved session found to clear")
#             print("No saved session found to clear.")
#     except Exception as e:
#         logger.error(f"Error clearing session: {e}")
#         print(f"Error clearing session: {e}")

# def main():
#     """Entry point for the script."""
#     print("🔐 BambooHR Resume Scraper with Session Persistence")
#     print("=" * 60)
#     print("Features:")
#     print("✅ Manual login (you login once, session is saved)")
#     print("✅ Session persistence (no repeated logins)")
#     print("✅ Automatic resume downloading")
#     print("=" * 60)
    
#     try:
#         print("\nOptions:")
#         print("1. Scrape job resumes (normal mode)")
#         print("2. Clear saved session and start fresh")
        
#         choice = input("\nEnter choice (1 or 2): ").strip()
        
#         if choice == "2":
#             clear_saved_session()
#             return
        
#         job_id = input("Enter job ID to scrape: ").strip()
        
#         if not job_id:
#             print("No job ID provided")
#             return
        
#         if not validate_job_id(job_id):
#             print("Invalid job ID. Please provide a numeric value.")
#             return
        
#         asyncio.run(scrape_job(job_id))
        
#         print("\n" + "="*60)
#         print("✅ SCRAPING COMPLETED")
#         print("🔐 Your login session has been saved!")
#         print("💡 Next time you run this, login won't be required.")
#         print(f"📁 Session location: {BROWSER_PROFILE_DIR}")
#         print("🗑️  To clear session: Run this script and choose option 2")
#         print("="*60)
        
#     except KeyboardInterrupt:
#         logger.info("\nScraping interrupted by user")
#     except Exception as e:
#         logger.error(f"Error in main: {e}")

# if __name__ == "__main__":
#     main()
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
    'TIMEOUT': 100_000,
    'RETRY_DELAY': 2,
    'MAX_RETRIES': 2,
    'MIN_PDF_SIZE': 1000,
    'HEADLESS': False,
    'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# Environment variables with fallbacks
BAMBOOHR_DOMAIN = os.getenv("BAMBOOHR_DOMAIN", "https://greenoceanpm.bamboohr.com")
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", os.path.abspath("resumes"))
LOGIN_URL = BAMBOOHR_DOMAIN + "/login.php"

# BambooHR Credentials
BAMBOOHR_EMAIL = os.getenv("BAMBOOHR_EMAIL", "support@smoothoperations.ai")
BAMBOOHR_PASSWORD = os.getenv("BAMBOOHR_PASSWORD", "Password1%")

# Browser profile directory for session persistence
BROWSER_PROFILE_DIR = "./bamboohr_user_data"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bamboohr_scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configure console output for Windows
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
async def wait_for_login(page: Page) -> bool:
    """Wait for user to complete login and return success status."""
    try:
        logger.info("→ Please complete login and 2FA in the browser...")
        
        # Simple non-blocking wait - this is the key difference!
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, input, "   👉 Press ENTER after login & 2FA completion: ")
        
        await page.wait_for_load_state("networkidle", timeout=10_000)
        
        current_url = page.url
        if "login" in current_url.lower():
            logger.warning("Still on login page - login may have failed")
            return False
            
        logger.info(f"Login appears successful")
        return True
        
    except Exception as e:
        logger.error(f"Login verification failed: {e}")
        return False

def sanitize_filename(name: str) -> str:
    """Sanitize filename by removing/replacing invalid characters."""
    if not name:
        return "unknown"
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
    sanitized = re.sub(r'\s+', '_', sanitized.strip())
    return sanitized[:50]

def validate_job_id(job_id) -> bool:
    """Validate that job_id is numeric."""
    job_id_str = str(job_id) if isinstance(job_id, (int, str)) else ""
    return job_id_str.isdigit() and len(job_id_str) > 0

async def check_if_logged_in(page: Page) -> bool:
    """Check if already logged in to BambooHR"""
    try:
        logger.info("Checking if already logged in...")
        
        # Try to navigate to a protected page to test login status
        await page.goto(f"{BAMBOOHR_DOMAIN}/home", wait_until="networkidle", timeout=300000)
        await asyncio.sleep(2)
        
        current_url = page.url.lower()
        
        # Check if we're on a protected page (not redirected to login)
        if any(indicator in current_url for indicator in ['home', 'dashboard', 'hiring', 'employees']):
            logger.info("✅ Already logged in to BambooHR!")
            return True
        
        # Check for navigation elements that indicate we're logged in
        try:
            await page.wait_for_selector("a[href*='/hiring'], a[href*='/employees'], .navigation", timeout=5000)
            logger.info("✅ Found navigation elements - already logged in!")
            return True
        except:
            pass
        
        logger.info("Not logged in - will need manual login")
        return False
        
    except Exception as e:
        logger.debug(f"Login check failed: {e}")
        return False

async def manual_login_to_bamboohr(page: Page) -> bool:
    """Manual login helper: prompts the user to complete BambooHR login and 2FA."""
    logger.info("🔑 Starting manual BambooHR login flow...")

    try:
        # Navigate to BambooHR login page
        await page.goto(LOGIN_URL, timeout=CONFIG['TIMEOUT'])
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)

        # Take a screenshot to help user see the page
        await page.screenshot(path="bamboohr_login_page.png")
        logger.info("Screenshot saved: bamboohr_login_page.png")

        # Prompt user to login manually
        print("\n" + "="*60)
        print("🔐 BAMBOOHR MANUAL LOGIN REQUIRED")
        print("="*60)
        print("Please complete the BambooHR login in the browser window:")
        print("1. Enter your email and password")
        print("2. Complete any 2FA if required")
        print("3. Wait until you see the BambooHR dashboard/home page")
        print("4. Then come back here and press ENTER")
        print("="*60)
        
        input("Press ENTER after you're successfully logged in to BambooHR: ")

        # Wait for page to settle post-login
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(3)
        
        # Verify login was successful
        if await check_if_logged_in(page):
            logger.info("✅ Manual login confirmed and session saved!")
            print("✅ Login successful! Your session has been saved for future use.")
            return True
        else:
            logger.error("❌ Login verification failed")
            print("❌ Login verification failed. Please try again.")
            return False

    except Exception as e:
        logger.error(f"Error during manual login: {e}")
        return False

async def keep_window_active(page: Page):
    """Keep the browser window active and prevent it from minimizing"""
    try:
        await page.bring_to_front()
        await page.evaluate("""
            () => {
                window.focus();
                // Scroll slightly to keep page active
                window.scrollBy(0, 1);
                window.scrollBy(0, -1);
            }
        """)
    except Exception as e:
        logger.debug(f"Window activation warning: {e}")

async def get_candidates_for_job(page: Page, job_id: str) -> List[Dict[str, str]]:
    """Extract candidate information for a specific job."""
    try:
        job_url = f"{BAMBOOHR_DOMAIN}/hiring/jobs/{job_id}"
        logger.info(f"→ Navigating to job page: {job_url}")
        
        # Keep window active
        await keep_window_active(page)
        
        await page.goto(job_url, timeout=CONFIG['TIMEOUT'])
        await page.wait_for_load_state("networkidle", timeout=CONFIG['TIMEOUT'])
        
        # Keep window active after navigation
        await keep_window_active(page)
        await asyncio.sleep(4)
        
        try:
            await page.wait_for_selector("a[href*='/hiring/candidates/']", timeout=30_000)
        except:
            logger.warning("No candidate links found - job may have no applicants")
            return []
        
        # Keep window active before processing
        await keep_window_active(page)
        
        candidates = []
        links = await page.locator("a[href*='/hiring/candidates/']").all()
        
        logger.info(f"Found {len(links)} candidate links")
        
        for link in links:
            try:
                href = await link.get_attribute("href")
                name = (await link.inner_text()).strip()
                
                if not href or not name:
                    continue
                    
                match = re.search(r'/hiring/candidates/(\d+)', href)
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
        
        unique_candidates = {c["id"]: c for c in candidates}.values()
        candidates = list(unique_candidates)
        
        logger.info(f"Found {len(candidates)} unique candidates")
        for candidate in candidates:
            logger.info(f"   - {candidate['name']} (ID: {candidate['id']})")
            
        return candidates
        
    except Exception as e:
        logger.error(f"Error getting candidates for job {job_id}: {e}")
        return []

async def download_resume(context: BrowserContext, page: Page, candidate: Dict[str, str]) -> bool:
    """Download resume PDF for a specific candidate."""
    try:
        candidate_url = f"{BAMBOOHR_DOMAIN}/hiring/candidates/{candidate['id']}?list_type=jobs&ats-info"
        logger.info(f"   → Processing {candidate['name']} ({candidate['id']})")
        
        await page.goto(candidate_url, timeout=CONFIG['TIMEOUT'])
        await page.wait_for_load_state("networkidle", timeout=CONFIG['TIMEOUT'])
        await asyncio.sleep(1)
        
        try:
            await page.wait_for_selector("a[href*='/files/download.php?id=']", timeout=15_000)
        except:
            logger.warning(f"      ⚠️  No resume download link found for {candidate['name']}")
            return False
        
        download_link = page.locator("a[href*='/files/download.php?id=']").first
        href = await download_link.get_attribute("href")
        
        if not href:
            logger.warning(f"      ⚠️  Download link href is empty for {candidate['name']}")
            return False
        
        pdf_url = f"{BAMBOOHR_DOMAIN}{href}" if href.startswith('/') else href
        logger.debug(f"      Downloading from: {pdf_url}")
        
        response = await context.request.get(pdf_url)
        
        if not response.ok:
            logger.error(f"      ❌ HTTP {response.status} fetching PDF for {candidate['name']}")
            return False
        
        content_type = response.headers.get('content-type', '').lower()
        if 'pdf' not in content_type and 'application/octet-stream' not in content_type:
            logger.warning(f"      ⚠️  Unexpected content type '{content_type}' for {candidate['name']}")
        
        content = await response.body()
        
        if len(content) < CONFIG['MIN_PDF_SIZE']:
            logger.warning(f"      ⚠️  Suspiciously small file ({len(content)} bytes) for {candidate['name']}")
        
        safe_name = sanitize_filename(candidate["name"])
        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"{safe_name}_{candidate['id']}_{timestamp}.pdf"
        output_path = Path(DOWNLOAD_DIR) / filename
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "wb") as f:
            f.write(content)
        
        logger.info(f"      ✅ Saved {output_path} ({len(content):,} bytes)")
        return True
        
    except asyncio.TimeoutError:
        logger.error(f"      ❌ Timeout downloading resume for {candidate['name']}")
        return False
    except Exception as e:
        logger.error(f"      ❌ Error downloading resume for {candidate['name']}: {e}")
        return False

async def save_candidate_metadata(candidates: List[Dict], job_id: str):
    """Save candidate metadata to JSON file."""
    try:
        metadata = {
            "job_id": job_id,
            "scraped_at": datetime.now().isoformat(),
            "total_candidates": len(candidates),
            "candidates": candidates,
            "scraper_version": "2.0.0_with_session_persistence"
        }
        
        metadata_path = Path(DOWNLOAD_DIR) / f"job_{job_id}_metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved metadata to {metadata_path}")
        
    except Exception as e:
        logger.error(f"Error saving metadata: {e}")

async def scrape_job(job_id):
    """Main function to scrape resumes for a specific job with session persistence."""
    job_id = str(job_id)
    
    if not validate_job_id(job_id):
        logger.error("Invalid job ID. Please provide a numeric job ID.")
        raise ValueError("Invalid job ID")
    
    Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)
    os.makedirs(BROWSER_PROFILE_DIR, exist_ok=True)
    
    logger.info(f"🚀 Starting BambooHR resume scraper for job ID: {job_id}")
    logger.info(f"📁 Download directory: {DOWNLOAD_DIR}")
    logger.info(f"🔐 Browser profile: {BROWSER_PROFILE_DIR}")
    
    context = None
    browser = None
    
    try:
        async with async_playwright() as playwright:
            try:
                # Enhanced browser launch with window management
                logger.info(f"Launching browser with persistent session...")
                
                # Check if headless mode is preferred from environment
                headless_mode = os.getenv('PW_HEADLESS', 'False').lower() == 'true'
                try:
                    context = await playwright.chromium.launch_persistent_context(
                        user_data_dir=BROWSER_PROFILE_DIR,
                        headless=headless_mode,
                        user_agent=CONFIG['USER_AGENT'],
                        viewport={'width': 1920, 'height': 1080},
                        args=[
                            '--no-sandbox', 
                            '--disable-setuid-sandbox',
                            # '--disable-dev-shm-usage',
                            # '--disable-gpu',
                            # '--no-first-run',
                            # '--disable-background-timer-throttling',
                            # '--disable-backgrounding-occluded-windows',
                            # '--disable-renderer-backgrounding',
                            # '--start-maximized',  # Start maximized
                            # '--disable-features=TranslateUI',
                            # '--disable-ipc-flooding-protection',
                            # '--window-position=0,0',  # Position at top-left
                            # '--window-size=1920,1080'  # Set explicit window size
                        ]
                    )
                except Exception as e:
                    logger.warning(f"Failed to launch persistent context: {e}")
                    # Fallback to regular browser launch
                    browser = await playwright.chromium.launch(
                        headless=CONFIG['HEADLESS'],
                        args=['--no-sandbox', '--disable-setuid-sandbox']
                    )
                    context = await browser.new_context(
                        user_agent=CONFIG['USER_AGENT'],
                        viewport={'width': 1920, 'height': 1080}
                    )

                page = context.pages[0] if context.pages else await context.new_page()
                logger.info(f"Navigating to login page: {LOGIN_URL}")
                await page.goto(LOGIN_URL, timeout=CONFIG['TIMEOUT'])   
                login_success = await wait_for_login(page)
                if not login_success:
                    logger.error("Login failed or was not completed properly")
                    raise Exception("Login failed")
                # Bring window to front and maximize
                try:
                    await page.bring_to_front()
                    await page.set_viewport_size({'width': 1920, 'height': 1080})
                    
                    # Use JavaScript to ensure window stays focused
                    await page.evaluate("""
                        () => {
                            window.focus();
                            // Prevent window from losing focus
                            window.addEventListener('blur', () => {
                                setTimeout(() => window.focus(), 100);
                            });
                        }
                    """)
                    
                    logger.info("✅ Browser window focused and maximized")
                except Exception as e:
                    logger.debug(f"Window management warning: {e}")
                
                # Add a small delay to let window settle
                await asyncio.sleep(2)
                
                # Check if already logged in
                if await check_if_logged_in(page):
                    logger.info("🎉 Using saved session - no login required!")
                else:
                    # Perform manual login
                    login_success = await manual_login_to_bamboohr(page)
                    
                    if not login_success:
                        logger.error("BambooHR login failed!")
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
                    
                    # Keep window active during processing
                    try:
                        await page.bring_to_front()
                    except:
                        pass
                    
                    success = await download_resume(context, page, candidate)
                    if success:
                        successful_downloads += 1
                    else:
                        failed_candidates.append(candidate)
                    
                    if i < len(candidates):
                        await asyncio.sleep(CONFIG['RETRY_DELAY'])
                
                # Retry failed downloads
                if failed_candidates and CONFIG['MAX_RETRIES'] > 0:
                    logger.info(f"Retrying {len(failed_candidates)} failed downloads...")
                    still_failed = []
                    
                    for candidate in failed_candidates:
                        logger.info(f"Retrying {candidate['name']}")
                        
                        # Keep window active during retry
                        try:
                            await page.bring_to_front()
                        except:
                            pass
                            
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
                
                if len(candidates) > 0:
                    logger.info(f"Success rate: {(successful_downloads/len(candidates)*100):.1f}%")
                
                if failed_candidates:
                    logger.warning("\nFailed downloads:")
                    for candidate in failed_candidates:
                        logger.warning(f"   - {candidate['name']} (ID: {candidate['id']})")
                else:
                    logger.info("\n🎉 All resumes downloaded successfully!")
                
                logger.info(f"Files saved to: {DOWNLOAD_DIR}")
                logger.info(f"Session saved to: {BROWSER_PROFILE_DIR}")
                logger.info("="*60)
                
            except Exception as e:
                logger.error(f"Error during scraping: {e}")
                raise
            finally:
                # Keep session by not closing context abruptly
                try:
                    if context:
                        # Add a small delay before closing to ensure session is saved
                        await asyncio.sleep(2)
                        await context.close()
                    logger.info("Browser session saved for future use")
                except Exception as e:
                    logger.debug(f"Error during cleanup: {e}")
                    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

def clear_saved_session():
    """Clear the saved browser session"""
    try:
        if os.path.exists(BROWSER_PROFILE_DIR):
            shutil.rmtree(BROWSER_PROFILE_DIR)
            logger.info(f"✅ Cleared saved session: {BROWSER_PROFILE_DIR}")
            print(f"✅ Cleared saved session. Next login will require manual authentication.")
        else:
            logger.info("No saved session found to clear")
            print("No saved session found to clear.")
    except Exception as e:
        logger.error(f"Error clearing session: {e}")
        print(f"Error clearing session: {e}")

def main():
    """Entry point for the script."""
    print("🔐 BambooHR Resume Scraper with Session Persistence")
    print("=" * 60)
    print("Features:")
    print("✅ Manual login (you login once, session is saved)")
    print("✅ Session persistence (no repeated logins)")
    print("✅ Automatic resume downloading")
    print("✅ Browser window management")
    print("=" * 60)
    
    try:
        print("\nOptions:")
        print("1. Scrape job resumes (normal mode)")
        print("2. Clear saved session and start fresh")
        
        choice = input("\nEnter choice (1 or 2): ").strip()
        
        if choice == "2":
            clear_saved_session()
            return
        
        job_id = input("Enter job ID to scrape: ").strip()
        
        if not job_id:
            print("No job ID provided")
            return
        
        if not validate_job_id(job_id):
            print("Invalid job ID. Please provide a numeric value.")
            return
        
        asyncio.run(scrape_job(job_id))
        
        print("\n" + "="*60)
        print("✅ SCRAPING COMPLETED")
        print("🔐 Your login session has been saved!")
        print("💡 Next time you run this, login won't be required.")
        print(f"📁 Session location: {BROWSER_PROFILE_DIR}")
        print("🗑️  To clear session: Run this script and choose option 2")
        print("="*60)
        
    except KeyboardInterrupt:
        logger.info("\nScraping interrupted by user")
    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    main()