
# import asyncio
# import os
# import json
# import logging
# from pathlib import Path
# from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
# import time
# from difflib import SequenceMatcher
# from datetime import datetime
# import re
# import openai
# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# if not OPENAI_API_KEY:
#     logging.error("OPENAI_API_KEY not found in environment variables")
#     raise ValueError("OPENAI_API_KEY not found in environment variables")

# # Configuration
# TESTLIFY_EMAIL = "jlau@knlrealty.com"
# USER_DATA_DIR = r"D:\interview link\testlify_browser_profile"
# OUTPUT_DIR = "assessment_links"

# # Setup logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler('testlify_automation.log', encoding='utf-8'),
#         logging.StreamHandler()
#     ]
# )
# logger = logging.getLogger(__name__)

# async def manual_login_to_testlify(page):
#     """Manual login helper: prompts the user to complete Testlify login"""
#     logger.info("🔑 Starting manual Testlify login flow...")

#     try:
#         # Check if already logged in by trying to go to assessments
#         await page.goto("https://app.testlify.com/assessments", wait_until="networkidle")
#         await asyncio.sleep(2)
        
#         # Check if we're already logged in
#         current_url = page.url
#         if "assessments" in current_url or "dashboard" in current_url:
#             logger.info("✅ Already logged in to Testlify")
#             return True
        
#         # If not logged in, go to login page
#         logger.info("Not logged in, redirecting to login page...")
#         await page.goto("https://app.testlify.com/login", wait_until="networkidle")
#         await asyncio.sleep(2)
        
#         # Prompt user to login manually
#         print("\n⚠️  Please complete the Testlify login (including 2FA if required) in the browser window.")
#         print("Once you're on the Testlify dashboard/assessments page, press ENTER to continue...")
#         input("Press ENTER after successful login: ")

#         # Wait for page to settle post-login
#         await page.wait_for_load_state("networkidle")
#         await asyncio.sleep(2)
        
#         # Verify we're logged in
#         current_url = page.url
#         if "assessments" in current_url or "dashboard" in current_url:
#             logger.info("✅ Manual login confirmed; session will be saved for future use.")
#             return True
#         else:
#             # Try to navigate to assessments to verify
#             await page.goto("https://app.testlify.com/assessments", wait_until="networkidle")
#             await asyncio.sleep(2)
            
#             current_url = page.url
#             if "assessments" in current_url or "dashboard" in current_url:
#                 logger.info("✅ Login successful - now on assessments page")
#                 return True
#             else:
#                 logger.error("❌ Login verification failed")
#                 return False
        
#     except Exception as e:
#         logger.error(f"Error during manual login: {e}")
#         return False

# async def get_gpt_test_suggestions(job_title, job_desc=""):
#     """Get test suggestions from GPT for any job role"""

#     prompt = f"""
#     Job Title: {job_title}
#     Job Description: {job_desc if job_desc else "Not provided"}

#     Suggest 5-7 simple test search terms (1-2 words maximum) that would be relevant for this role.
#     These should be core skills that are likely to have tests in an assessment platform.

#     Return ONLY the search terms, one per line. Keep them simple and searchable.

#     Example output for "AI Engineer":
#     Python
#     Machine Learning
#     AI
#     Data Science
#     Algorithm
#     SQL
#     Statistics
#     """

#     try:
#         client = openai.OpenAI(api_key=OPENAI_API_KEY)
#         response = client.chat.completions.create(
#             model="gpt-4o",
#             messages=[{"role": "user", "content": prompt}],
#             max_tokens=150,
#             temperature=0
#         )

#         suggestions = response.choices[0].message.content.strip().split('\n')
#         suggestions = [s.strip() for s in suggestions if s.strip() and len(s.strip().split()) <= 2]
#         logger.info(f"GPT suggested tests: {suggestions}")
#         return suggestions[:7]

#     except Exception as e:
#         logger.error(f"GPT API error: {e}")
#         try:
#             simple_prompt = f"List 5 core skills for {job_title} job. One skill per line, 1-2 words only."
#             client = openai.OpenAI(api_key=OPENAI_API_KEY)
#             response = client.chat.completions.create(
#                 model="gpt-3.5-turbo",
#                 messages=[{"role": "user", "content": simple_prompt}],
#                 max_tokens=100,
#                 temperature=0.5
#             )
#             suggestions = response.choices[0].message.content.strip().split('\n')
#             suggestions = [s.strip() for s in suggestions if s.strip()][:5]
#             logger.info(f"GPT fallback suggestions: {suggestions}")
#             return suggestions

#         except Exception as e:
#             logger.error("GPT completely failed. Using generic tests.")
#             return ["Skills Assessment", "Aptitude", "General Knowledge"]

# async def select_best_test_with_gpt(page, search_term, job_title, job_desc=""):
#     """Use GPT to select the best test from search results"""
    
#     # Get all visible test cards
#     test_cards = await page.query_selector_all(".test-card, div[class*='card'], .test-item")
    
#     if not test_cards:
#         logger.warning(f"No test cards found for: {search_term}")
#         return None
    
#     # Extract test information
#     test_options = []
#     for idx, card in enumerate(test_cards[:10]):  # Limit to first 10 results
#         try:
#             # Extract test title
#             title_elem = await card.query_selector("h3, .test-title, [class*='title'], h4, h5")
#             if not title_elem:
#                 continue
                
#             test_title = await title_elem.inner_text()
            
#             # Extract test description if available
#             desc_elem = await card.query_selector("p, .test-description, .description, .test-desc")
#             test_desc = await desc_elem.inner_text() if desc_elem else ""
            
#             # Find Add button
#             add_button = await card.query_selector("button:has-text('Add'), button[class*='add'], .add-btn")
            
#             test_options.append({
#                 "index": idx,
#                 "title": test_title.strip(),
#                 "description": test_desc.strip()[:100],  # Limit description length
#                 "card": card,
#                 "add_button": add_button
#             })
            
#         except Exception as e:
#             logger.debug(f"Error processing card {idx}: {e}")
#             continue
    
#     if not test_options:
#         logger.warning("No valid test options found")
#         return None
    
#     # Use GPT to select the best test
#     prompt = f"""
#     Job Title: {job_title}
#     Search Term: {search_term}
    
#     Which of these tests is most appropriate for this role? Reply with ONLY the number.
    
#     Available tests:
#     {chr(10).join(f"{i+1}. {t['title']} - {t['description']}" for i, t in enumerate(test_options))}
    
#     Select the number of the most relevant test (1-{len(test_options)}):
#     """
    
#     try:
#         client = openai.OpenAI(api_key=OPENAI_API_KEY)
#         response = client.chat.completions.create(
#             model="gpt-3.5-turbo",
#             messages=[{"role": "user", "content": prompt}],
#             max_tokens=10,
#             temperature=0.1
#         )
        
#         # Extract the number from response
#         response_text = response.choices[0].message.content.strip()
#         selected_index = int(re.search(r'\d+', response_text).group()) - 1
        
#         if 0 <= selected_index < len(test_options):
#             selected_test = test_options[selected_index]
#             logger.info(f"GPT selected: {selected_test['title']}")
#             return selected_test
        
#     except Exception as e:
#         logger.error(f"GPT selection error: {e}")
    
#     # Fallback: Select first test with "Add" button
#     for test in test_options:
#         if test["add_button"]:
#             logger.info(f"Fallback selection: {test['title']}")
#             return test
    
#     return None

# async def handle_job_role_dropdown(page, target_role, fallback_roles, attempt_number=1):
#     """Enhanced job role selection with retry logic and intercept handling"""
    
#     max_attempts = 3
    
#     if attempt_number > max_attempts:
#         logger.error(f"Failed after {max_attempts} attempts")
#         return False, target_role
    
#     try:
#         logger.info(f"Job role selection - Attempt {attempt_number}/{max_attempts}")
        
#         # Wait for page stability
#         await page.wait_for_load_state("networkidle")
#         await asyncio.sleep(2)
        
#         # Strategy 1: Click the intercepting span element directly
#         try:
#             logger.info("Trying to click the span element that's intercepting...")
#             span_element = await page.wait_for_selector("span:has-text('Add the title you are hiring for')", timeout=3000)
#             if span_element:
#                 await span_element.click()
#                 logger.info("Clicked the intercepting span element")
#                 await asyncio.sleep(1)
#         except:
#             logger.info("Span element not found, trying parent div...")
        
#         # Strategy 2: Click the parent div container
#         try:
#             parent_div = await page.wait_for_selector("div.el-select__selected-item", timeout=3000)
#             if parent_div:
#                 await parent_div.click()
#                 logger.info("Clicked the parent div container")
#                 await asyncio.sleep(1)
#         except:
#             pass
        
#         # Strategy 3: Use JavaScript to click through the layers
#         try:
#             await page.evaluate("""
#                 () => {
#                     // Find and click the el-select container
#                     const selectElements = document.querySelectorAll('.el-select, #jobRole');
#                     for (const el of selectElements) {
#                         el.click();
#                         // Also try clicking any child elements
#                         const clickableChild = el.querySelector('.el-select__selected-item, input, span');
#                         if (clickableChild) clickableChild.click();
#                     }
#                 }
#             """)
#             logger.info("Used JavaScript to click through layers")
#             await asyncio.sleep(1)
#         except:
#             pass
        
#         # Now type the job role SLOWLY
#         logger.info(f"Typing job role: {target_role}")
#         await page.keyboard.type(target_role, delay=200)  # Increased delay
        
#         # Wait for dropdown to appear and load
#         dropdown_found = False
#         for wait_attempt in range(5):  # Try 5 times with increasing wait
#             try:
#                 await asyncio.sleep(1 + wait_attempt * 0.5)  # Progressive wait
                
#                 # Check for dropdown
#                 dropdown = await page.query_selector(".el-select-dropdown:visible")
#                 if dropdown:
#                     dropdown_found = True
#                     logger.info(f"Dropdown appeared after {wait_attempt + 1} attempts")
#                     break
                
#                 # Also check for dropdown items directly
#                 items = await page.query_selector_all(".el-select-dropdown__item:visible")
#                 if items:
#                     dropdown_found = True
#                     logger.info(f"Found {len(items)} dropdown items")
#                     break
                    
#             except:
#                 continue
        
#         if dropdown_found:
#             # Extra wait for options to fully load
#             await asyncio.sleep(2)
            
#             # Get all visible dropdown items
#             dropdown_items = await page.query_selector_all(".el-select-dropdown__item:visible")
            
#             if dropdown_items:
#                 logger.info(f"Processing {len(dropdown_items)} dropdown options...")
                
#                 # Process each option
#                 valid_options = []
#                 for idx, item in enumerate(dropdown_items):
#                     try:
#                         text = await item.inner_text()
#                         text = text.strip()
                        
#                         # Skip invalid options
#                         if text and text.lower() not in ['all assessments', 'no data', 'loading...', '']:
#                             valid_options.append((text, item, idx))
#                             logger.info(f"Option {idx}: {text}")
#                     except:
#                         continue
                
#                 if valid_options:
#                     # Find best match
#                     best_match = None
#                     best_score = 0
                    
#                     for text, item, idx in valid_options:
#                         # Exact match
#                         if text.lower() == target_role.lower():
#                             best_match = (text, item)
#                             break
                        
#                         # Similarity score
#                         score = SequenceMatcher(None, text.lower(), target_role.lower()).ratio()
#                         if score > best_score:
#                             best_score = score
#                             best_match = (text, item)
                    
#                     # Select the best option or first valid one
#                     if best_match:
#                         selected_text, selected_item = best_match
#                     else:
#                         selected_text, selected_item, _ = valid_options[0]
                    
#                     # Click with retry
#                     click_success = False
#                     for click_attempt in range(3):
#                         try:
#                             await selected_item.click()
#                             click_success = True
#                             logger.info(f"Successfully clicked: {selected_text}")
#                             break
#                         except:
#                             # Try JavaScript click
#                             try:
#                                 await selected_item.evaluate("el => el.click()")
#                                 click_success = True
#                                 logger.info(f"JS clicked: {selected_text}")
#                                 break
#                             except:
#                                 await asyncio.sleep(0.5)
                    
#                     if click_success:
#                         await asyncio.sleep(2)
                        
#                         # Verify selection worked
#                         dropdown_gone = not await page.query_selector(".el-select-dropdown:visible")
#                         if dropdown_gone:
#                             logger.info("✅ Dropdown closed - selection successful!")
#                             return True, selected_text
#                         else:
#                             logger.warning("Dropdown still visible after selection")
#         else:
#             logger.warning("Dropdown did not appear, trying Enter key...")
#             await page.keyboard.press("Enter")
#             await asyncio.sleep(1)
        
#         # Check if we succeeded by looking at the assessment name field
#         assessment_input = await page.query_selector("input[placeholder*='Assessment name']")
#         if assessment_input:
#             value = await assessment_input.get_attribute("value")
#             if value and len(value) > 0:
#                 logger.info(f"Assessment name has value: {value} - assuming success")
#                 return True, target_role
        
#         # Check if Next button is enabled
#         next_btn = await page.query_selector("button:has-text('Next'):not([disabled])")
#         if next_btn and await next_btn.is_enabled():
#             logger.info("Next button enabled - assuming success")
#             return True, target_role
            
#     except Exception as e:
#         logger.error(f"Error in attempt {attempt_number}: {e}")
    
#     # If we failed, retry
#     logger.warning(f"Attempt {attempt_number} failed, retrying...")
#     await asyncio.sleep(2)
#     return await handle_job_role_dropdown(page, target_role, fallback_roles, attempt_number + 1)

# async def add_tests_with_gpt_selection(page, tests, job_title, job_desc=""):
#     """Enhanced test addition with GPT-based selection"""
#     added_count = 0
    
#     try:
#         # Wait for tests page to load
#         await page.wait_for_load_state("networkidle")
#         await asyncio.sleep(3)
        
#         # Find search input
#         search_input = None
#         search_selectors = [
#             "input[placeholder*='Search']",
#             "input[placeholder*='search']",
#             "input[type='search']",
#             ".search-input",
#             "input[class*='search']"
#         ]
        
#         for selector in search_selectors:
#             try:
#                 element = await page.wait_for_selector(selector, timeout=3000)
#                 if element and await element.is_visible():
#                     search_input = element
#                     logger.info(f"Found search input with selector: {selector}")
#                     break
#             except:
#                 continue
        
#         if search_input:
#             for test_name in tests:
#                 try:
#                     # Clear search and type test name
#                     await search_input.click()
#                     await search_input.fill("")
#                     await asyncio.sleep(0.5)
                    
#                     # Type slowly to trigger search
#                     await search_input.type(test_name, delay=150)
#                     logger.info(f"Searching for: {test_name}")
                    
#                     # Wait for search results to load
#                     results_loaded = False
#                     for wait_attempt in range(5):
#                         await asyncio.sleep(1.5)
                        
#                         test_cards = await page.query_selector_all(".test-card, .assessment-card, [class*='card'], .test-item")
#                         if test_cards:
#                             logger.info(f"Found {len(test_cards)} test cards after {wait_attempt + 1} attempts")
#                             results_loaded = True
#                             break
                        
#                         add_buttons = await page.query_selector_all("button:has-text('Add')")
#                         if add_buttons:
#                             logger.info(f"Found {len(add_buttons)} Add buttons")
#                             results_loaded = True
#                             break
                    
#                     if not results_loaded:
#                         logger.warning(f"No results loaded for: {test_name}")
#                         continue
                    
#                     # Use GPT to select the best test
#                     best_test = await select_best_test_with_gpt(page, test_name, job_title, job_desc)
                    
#                     if best_test and best_test["add_button"]:
#                         # Click the Add button
#                         await best_test["add_button"].click()
#                         added_count += 1
#                         logger.info(f"✅ Added test: {best_test['title']}")
                        
#                         # Wait for UI to update
#                         await asyncio.sleep(2)
                        
#                     else:
#                         logger.warning(f"Could not find suitable test for: {test_name}")
                    
#                     # Wait before next search
#                     await asyncio.sleep(1)
                    
#                 except Exception as e:
#                     logger.error(f"Error adding test '{test_name}': {e}")
                    
#         else:
#             logger.error("❌ Could not find test search input")
#             await page.screenshot(path="no_search_input.png")
            
#     except Exception as e:
#         logger.error(f"Test addition failed: {e}")
    
#     logger.info(f"Total tests added: {added_count}/{len(tests)}")
#     return added_count

# async def extract_invite_link(page):
#     """Extract the candidate invite link from the assessment page"""
#     try:
#         logger.info("Extracting candidate invite link...")
        
#         # Wait for page to load completely
#         await page.wait_for_load_state("networkidle")
#         await asyncio.sleep(3)
        
#         # Try different strategies to find the invite link
#         invite_link = None
        
#         # Strategy 1: Look for copy link button or input
#         try:
#             # Look for copy buttons
#             copy_selectors = [
#                 "button:has-text('Copy')",
#                 "button[class*='copy']",
#                 ".copy-btn",
#                 "button:has-text('Copy Link')"
#             ]
            
#             for selector in copy_selectors:
#                 copy_btn = await page.query_selector(selector)
#                 if copy_btn:
#                     # Click copy button and try to get from clipboard
#                     await copy_btn.click()
#                     await asyncio.sleep(1)
                    
#                     # Try to get clipboard content
#                     try:
#                         clipboard_content = await page.evaluate("() => navigator.clipboard.readText()")
#                         if clipboard_content and "testlify.com" in clipboard_content:
#                             invite_link = clipboard_content
#                             logger.info(f"Got invite link from clipboard: {invite_link}")
#                             break
#                     except:
#                         pass
#         except Exception as e:
#             logger.debug(f"Copy button strategy failed: {e}")
        
#         # Strategy 2: Look for input fields containing the link
#         if not invite_link:
#             try:
#                 input_selectors = [
#                     "input[value*='testlify.com']",
#                     "input[value*='candidate']",
#                     "input[value*='assessment']",
#                     "input[class*='link']"
#                 ]
                
#                 for selector in input_selectors:
#                     input_elem = await page.query_selector(selector)
#                     if input_elem:
#                         value = await input_elem.get_attribute("value")
#                         if value and "testlify.com" in value:
#                             invite_link = value
#                             logger.info(f"Found invite link in input: {invite_link}")
#                             break
#             except Exception as e:
#                 logger.debug(f"Input field strategy failed: {e}")
        
#         # Strategy 3: Look in page text
#         if not invite_link:
#             try:
#                 page_content = await page.content()
#                 import re
#                 link_pattern = r'https://[^\s]*testlify\.com/[^\s]*'
#                 matches = re.findall(link_pattern, page_content)
                
#                 for match in matches:
#                     if "assessment" in match or "candidate" in match:
#                         invite_link = match.strip('"').strip("'")
#                         logger.info(f"Found invite link in page content: {invite_link}")
#                         break
#             except Exception as e:
#                 logger.debug(f"Page content strategy failed: {e}")
        
#         # Strategy 4: Generate fallback link
#         if not invite_link:
#             current_url = page.url
#             # Extract assessment ID from current URL if possible
#             assessment_id_match = re.search(r'/assessments/(\d+)', current_url)
#             if assessment_id_match:
#                 assessment_id = assessment_id_match.group(1)
#                 invite_link = f"https://candidate.testlify.com/assessment/{assessment_id}"
#                 logger.info(f"Generated fallback invite link: {invite_link}")
        
#         return invite_link
        
#     except Exception as e:
#         logger.error(f"Error extracting invite link: {e}")
#         return None

# async def automate_testlify_robust(job_title, job_desc=""):
#     """Main automation function with GPT integration and persistent session"""
    
#     # Get test suggestions from GPT
#     logger.info("Getting test suggestions from GPT...")
#     tests = await get_gpt_test_suggestions(job_title, job_desc)
    
#     # Use the job title as the suggested role
#     suggested_role = job_title.title()
    
#     logger.info(f"Starting automation for: {job_title}")
#     logger.info(f"Suggested role: {suggested_role}")
#     logger.info(f"Tests to add: {tests}")
    
#     # Ensure directories exist
#     os.makedirs(USER_DATA_DIR, exist_ok=True)
#     os.makedirs(OUTPUT_DIR, exist_ok=True)
    
#     async with async_playwright() as playwright:
#         # Browser context with persistent session
#         try:
#             context = await playwright.chromium.launch_persistent_context(
#                 user_data_dir=USER_DATA_DIR,
#                 headless=False,
#                 viewport={'width': 1280, 'height': 900},
#                 args=[
#                     '--disable-blink-features=AutomationControlled',
#                     '--disable-dev-shm-usage',
#                     '--no-sandbox'
#                 ]
#             )
#         except Exception as e:
#             logger.warning(f"Failed to launch persistent context: {e}")
#             logger.info("Falling back to regular browser launch...")
            
#             browser = await playwright.chromium.launch(
#                 headless=False,
#                 args=['--no-sandbox', '--disable-setuid-sandbox']
#             )
#             context = await browser.new_context(
#                 viewport={'width': 1280, 'height': 900}
#             )
        
#         page = context.pages[0] if context.pages else await context.new_page()
        
#         try:
#             # Perform manual login
#             login_success = await manual_login_to_testlify(page)
            
#             if not login_success:
#                 logger.error("Testlify login failed!")
#                 return None
            
#             # Navigate to assessments page
#             await page.goto("https://app.testlify.com/assessments", wait_until="networkidle")
#             await asyncio.sleep(3)
            
#             # Click Create Assessment button
#             create_btn = await page.wait_for_selector("button:has-text('Create assessment')", timeout=30000)
#             await create_btn.click()
#             logger.info("Clicked Create Assessment")
#             await asyncio.sleep(3)
            
#             # Handle job role selection with retry mechanism
#             success, selected_role = await handle_job_role_dropdown(page, suggested_role, [job_title])
            
#             if not success:
#                 print("\n⚠️  Automated job role selection failed.")
#                 print("Please manually:")
#                 print("1. Click on the job role dropdown")
#                 print("2. Type and select your desired role")
#                 print("3. Press ENTER when done")
#                 input("Press ENTER to continue: ")
#                 selected_role = job_title
            
#             # Ensure assessment name is filled
#             await asyncio.sleep(2)
#             assessment_input = await page.query_selector("input[placeholder*='Assessment name']")
#             if assessment_input:
#                 current_value = await assessment_input.get_attribute("value")
#                 if not current_value:
#                     await assessment_input.fill(f"{selected_role} Assessment")
#                     logger.info("Filled assessment name")
            
#             # Click Next to go to tests
#             next_btn = await page.wait_for_selector("button:has-text('Next'):not([disabled])", timeout=15000)
#             await next_btn.click()
#             logger.info("Navigated to Tests page")
#             await asyncio.sleep(3)
            
#             # Add tests with GPT selection
#             added_count = await add_tests_with_gpt_selection(page, tests[:5], job_title, job_desc)
            
#             # Navigate through remaining steps
#             steps = ["Tests → Questions", "Questions → Settings"]
#             for step in steps:
#                 try:
#                     await asyncio.sleep(2)
#                     next_btn = await page.wait_for_selector("button:has-text('Next'):visible", timeout=15000)
#                     if next_btn and await next_btn.is_enabled():
#                         await next_btn.click()
#                         logger.info(f"Completed: {step}")
#                         await asyncio.sleep(2)
#                 except Exception as e:
#                     logger.warning(f"Could not complete {step}: {e}")
            
#             # Save assessment
#             try:
#                 save_btn = await page.wait_for_selector("button:has-text('Save'):visible", timeout=15000)
#                 await save_btn.click()
#                 logger.info("Assessment saved!")
#                 await asyncio.sleep(3)
#             except:
#                 logger.error("Could not find Save button")
            
#             # Extract candidate invite link
#             candidate_link = await extract_invite_link(page)
            
#             # Save results to JSON file
#             assessment_data = {
#                 "job_title": job_title,
#                 "selected_role": selected_role,
#                 "tests_added": added_count,
#                 "total_tests_attempted": len(tests[:5]),
#                 "gpt_suggested_tests": tests,
#                 "candidate_invite_link": candidate_link,
#                 "assessment_url": page.url,
#                 "created_at": datetime.now().isoformat(),
#                 "success": True
#             }
            
#             # Save to JSON file
#             output_filename = f"assessment_{job_title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
#             output_path = Path(OUTPUT_DIR) / output_filename
            
#             with open(output_path, 'w', encoding='utf-8') as f:
#                 json.dump(assessment_data, f, indent=2)
            
#             logger.info(f"Assessment data saved to: {output_path}")
            
#             # Summary
#             print("\n" + "="*50)
#             print("✅ ASSESSMENT CREATION COMPLETED")
#             print("="*50)
#             print(f"Job Role: {selected_role}")
#             print(f"Tests Added: {added_count}")
#             print(f"GPT Suggested: {', '.join(tests[:5])}")
#             if candidate_link:
#                 print(f"Candidate Link: {candidate_link}")
#             else:
#                 print("⚠️  Could not extract candidate link automatically")
#                 print(f"Assessment URL: {page.url}")
#             print(f"Data saved to: {output_path}")
#             print("="*50)
            
#             if added_count > 0:
#                 print("\n🎉 Success! Assessment created with tests.")
#             else:
#                 print("\n⚠️  Assessment created but no tests were added.")
#                 print("You may need to add tests manually.")
            
#             return assessment_data
            
#         except Exception as e:
#             logger.error(f"Critical error: {e}")
#             await page.screenshot(path=f"error_{int(time.time())}.png")
#             print(f"\n❌ Automation failed: {e}")
#             print("Screenshot saved for debugging")
#             return None
            
#         finally:
#             await asyncio.sleep(2)
#             await context.close()

# def create_assessment(job_title, job_desc=""):
#     """Create assessment and return assessment data"""
#     return asyncio.run(automate_testlify_robust(job_title, job_desc))

# def run_recruitment_with_invite_link(job_title, job_desc=""):
#     """Main function that creates assessment and returns invite link"""
    
#     print(f"🚀 Starting recruitment process for: {job_title}")
    
#     # Create the assessment
#     assessment_data = asyncio.run(automate_testlify_robust(job_title, job_desc))
    
#     if assessment_data and assessment_data.get('candidate_invite_link'):
#         invite_link = assessment_data['candidate_invite_link']
#         print(f"\n✅ Assessment created successfully!")
#         print(f"📧 Candidate Invite Link: {invite_link}")
#         return invite_link
#     else:
#         print("\n⚠️  Assessment creation completed but no invite link was extracted.")
#         print("Please check the Testlify dashboard manually for the invite link.")
#         return None

# if __name__ == "__main__":
#     print("🚀 Testlify Assessment Automation with Manual Login & Session Persistence")
#     print("-" * 70)
#     print("Features:")
#     print("✅ Manual login (you login once, session is saved)")
#     print("✅ GPT-powered test suggestions")
#     print("✅ Automatic test selection and addition")
#     print("✅ Session persistence (no need to login repeatedly)")
#     print("-" * 70)
    
#     job_title = input("Enter job title: ").strip()
#     job_desc = input("Enter job description (optional): ").strip()
    
#     invite_link = run_recruitment_with_invite_link(job_title, job_desc)
    
#     if invite_link:
#         print(f"\n🎉 Final Result: {invite_link}")
#     else:
#         print("\n❌ Could not retrieve invite link automatically.")
#         print("💡 Your session is saved - next time you run this, you won't need to login again!")
        
#     print("\n" + "="*50)
#     print("Session saved! Next runs will be faster without login.")
#     print("To clear session: Delete the folder:", USER_DATA_DIR)
#     print("="*50)
import asyncio
import os
import json
import logging
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import time
from difflib import SequenceMatcher
from datetime import datetime
import re
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logging.error("OPENAI_API_KEY not found in environment variables")
    raise ValueError("OPENAI_API_KEY not found in environment variables")

# Configuration
TESTLIFY_EMAIL = "jlau@knlrealty.com"
USER_DATA_DIR = r"D:\interview link\testlify_browser_profile"
OUTPUT_DIR = "assessment_links"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('testlify_automation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def handle_popups_and_notifications(page):
    """Handle any popups, alerts, or notifications that appear"""
    try:
        # Common popup selectors that need to be handled
        popup_selectors = [
            # "I understand" buttons
            "button:has-text('I understand')",
            "button:has-text('I Understand')",
            "button[class*='understand']",
            
            # "OK" buttons
            "button:has-text('OK')",
            "button:has-text('Ok')",
            
            # "Got it" buttons
            "button:has-text('Got it')",
            "button:has-text('Got It')",
            
            # "Continue" buttons
            "button:has-text('Continue')",
            
            # "Close" buttons for tips/notifications
            "button:has-text('Close')",
            ".close-btn",
            ".notification-close",
            
            # Generic confirmation buttons
            ".btn-primary:has-text('Yes')",
            ".btn-success",
            
            # Modal close buttons
            ".modal-footer button",
            ".dialog-footer button",
        ]
        
        # Check for and handle popups
        for selector in popup_selectors:
            try:
                # Wait briefly for popup to appear
                popup_btn = await page.wait_for_selector(selector, timeout=2000)
                if popup_btn and await popup_btn.is_visible():
                    await popup_btn.click()
                    logger.info(f"✅ Handled popup with selector: {selector}")
                    await asyncio.sleep(1)  # Wait for popup to close
                    return True
            except:
                continue
        
        # Check for overlay/backdrop clicks needed
        try:
            overlay = await page.query_selector(".modal-backdrop, .overlay, .popup-overlay")
            if overlay:
                # Try clicking outside the modal
                await page.keyboard.press("Escape")
                logger.info("Pressed Escape to close modal")
                await asyncio.sleep(1)
        except:
            pass
            
        return False
        
    except Exception as e:
        logger.debug(f"Error handling popups: {e}")
        return False

async def manual_login_to_testlify(page):
    """Manual login helper: prompts the user to complete Testlify login"""
    logger.info("🔑 Starting manual Testlify login flow...")

    try:
        # Check if already logged in by trying to go to assessments
        await page.goto("https://app.testlify.com/assessments", wait_until="networkidle")
        await asyncio.sleep(2)
        
        # Check if we're already logged in
        current_url = page.url
        if "assessments" in current_url or "dashboard" in current_url:
            logger.info("✅ Already logged in to Testlify")
            return True
        
        # If not logged in, go to login page
        logger.info("Not logged in, redirecting to login page...")
        await page.goto("https://app.testlify.com/login", wait_until="networkidle")
        await asyncio.sleep(2)
        
        # Prompt user to login manually
        print("\n⚠️  Please complete the Testlify login (including 2FA if required) in the browser window.")
        print("Once you're on the Testlify dashboard/assessments page, press ENTER to continue...")
        input("Press ENTER after successful login: ")

        # Wait for page to settle post-login
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)
        
        # Verify we're logged in
        current_url = page.url
        if "assessments" in current_url or "dashboard" in current_url:
            logger.info("✅ Manual login confirmed; session will be saved for future use.")
            return True
        else:
            # Try to navigate to assessments to verify
            await page.goto("https://app.testlify.com/assessments", wait_until="networkidle")
            await asyncio.sleep(2)
            
            current_url = page.url
            if "assessments" in current_url or "dashboard" in current_url:
                logger.info("✅ Login successful - now on assessments page")
                return True
            else:
                logger.error("❌ Login verification failed")
                return False
        
    except Exception as e:
        logger.error(f"Error during manual login: {e}")
        return False

async def get_programming_test_suggestions(job_title, job_desc=""):
    """Get 3 core programming test suggestions with diversity and depth"""

    prompt = f"""
    Job Title: {job_title}
    Job Description: {job_desc if job_desc else "Not provided"}

    Suggest exactly 3 programming test categories that cover DIVERSITY and DEPTH for this role.
    
    The 3 tests should cover:
    1. Core Programming Language (Python, Java, JavaScript, etc.)
    2. Advanced Technical Concept (Algorithms, Data Structures, System Design, etc.)
    3. Specialized Domain Skill (AI/ML, Web Development, Database, etc.)

    Requirements:
    - Each suggestion should be 1-2 words maximum
    - Focus on programming/technical skills only
    - Ensure diversity across different technical areas
    - Pick the most relevant for the specific job role

    Return ONLY 3 search terms, one per line.

    Example for "AI Engineer":
    Python
    Algorithms
    Machine Learning

    Example for "Full Stack Developer":
    JavaScript
    System Design
    Database
    """

    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.1
        )

        suggestions = response.choices[0].message.content.strip().split('\n')
        suggestions = [s.strip() for s in suggestions if s.strip() and len(s.strip().split()) <= 2]
        
        # Ensure we have exactly 3 suggestions
        if len(suggestions) >= 3:
            final_suggestions = suggestions[:3]
        else:
            # Add fallbacks if needed
            fallbacks = ["Programming", "Algorithms", "Problem Solving"]
            final_suggestions = suggestions + fallbacks[:3-len(suggestions)]
        
        logger.info(f"GPT suggested 3 core tests: {final_suggestions}")
        return final_suggestions

    except Exception as e:
        logger.error(f"GPT API error: {e}")
        # Fallback based on job title
        if "ai" in job_title.lower() or "ml" in job_title.lower():
            return ["Python", "Machine Learning", "Algorithms"]
        elif "web" in job_title.lower() or "frontend" in job_title.lower():
            return ["JavaScript", "React", "CSS"]
        elif "backend" in job_title.lower():
            return ["Python", "Database", "API"]
        elif "data" in job_title.lower():
            return ["Python", "SQL", "Statistics"]
        else:
            return ["Programming", "Algorithms", "Problem Solving"]

async def select_best_programming_test(page, search_term, job_title):
    """Enhanced test selection focusing on programming tests with better filtering"""
    
    # Get all visible test cards
    test_cards = await page.query_selector_all(".test-card, div[class*='card'], .test-item")
    
    if not test_cards:
        logger.warning(f"No test cards found for: {search_term}")
        return None
    
    # Extract test information
    test_options = []
    for idx, card in enumerate(test_cards[:8]):  # Limit to first 8 results
        try:
            # Extract test title
            title_elem = await card.query_selector("h3, .test-title, [class*='title'], h4, h5")
            if not title_elem:
                continue
                
            test_title = await title_elem.inner_text()
            
            # Extract test description if available
            desc_elem = await card.query_selector("p, .test-description, .description, .test-desc")
            test_desc = await desc_elem.inner_text() if desc_elem else ""
            
            # Find Add button
            add_button = await card.query_selector("button:has-text('Add'), button[class*='add'], .add-btn")
            
            # Filter for programming-related tests
            combined_text = f"{test_title} {test_desc}".lower()
            programming_keywords = [
                "programming", "coding", "algorithm", "data structure", "software",
                "python", "java", "javascript", "react", "node", "sql", "database",
                "machine learning", "ai", "artificial intelligence", "web development",
                "backend", "frontend", "api", "system design", "computer science"
            ]
            
            is_programming_test = any(keyword in combined_text for keyword in programming_keywords)
            
            if is_programming_test and add_button:
                test_options.append({
                    "index": idx,
                    "title": test_title.strip(),
                    "description": test_desc.strip()[:150],
                    "card": card,
                    "add_button": add_button,
                    "relevance_score": 0
                })
            
        except Exception as e:
            logger.debug(f"Error processing card {idx}: {e}")
            continue
    
    if not test_options:
        logger.warning("No programming test options found")
        return None
    
    # Enhanced scoring for programming tests
    for test in test_options:
        title_lower = test['title'].lower()
        desc_lower = test['description'].lower()
        
        # Score based on search term relevance
        if search_term.lower() in title_lower:
            test['relevance_score'] += 10
        if search_term.lower() in desc_lower:
            test['relevance_score'] += 5
        
        # Bonus for advanced/comprehensive tests
        advanced_keywords = ["advanced", "comprehensive", "expert", "senior", "professional"]
        if any(keyword in title_lower for keyword in advanced_keywords):
            test['relevance_score'] += 3
        
        # Bonus for specific technical depth
        depth_keywords = ["algorithm", "data structure", "system design", "architecture"]
        if any(keyword in title_lower or keyword in desc_lower for keyword in depth_keywords):
            test['relevance_score'] += 2
    
    # Sort by relevance score and select best
    test_options.sort(key=lambda x: x['relevance_score'], reverse=True)
    best_test = test_options[0]
    
    logger.info(f"Selected best programming test: {best_test['title']} (score: {best_test['relevance_score']})")
    return best_test

async def handle_job_role_dropdown(page, target_role, fallback_roles, attempt_number=1):
    """Enhanced job role selection with popup handling"""
    
    max_attempts = 3
    
    if attempt_number > max_attempts:
        logger.error(f"Failed after {max_attempts} attempts")
        return False, target_role
    
    try:
        logger.info(f"Job role selection - Attempt {attempt_number}/{max_attempts}")
        
        # Handle any popups first
        await handle_popups_and_notifications(page)
        
        # Wait for page stability
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)
        
        # Strategy 1: Click the intercepting span element directly
        try:
            logger.info("Trying to click the span element that's intercepting...")
            span_element = await page.wait_for_selector("span:has-text('Add the title you are hiring for')", timeout=3000)
            if span_element:
                await span_element.click()
                logger.info("Clicked the intercepting span element")
                await asyncio.sleep(1)
        except:
            logger.info("Span element not found, trying parent div...")
        
        # Strategy 2: Click the parent div container
        try:
            parent_div = await page.wait_for_selector("div.el-select__selected-item", timeout=3000)
            if parent_div:
                await parent_div.click()
                logger.info("Clicked the parent div container")
                await asyncio.sleep(1)
        except:
            pass
        
        # Strategy 3: Use JavaScript to click through the layers
        try:
            await page.evaluate("""
                () => {
                    // Find and click the el-select container
                    const selectElements = document.querySelectorAll('.el-select, #jobRole');
                    for (const el of selectElements) {
                        el.click();
                        // Also try clicking any child elements
                        const clickableChild = el.querySelector('.el-select__selected-item, input, span');
                        if (clickableChild) clickableChild.click();
                    }
                }
            """)
            logger.info("Used JavaScript to click through layers")
            await asyncio.sleep(1)
        except:
            pass
        
        # Handle any popups that appeared after clicking
        await handle_popups_and_notifications(page)
        
        # Now type the job role SLOWLY
        logger.info(f"Typing job role: {target_role}")
        await page.keyboard.type(target_role, delay=200)
        
        # Wait for dropdown to appear and load
        dropdown_found = False
        for wait_attempt in range(5):
            try:
                await asyncio.sleep(1 + wait_attempt * 0.5)
                
                # Handle popups during wait
                await handle_popups_and_notifications(page)
                
                # Check for dropdown
                dropdown = await page.query_selector(".el-select-dropdown:visible")
                if dropdown:
                    dropdown_found = True
                    logger.info(f"Dropdown appeared after {wait_attempt + 1} attempts")
                    break
                
                # Also check for dropdown items directly
                items = await page.query_selector_all(".el-select-dropdown__item:visible")
                if items:
                    dropdown_found = True
                    logger.info(f"Found {len(items)} dropdown items")
                    break
                    
            except:
                continue
        
        if dropdown_found:
            # Extra wait for options to fully load
            await asyncio.sleep(2)
            
            # Get all visible dropdown items
            dropdown_items = await page.query_selector_all(".el-select-dropdown__item:visible")
            
            if dropdown_items:
                logger.info(f"Processing {len(dropdown_items)} dropdown options...")
                
                # Process each option
                valid_options = []
                for idx, item in enumerate(dropdown_items):
                    try:
                        text = await item.inner_text()
                        text = text.strip()
                        
                        # Skip invalid options
                        if text and text.lower() not in ['all assessments', 'no data', 'loading...', '']:
                            valid_options.append((text, item, idx))
                            logger.info(f"Option {idx}: {text}")
                    except:
                        continue
                
                if valid_options:
                    # Find best match
                    best_match = None
                    best_score = 0
                    
                    for text, item, idx in valid_options:
                        # Exact match
                        if text.lower() == target_role.lower():
                            best_match = (text, item)
                            break
                        
                        # Similarity score
                        score = SequenceMatcher(None, text.lower(), target_role.lower()).ratio()
                        if score > best_score:
                            best_score = score
                            best_match = (text, item)
                    
                    # Select the best option or first valid one
                    if best_match:
                        selected_text, selected_item = best_match
                    else:
                        selected_text, selected_item, _ = valid_options[0]
                    
                    # Click with retry
                    click_success = False
                    for click_attempt in range(3):
                        try:
                            await selected_item.click()
                            click_success = True
                            logger.info(f"Successfully clicked: {selected_text}")
                            break
                        except:
                            # Try JavaScript click
                            try:
                                await selected_item.evaluate("el => el.click()")
                                click_success = True
                                logger.info(f"JS clicked: {selected_text}")
                                break
                            except:
                                await asyncio.sleep(0.5)
                    
                    if click_success:
                        await asyncio.sleep(2)
                        
                        # Handle any popups after selection
                        await handle_popups_and_notifications(page)
                        
                        # Verify selection worked
                        dropdown_gone = not await page.query_selector(".el-select-dropdown:visible")
                        if dropdown_gone:
                            logger.info("✅ Dropdown closed - selection successful!")
                            return True, selected_text
                        else:
                            logger.warning("Dropdown still visible after selection")
        else:
            logger.warning("Dropdown did not appear, trying Enter key...")
            await page.keyboard.press("Enter")
            await asyncio.sleep(1)
        
        # Handle popups before final verification
        await handle_popups_and_notifications(page)
        
        # Check if we succeeded by looking at the assessment name field
        assessment_input = await page.query_selector("input[placeholder*='Assessment name']")
        if assessment_input:
            value = await assessment_input.get_attribute("value")
            if value and len(value) > 0:
                logger.info(f"Assessment name has value: {value} - assuming success")
                return True, target_role
        
        # Check if Next button is enabled
        next_btn = await page.query_selector("button:has-text('Next'):not([disabled])")
        if next_btn and await next_btn.is_enabled():
            logger.info("Next button enabled - assuming success")
            return True, target_role
            
    except Exception as e:
        logger.error(f"Error in attempt {attempt_number}: {e}")
    
    # If we failed, retry
    logger.warning(f"Attempt {attempt_number} failed, retrying...")
    await asyncio.sleep(2)
    return await handle_job_role_dropdown(page, target_role, fallback_roles, attempt_number + 1)

async def add_programming_tests_with_diversity(page, tests, job_title, job_desc=""):
    """Enhanced test addition with diversity focus and popup handling"""
    added_count = 0
    added_tests = []
    
    try:
        # Wait for tests page to load
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(3)
        
        # Handle any initial popups
        await handle_popups_and_notifications(page)
        
        # Find search input
        search_input = None
        search_selectors = [
            "input[placeholder*='Search']",
            "input[placeholder*='search']", 
            "input[type='search']",
            ".search-input",
            "input[class*='search']"
        ]
        
        for selector in search_selectors:
            try:
                element = await page.wait_for_selector(selector, timeout=3000)
                if element and await element.is_visible():
                    search_input = element
                    logger.info(f"Found search input with selector: {selector}")
                    break
            except:
                continue
        
        if search_input:
            for i, test_name in enumerate(tests):
                try:
                    logger.info(f"Adding test {i+1}/3: {test_name}")
                    
                    # Handle popups before searching
                    await handle_popups_and_notifications(page)
                    
                    # Clear search and type test name
                    await search_input.click()
                    await search_input.fill("")
                    await asyncio.sleep(0.5)
                    
                    # Type slowly to trigger search
                    await search_input.type(test_name, delay=150)
                    logger.info(f"Searching for: {test_name}")
                    
                    # Wait for search results to load
                    results_loaded = False
                    for wait_attempt in range(6):  # Increased attempts
                        await asyncio.sleep(1.5)
                        
                        # Handle popups during wait
                        popup_handled = await handle_popups_and_notifications(page)
                        if popup_handled:
                            await asyncio.sleep(1)  # Extra wait after popup handling
                        
                        test_cards = await page.query_selector_all(".test-card, .assessment-card, [class*='card'], .test-item")
                        if test_cards:
                            logger.info(f"Found {len(test_cards)} test cards after {wait_attempt + 1} attempts")
                            results_loaded = True
                            break
                        
                        add_buttons = await page.query_selector_all("button:has-text('Add')")
                        if add_buttons:
                            logger.info(f"Found {len(add_buttons)} Add buttons")
                            results_loaded = True
                            break
                    
                    if not results_loaded:
                        logger.warning(f"No results loaded for: {test_name}")
                        continue
                    
                    # Select the best programming test
                    best_test = await select_best_programming_test(page, test_name, job_title)
                    
                    if best_test and best_test["add_button"]:
                        # Handle popups before clicking Add
                        await handle_popups_and_notifications(page)
                        
                        # Click the Add button
                        try:
                            await best_test["add_button"].click()
                            logger.info(f"Clicked Add button for: {best_test['title']}")
                        except:
                            # Try JavaScript click if regular click fails
                            await best_test["add_button"].evaluate("el => el.click()")
                            logger.info(f"JS clicked Add button for: {best_test['title']}")
                        
                        added_count += 1
                        added_tests.append(best_test['title'])
                        logger.info(f"✅ Added test {added_count}/3: {best_test['title']}")
                        
                        # Wait for UI to update and handle any popups
                        await asyncio.sleep(2)
                        await handle_popups_and_notifications(page)
                        
                        # Additional wait if we just added the first test (more popups likely)
                        if added_count == 1:
                            await asyncio.sleep(3)
                            await handle_popups_and_notifications(page)
                        
                    else:
                        logger.warning(f"Could not find suitable programming test for: {test_name}")
                    
                    # Wait before next search
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error adding test '{test_name}': {e}")
                    # Handle popups even on error
                    await handle_popups_and_notifications(page)
                    
        else:
            logger.error("❌ Could not find test search input")
            await page.screenshot(path="no_search_input.png")
            
    except Exception as e:
        logger.error(f"Test addition failed: {e}")
        # Handle popups on critical error
        await handle_popups_and_notifications(page)
    
    logger.info(f"Total programming tests added: {added_count}/3")
    logger.info(f"Added tests: {added_tests}")
    return added_count, added_tests

async def extract_invite_link(page):
    """Extract the candidate invite link from the assessment page"""
    try:
        logger.info("Extracting candidate invite link...")
        
        # Handle any popups first
        await handle_popups_and_notifications(page)
        
        # Wait for page to load completely
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(3)
        
        # Try different strategies to find the invite link
        invite_link = None
        
        # Strategy 1: Look for copy link button or input
        try:
            # Look for copy buttons
            copy_selectors = [
                "button:has-text('Copy')",
                "button[class*='copy']",
                ".copy-btn",
                "button:has-text('Copy Link')"
            ]
            
            for selector in copy_selectors:
                copy_btn = await page.query_selector(selector)
                if copy_btn:
                    # Click copy button and try to get from clipboard
                    await copy_btn.click()
                    await asyncio.sleep(1)
                    
                    # Try to get clipboard content
                    try:
                        clipboard_content = await page.evaluate("() => navigator.clipboard.readText()")
                        if clipboard_content and "testlify.com" in clipboard_content:
                            invite_link = clipboard_content
                            logger.info(f"Got invite link from clipboard: {invite_link}")
                            break
                    except:
                        pass
        except Exception as e:
            logger.debug(f"Copy button strategy failed: {e}")
        
        # Strategy 2: Look for input fields containing the link
        if not invite_link:
            try:
                input_selectors = [
                    "input[value*='testlify.com']",
                    "input[value*='candidate']",
                    "input[value*='assessment']",
                    "input[class*='link']"
                ]
                
                for selector in input_selectors:
                    input_elem = await page.query_selector(selector)
                    if input_elem:
                        value = await input_elem.get_attribute("value")
                        if value and "testlify.com" in value:
                            invite_link = value
                            logger.info(f"Found invite link in input: {invite_link}")
                            break
            except Exception as e:
                logger.debug(f"Input field strategy failed: {e}")
        
        # Strategy 3: Look in page text
        if not invite_link:
            try:
                page_content = await page.content()
                import re
                link_pattern = r'https://[^\s]*testlify\.com/[^\s]*'
                matches = re.findall(link_pattern, page_content)
                
                for match in matches:
                    if "assessment" in match or "candidate" in match:
                        invite_link = match.strip('"').strip("'")
                        logger.info(f"Found invite link in page content: {invite_link}")
                        break
            except Exception as e:
                logger.debug(f"Page content strategy failed: {e}")
        
        # Strategy 4: Generate fallback link
        if not invite_link:
            current_url = page.url
            # Extract assessment ID from current URL if possible
            assessment_id_match = re.search(r'/assessments/(\d+)', current_url)
            if assessment_id_match:
                assessment_id = assessment_id_match.group(1)
                invite_link = f"https://candidate.testlify.com/assessment/{assessment_id}"
                logger.info(f"Generated fallback invite link: {invite_link}")
        
        return invite_link
        
    except Exception as e:
        logger.error(f"Error extracting invite link: {e}")
        return None

async def automate_testlify_with_programming_focus(job_title, job_desc=""):
    """Main automation function with programming test focus and popup handling"""
    
    # Get 3 core programming test suggestions from GPT
    logger.info("Getting 3 core programming test suggestions from GPT...")
    tests = await get_programming_test_suggestions(job_title, job_desc)
    
    # Use the job title as the suggested role
    suggested_role = job_title.title()
    
    logger.info(f"Starting automation for: {job_title}")
    logger.info(f"Suggested role: {suggested_role}")
    logger.info(f"3 Core tests to add: {tests}")
    
    # Ensure directories exist
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    async with async_playwright() as playwright:
        # Browser context with persistent session
        try:
            context = await playwright.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                headless=False,
                viewport={'width': 1280, 'height': 900},
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox'
                ]
            )
        except Exception as e:
            logger.warning(f"Failed to launch persistent context: {e}")
            logger.info("Falling back to regular browser launch...")
            
            browser = await playwright.chromium.launch(
                headless=False,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 900}
            )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        try:
            # Perform manual login
            login_success = await manual_login_to_testlify(page)
            
            if not login_success:
                logger.error("Testlify login failed!")
                return None
            
            # Navigate to assessments page
            await page.goto("https://app.testlify.com/assessments", wait_until="networkidle")
            await asyncio.sleep(3)
            
            # Handle any initial popups
            await handle_popups_and_notifications(page)
            
            # Click Create Assessment button
            create_btn = await page.wait_for_selector("button:has-text('Create assessment')", timeout=3000)
            await create_btn.click()
            logger.info("Clicked Create Assessment")
            await asyncio.sleep(3)
            
            # Handle popups after clicking create
            await handle_popups_and_notifications(page)
            
            # Handle job role selection with retry mechanism
            success, selected_role = await handle_job_role_dropdown(page, suggested_role, [job_title])
            
            if not success:
                print("\n⚠️  Automated job role selection failed.")
                print("Please manually:")
                print("1. Click on the job role dropdown")
                print("2. Type and select your desired role")
                print("3. Press ENTER when done")
                input("Press ENTER to continue: ")
                selected_role = job_title
            
            # Handle popups after role selection
            await handle_popups_and_notifications(page)
            
            # Ensure assessment name is filled
            await asyncio.sleep(2)
            assessment_input = await page.query_selector("input[placeholder*='Assessment name']")
            if assessment_input:
                current_value = await assessment_input.get_attribute("value")
                if not current_value:
                    await assessment_input.fill(f"{selected_role} Programming Assessment")
                    logger.info("Filled assessment name")
            
            # Click Next to go to tests
            next_btn = await page.wait_for_selector("button:has-text('Next'):not([disabled])", timeout=10_000)
            await next_btn.click()
            logger.info("Navigated to Tests page")
            await asyncio.sleep(3)
            
            # Handle popups on tests page
            await handle_popups_and_notifications(page)
            
            # Add 3 core programming tests with diversity
            added_count, added_tests = await add_programming_tests_with_diversity(page, tests, job_title, job_desc)
            
            # Handle popups after adding tests
            await handle_popups_and_notifications(page)
            
            # Navigate through remaining steps
            steps = ["Tests → Questions", "Questions → Settings"]
            for step in steps:
                try:
                    await asyncio.sleep(2)
                    
                    # Handle popups before navigation
                    await handle_popups_and_notifications(page)
                    
                    next_btn = await page.wait_for_selector("button:has-text('Next'):visible", timeout=15_000)
                    if next_btn and await next_btn.is_enabled():
                        await next_btn.click()
                        logger.info(f"Completed: {step}")
                        await asyncio.sleep(2)
                        
                        # Handle popups after navigation
                        await handle_popups_and_notifications(page)
                        
                except Exception as e:
                    logger.warning(f"Could not complete {step}: {e}")
                    # Try to handle popups even on error
                    await handle_popups_and_notifications(page)
            
            # Handle popups before saving
            await handle_popups_and_notifications(page)
            
            # Save assessment
            try:
                save_btn = await page.wait_for_selector("button:has-text('Save'):visible", timeout=15_000)
                await save_btn.click()
                logger.info("Assessment saved!")
                await asyncio.sleep(3)
                
                # Handle popups after saving
                await handle_popups_and_notifications(page)
                
            except:
                logger.error("Could not find Save button")
            
            # Extract candidate invite link
            candidate_link = await extract_invite_link(page)
            
            # Save results to JSON file
            assessment_data = {
                "job_title": job_title,
                "selected_role": selected_role,
                "programming_tests_added": added_count,
                "total_tests_attempted": 3,
                "gpt_suggested_tests": tests,
                "actual_added_tests": added_tests,
                "candidate_invite_link": candidate_link,
                "assessment_url": page.url,
                "created_at": datetime.now().isoformat(),
                "success": added_count > 0,
                "diversity_achieved": len(set(added_tests)) == len(added_tests),  # Check if all tests are unique
                "assessment_type": "Programming Assessment with Diversity Focus"
            }
            
            # Save to JSON file
            output_filename = f"programming_assessment_{job_title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            output_path = Path(OUTPUT_DIR) / output_filename
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(assessment_data, f, indent=2)
            
            logger.info(f"Assessment data saved to: {output_path}")
            
            # Summary
            print("\n" + "="*60)
            print("✅ PROGRAMMING ASSESSMENT CREATION COMPLETED")
            print("="*60)
            print(f"Job Role: {selected_role}")
            print(f"Programming Tests Added: {added_count}/3")
            print(f"GPT Suggested: {', '.join(tests)}")
            print(f"Actually Added: {', '.join(added_tests)}")
            print(f"Diversity Achieved: {'Yes' if len(set(added_tests)) == len(added_tests) else 'No'}")
            
            if candidate_link:
                print(f"Candidate Link: {candidate_link}")
            else:
                print("⚠️  Could not extract candidate link automatically")
                print(f"Assessment URL: {page.url}")
            print(f"Data saved to: {output_path}")
            print("="*60)
            
            if added_count >= 2:
                print("\n🎉 Excellent! Assessment created with diverse programming tests.")
            elif added_count == 1:
                print("\n⚠️  Assessment created but only 1 test was added.")
                print("You may need to add more tests manually for better diversity.")
            else:
                print("\n⚠️  Assessment created but no tests were added.")
                print("Please add programming tests manually.")
            
            print("\n💡 Programming Assessment Features:")
            print("✅ Core programming language test")
            print("✅ Advanced technical concepts")
            print("✅ Specialized domain skills")
            print("✅ Popup handling during automation")
            
            return assessment_data
            
        except Exception as e:
            logger.error(f"Critical error: {e}")
            await page.screenshot(path=f"error_{int(time.time())}.png")
            print(f"\n❌ Automation failed: {e}")
            print("Screenshot saved for debugging")
            
            # Try to handle popups even on critical error
            try:
                await handle_popups_and_notifications(page)
            except:
                pass
            
            return None
            
        finally:
            await asyncio.sleep(2)
            await context.close()

def create_programming_assessment(job_title, job_desc=""):
    """Create programming assessment with diversity focus and return assessment data"""
    return asyncio.run(automate_testlify_with_programming_focus(job_title, job_desc))

def run_programming_recruitment_with_invite_link(job_title, job_desc=""):
    """Main function that creates programming assessment and returns invite link"""
    
    print(f"🚀 Starting programming recruitment process for: {job_title}")
    print("📊 Focus: 3 Core Programming Tests with Diversity & Depth")
    
    # Create the programming assessment
    assessment_data = asyncio.run(automate_testlify_with_programming_focus(job_title, job_desc))
    
    if assessment_data and assessment_data.get('candidate_invite_link'):
        invite_link = assessment_data['candidate_invite_link']
        print(f"\n✅ Programming assessment created successfully!")
        print(f"📧 Candidate Invite Link: {invite_link}")
        return invite_link
    else:
        print("\n⚠️  Assessment creation completed but no invite link was extracted.")
        print("Please check the Testlify dashboard manually for the invite link.")
        return None

if __name__ == "__main__":
    print("🚀 Enhanced Testlify Programming Assessment Automation")
    print("-" * 80)
    print("Features:")
    print("✅ Manual login with session persistence")
    print("✅ GPT-powered programming test suggestions (3 core tests)")
    print("✅ Diversity focus: Core Language + Advanced Concepts + Domain Skills")
    print("✅ Automatic popup/notification handling")
    print("✅ Enhanced test selection for programming roles")
    print("✅ Comprehensive error handling and retries")
    print("-" * 80)
    
    job_title = input("Enter job title: ").strip()
    job_desc = input("Enter job description (optional): ").strip()
    
    print(f"\n📋 Creating programming assessment for: {job_title}")
    print("🎯 Target: 3 diverse programming tests")
    
    invite_link = run_programming_recruitment_with_invite_link(job_title, job_desc)
    
    if invite_link:
        print(f"\n🎉 Final Result: {invite_link}")
        print("\n📊 Assessment Summary:")
        print("• Core programming language skills tested")
        print("• Advanced technical concepts covered") 
        print("• Specialized domain expertise evaluated")
    else:
        print("\n❌ Could not retrieve invite link automatically.")
        print("💡 Your session is saved - next time you run this, you won't need to login again!")
        
    print("\n" + "="*60)
    print("Session saved! Next runs will be faster without login.")
    print("To clear session: Delete the folder:", USER_DATA_DIR)
    print("="*60)