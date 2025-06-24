# testlify_results_scraper.py - QUICK FIX VERSION
# Replace your existing testlify_results_scraper.py with this

import asyncio
import json
import logging
from pathlib import Path
from playwright.async_api import async_playwright
import re
from datetime import datetime, timedelta
import time
import os
from typing import Dict, List, Optional
from db import Candidate, SessionLocal
from email_util import send_interview_link_email, send_rejection_email
from sqlalchemy import and_

USER_DATA_DIR = r"D:\interview link\testlify_browser_profile"
OUTPUT_DIR = "assessment_results"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class TestlifyResultsScraperFixed:
    """Quick fix version with aggressive score extraction"""
    
    def __init__(self):
        self.session = SessionLocal()
        Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    async def scrape_assessment_results(self, assessment_name: str) -> List[Dict]:
        """Fixed scraping with aggressive extraction"""
        async with async_playwright() as playwright:
            context = await playwright.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                headless=False,
                viewport={'width': 1400, 'height': 1000}
            )
            page = context.pages[0] if context.pages else await context.new_page()
            
            try:
                logging.info("🔍 Starting fixed Testlify scraping...")
                
                # Navigate to assessments
                await page.goto("https://app.testlify.com/assessments", wait_until="networkidle")
                await asyncio.sleep(3)
                
                # Check login
                if await page.query_selector("input[type='email']"):
                    print("🔐 Please log in manually...")
                    input("Press ENTER after logging in: ")
                    await page.wait_for_load_state("networkidle")
                
                # Find assessment
                assessment_found = await self._find_and_click_assessment(page, assessment_name)
                if not assessment_found:
                    logging.error(f"Assessment '{assessment_name}' not found")
                    return []
                
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(5)  # Give it more time to load
                
                # Extract scores aggressively
                results = await self._extract_scores_aggressively(page)
                
                # Save and process
                self._save_results(assessment_name, results)
                await self._process_results(results)
                
                return results
                
            except Exception as e:
                logging.error(f"Scraping error: {e}")
                await page.screenshot(path="scraping_error.png")
                return []
            finally:
                await context.close()
    
    async def _find_and_click_assessment(self, page, assessment_name: str) -> bool:
        """Find and click assessment - simplified"""
        try:
            logging.info(f"Looking for assessment: {assessment_name}")
            
            # Method 1: Exact text
            try:
                element = await page.wait_for_selector(f"text={assessment_name}", timeout=10000)
                await element.click()
                logging.info("✅ Found via exact text")
                return True
            except:
                pass
            
            # Method 2: Contains text (case insensitive)
            try:
                all_elements = await page.query_selector_all("a, button, div, span")
                for element in all_elements:
                    try:
                        text = await element.inner_text()
                        if text and assessment_name.lower() in text.lower() and len(text.strip()) < 100:
                            await element.click()
                            logging.info("✅ Found via contains text")
                            return True
                    except:
                        continue
            except:
                pass
            
            return False
            
        except Exception as e:
            logging.error(f"Error finding assessment: {e}")
            return False
    
    async def _extract_scores_aggressively(self, page) -> List[Dict]:
        """Aggressive score extraction using multiple methods"""
        logging.info("🎯 Starting aggressive score extraction...")
        
        candidates = []
        
        # Method 1: Pure JavaScript extraction
        js_candidates = await self._javascript_extraction(page)
        candidates.extend(js_candidates)
        logging.info(f"JavaScript method found: {len(js_candidates)} candidates")
        
        # Method 2: Full page text analysis
        if not candidates:
            text_candidates = await self._text_analysis_extraction(page)
            candidates.extend(text_candidates)
            logging.info(f"Text analysis found: {len(text_candidates)} candidates")
        
        # Method 3: Element-by-element search
        if not candidates:
            element_candidates = await self._element_search_extraction(page)
            candidates.extend(element_candidates)
            logging.info(f"Element search found: {len(element_candidates)} candidates")
        
        # Remove duplicates
        unique_candidates = []
        seen_emails = set()
        for candidate in candidates:
            email = candidate.get('email')
            if email and email not in seen_emails:
                seen_emails.add(email)
                unique_candidates.append(candidate)
        
        logging.info(f"🎯 Total unique candidates with scores: {len(unique_candidates)}")
        return unique_candidates
    
    async def _javascript_extraction(self, page) -> List[Dict]:
        """Use JavaScript to find all score patterns"""
        try:
            result = await page.evaluate("""
                () => {
                    const candidates = [];
                    const emailRegex = /\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b/g;
                    const percentRegex = /(\\d+(?:\\.\\d+)?)%/g;
                    const scoreRegex = /(\\d+)\\s*\\/\\s*(\\d+)/g;
                    
                    // Get entire page text
                    const pageText = document.body.innerText || document.body.textContent || '';
                    
                    // Find all emails
                    const emails = [...pageText.matchAll(emailRegex)].map(m => m[0]);
                    
                    // For each email, try to find nearby scores
                    for (let email of emails) {
                        const emailIndex = pageText.indexOf(email);
                        if (emailIndex === -1) continue;
                        
                        // Look 500 characters before and after the email
                        const start = Math.max(0, emailIndex - 500);
                        const end = Math.min(pageText.length, emailIndex + 500);
                        const context = pageText.substring(start, end);
                        
                        // Find percentages in context
                        const percentMatches = [...context.matchAll(percentRegex)];
                        const scoreMatches = [...context.matchAll(scoreRegex)];
                        
                        if (percentMatches.length > 0 || scoreMatches.length > 0) {
                            const candidate = {
                                email: email,
                                percentage: null,
                                score: null,
                                total_questions: null,
                                context: context.trim(),
                                method: 'javascript'
                            };
                            
                            // Get the closest percentage
                            if (percentMatches.length > 0) {
                                candidate.percentage = parseFloat(percentMatches[0][1]);
                            }
                            
                            // Get the closest score
                            if (scoreMatches.length > 0) {
                                candidate.score = parseInt(scoreMatches[0][1]);
                                candidate.total_questions = parseInt(scoreMatches[0][2]);
                                
                                // Calculate percentage if missing
                                if (!candidate.percentage && candidate.total_questions > 0) {
                                    candidate.percentage = (candidate.score / candidate.total_questions) * 100;
                                }
                            }
                            
                            candidates.push(candidate);
                        }
                    }
                    
                    return candidates;
                }
            """)
            
            return result or []
            
        except Exception as e:
            logging.error(f"JavaScript extraction failed: {e}")
            return []
    
    async def _text_analysis_extraction(self, page) -> List[Dict]:
        """Analyze full page text for patterns"""
        try:
            page_content = await page.content()
            page_text = await page.evaluate("() => document.body.innerText")
            
            # Find all emails
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', page_text)
            
            candidates = []
            for email in set(emails):  # Remove duplicates
                # Find position of email in text
                email_pos = page_text.find(email)
                if email_pos == -1:
                    continue
                
                # Get context around email (1000 chars before and after)
                start = max(0, email_pos - 1000)
                end = min(len(page_text), email_pos + 1000)
                context = page_text[start:end]
                
                # Look for scores in context
                percentage_match = re.search(r'(\d+(?:\.\d+)?)%', context)
                score_match = re.search(r'(\d+)\s*/\s*(\d+)', context)
                
                if percentage_match or score_match:
                    candidate = {
                        'email': email,
                        'percentage': float(percentage_match.group(1)) if percentage_match else None,
                        'score': int(score_match.group(1)) if score_match else None,
                        'total_questions': int(score_match.group(2)) if score_match else None,
                        'method': 'text_analysis',
                        'context': context[:200] + "..." if len(context) > 200 else context
                    }
                    
                    # Calculate percentage if missing
                    if not candidate['percentage'] and candidate['score'] and candidate['total_questions']:
                        candidate['percentage'] = (candidate['score'] / candidate['total_questions']) * 100
                    
                    candidates.append(candidate)
            
            return candidates
            
        except Exception as e:
            logging.error(f"Text analysis failed: {e}")
            return []
    
    async def _element_search_extraction(self, page) -> List[Dict]:
        """Search element by element"""
        try:
            # Get all elements that might contain candidate data
            elements = await page.query_selector_all("*")
            
            candidates = []
            for element in elements:
                try:
                    text = await element.inner_text()
                    if not text or len(text) < 10 or len(text) > 1000:
                        continue
                    
                    # Must have email
                    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
                    if not email_match:
                        continue
                    
                    # Must have score or percentage
                    percentage_match = re.search(r'(\d+(?:\.\d+)?)%', text)
                    score_match = re.search(r'(\d+)\s*/\s*(\d+)', text)
                    
                    if percentage_match or score_match:
                        candidate = {
                            'email': email_match.group(),
                            'percentage': float(percentage_match.group(1)) if percentage_match else None,
                            'score': int(score_match.group(1)) if score_match else None,
                            'total_questions': int(score_match.group(2)) if score_match else None,
                            'method': 'element_search',
                            'element_text': text[:200] + "..." if len(text) > 200 else text
                        }
                        
                        # Calculate percentage if missing
                        if not candidate['percentage'] and candidate['score'] and candidate['total_questions']:
                            candidate['percentage'] = (candidate['score'] / candidate['total_questions']) * 100
                        
                        candidates.append(candidate)
                
                except:
                    continue
            
            return candidates
            
        except Exception as e:
            logging.error(f"Element search failed: {e}")
            return []
    
    def _save_results(self, assessment_name: str, results: List[Dict]):
        """Save results to file"""
        try:
            output_data = {
                "assessment_name": assessment_name,
                "scraped_at": datetime.now().isoformat(),
                "total_candidates": len(results),
                "candidates_with_scores": len([r for r in results if r.get('percentage') is not None]),
                "candidates": results
            }
            
            filename = f"fixed_results_{assessment_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            output_file = Path(OUTPUT_DIR) / filename
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            logging.info(f"Results saved to: {output_file}")
            
        except Exception as e:
            logging.error(f"Error saving results: {e}")
    
    async def _process_results(self, results: List[Dict]):
        """Process results and update database"""
        try:
            processed_count = 0
            
            for candidate_data in results:
                email = candidate_data.get('email')
                percentage = candidate_data.get('percentage')
                
                if not email or percentage is None:
                    continue
                
                # Find candidate in database
                candidate = self.session.query(Candidate).filter_by(email=email).first()
                if not candidate:
                    logging.warning(f"Candidate {email} not found in database")
                    continue
                
                # Update candidate
                candidate.exam_completed = True
                candidate.exam_completed_date = datetime.now()
                candidate.exam_percentage = percentage
                candidate.exam_score = candidate_data.get('score', 0)
                candidate.exam_total_questions = candidate_data.get('total_questions', 100)
                
                # Add feedback
                if percentage >= 70:
                    candidate.exam_feedback = f"Good performance! Score: {percentage:.1f}%"
                    candidate.final_status = 'Interview Scheduled'
                    candidate.interview_scheduled = True
                    candidate.interview_date = datetime.now() + timedelta(days=3)
                    
                    try:
                        interview_link = send_interview_link_email(candidate)
                        candidate.interview_link = interview_link
                        logging.info(f"✅ Interview scheduled: {email} ({percentage:.1f}%)")
                    except Exception as e:
                        logging.error(f"Failed to send interview email: {e}")
                else:
                    candidate.exam_feedback = f"Score: {percentage:.1f}% - Below threshold"
                    candidate.final_status = 'Rejected After Exam'
                    
                    try:
                        send_rejection_email(candidate)
                        logging.info(f"❌ Rejection sent: {email} ({percentage:.1f}%)")
                    except Exception as e:
                        logging.error(f"Failed to send rejection email: {e}")
                
                processed_count += 1
            
            self.session.commit()
            logging.info(f"Updated {processed_count} candidates with scores")
            
        except Exception as e:
            logging.error(f"Error processing results: {e}")
            self.session.rollback()


# Main functions for compatibility
async def scrape_assessment_results_by_name(assessment_name: str) -> List[Dict]:
    """Fixed scraping function"""
    scraper = TestlifyResultsScraperFixed()
    try:
        results = await scraper.scrape_assessment_results(assessment_name)
        return results
    finally:
        scraper.session.close()


async def scrape_all_pending_assessments():
    """Scrape all pending assessments"""
    session = SessionLocal()
    try:
        pending_assessments = session.query(Candidate.job_title).filter(
            and_(
                Candidate.exam_link_sent == True,
                Candidate.exam_completed == False
            )
        ).distinct().all()
        
        results_summary = {}
        
        for (assessment_name,) in pending_assessments:
            if assessment_name:
                logging.info(f"Scraping scores for: {assessment_name}")
                results = await scrape_assessment_results_by_name(assessment_name)
                scored_count = len([r for r in results if r.get('percentage') is not None])
                results_summary[assessment_name] = scored_count
        
        return results_summary
        
    finally:
        session.close()


# Test function
async def main():
    print("🔧 Fixed Testlify Scraper")
    print("=" * 40)
    
    assessment_name = input("Enter assessment name to test: ").strip()
    if assessment_name:
        print(f"\n🎯 Testing scraper with: {assessment_name}")
        results = await scrape_assessment_results_by_name(assessment_name)
        
        scored = [r for r in results if r.get('percentage') is not None]
        print(f"\n📊 Results:")
        print(f"   • Total found: {len(results)}")
        print(f"   • With scores: {len(scored)}")
        
        if scored:
            print(f"\n🎯 Scored candidates:")
            for candidate in scored:
                print(f"   • {candidate['email']}: {candidate['percentage']:.1f}% (method: {candidate.get('method', 'unknown')})")


if __name__ == "__main__":
    asyncio.run(main())