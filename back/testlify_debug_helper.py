# testlify_debug_helper.py - Debug the exact HTML structure

import asyncio
import logging
from playwright.async_api import async_playwright
import re
from datetime import datetime

USER_DATA_DIR = r"D:\interview link\testlify_browser_profile"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def debug_testlify_structure(assessment_name: str):
    """Debug the exact HTML structure of Testlify assessment page"""
    
    async with async_playwright() as playwright:
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            viewport={'width': 1400, 'height': 1000}
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        try:
            print("🔍 Starting Testlify Structure Debug")
            print("=" * 50)
            
            # Navigate to assessments
            await page.goto("https://app.testlify.com/assessments", wait_until="networkidle", timeout=90000)

            await asyncio.sleep(3)
            
            # Check login
            if await page.query_selector("input[type='email']"):
                print("🔐 Please log in manually...")
                input("Press ENTER after logging in: ")
                await page.wait_for_load_state("networkidle")
            
            # Find and click assessment
            print(f"📋 Looking for assessment: {assessment_name}")
            
            # Try to find the assessment
            found = False
            try:
                element = await page.wait_for_selector(f"text={assessment_name}", timeout=5000)
                await element.click()
                found = True
                print("✅ Found assessment!")
            except:
                print("❌ Assessment not found with exact match, trying partial...")
                elements = await page.query_selector_all("*")
                for element in elements:
                    try:
                        text = await element.inner_text()
                        if assessment_name.lower() in text.lower() and len(text.strip()) < 100:
                            await element.click()
                            found = True
                            print("✅ Found assessment with partial match!")
                            break
                    except:
                        continue
            
            if not found:
                print("❌ Could not find assessment")
                return
            
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)
            
            print("🔍 Analyzing page structure...")
            
            # Debug 1: Check page title and URL
            title = await page.title()
            url = page.url
            print(f"📄 Page Title: {title}")
            print(f"🌐 URL: {url}")
            
            # Debug 2: Find all elements with emails
            print("\n📧 Looking for email patterns...")
            page_content = await page.content()
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', page_content)
            print(f"Found {len(set(emails))} unique emails:")
            for email in list(set(emails))[:10]:  # Show first 10
                print(f"   • {email}")
            
            # Debug 3: Find all percentage patterns
            print("\n📊 Looking for percentage patterns...")
            percentages = re.findall(r'(\d+(?:\.\d+)?)%', page_content)
            print(f"Found {len(percentages)} percentage values:")
            for pct in percentages[:10]:  # Show first 10
                print(f"   • {pct}%")
            
            # Debug 4: Find score patterns (like 3/104)
            print("\n🎯 Looking for score patterns...")
            scores = re.findall(r'(\d+)/(\d+)', page_content)
            print(f"Found {len(scores)} score patterns:")
            for score in scores[:10]:  # Show first 10
                print(f"   • {score[0]}/{score[1]}")
            
            # Debug 5: Analyze table structure
            print("\n📋 Analyzing table structure...")
            tables = await page.query_selector_all("table")
            print(f"Found {len(tables)} tables")
            
            for i, table in enumerate(tables):
                try:
                    rows = await table.query_selector_all("tr")
                    print(f"   Table {i+1}: {len(rows)} rows")
                    
                    if rows:
                        # Analyze first few rows
                        for j, row in enumerate(rows[:3]):
                            cells = await row.query_selector_all("td, th")
                            row_text = await row.inner_text()
                            print(f"     Row {j+1}: {len(cells)} cells")
                            print(f"     Text: {row_text[:100]}...")
                            
                            # Check if this row has email + score
                            if '@' in row_text and ('%' in row_text or '/' in row_text):
                                print(f"     ⭐ CANDIDATE ROW FOUND!")
                                print(f"     Full text: {row_text}")
                except Exception as e:
                    print(f"   Error analyzing table {i+1}: {e}")
            
            # Debug 6: Look for div/card structures
            print("\n🎴 Analyzing card/div structures...")
            cards = await page.query_selector_all(".card, .candidate, [class*='result'], [class*='candidate']")
            print(f"Found {len(cards)} potential candidate cards")
            
            for i, card in enumerate(cards[:5]):  # Check first 5
                try:
                    card_text = await card.inner_text()
                    if '@' in card_text:
                        print(f"   Card {i+1} (has email):")
                        print(f"     Text: {card_text[:150]}...")
                except:
                    continue
            
            # Debug 7: JavaScript deep dive
            print("\n🔧 Running JavaScript analysis...")
            js_result = await page.evaluate("""
                () => {
                    const results = {
                        emails_found: [],
                        scores_found: [],
                        elements_with_both: []
                    };
                    
                    const emailRegex = /\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b/;
                    const percentageRegex = /(\\d+(?:\\.\\d+)?)%/;
                    const scoreRegex = /(\\d+)\\/(\\d+)/;
                    
                    const allElements = document.querySelectorAll('*');
                    
                    for (let element of allElements) {
                        const text = element.textContent || '';
                        
                        if (text.length > 5 && text.length < 500) {  // Reasonable text length
                            const hasEmail = emailRegex.test(text);
                            const hasPercentage = percentageRegex.test(text);
                            const hasScore = scoreRegex.test(text);
                            
                            if (hasEmail) {
                                const emailMatch = text.match(emailRegex);
                                results.emails_found.push({
                                    email: emailMatch[0],
                                    element_tag: element.tagName,
                                    element_class: element.className,
                                    text_sample: text.substring(0, 100)
                                });
                            }
                            
                            if (hasPercentage || hasScore) {
                                const percentageMatch = text.match(percentageRegex);
                                const scoreMatch = text.match(scoreRegex);
                                
                                results.scores_found.push({
                                    percentage: percentageMatch ? percentageMatch[1] : null,
                                    score: scoreMatch ? scoreMatch[1] + '/' + scoreMatch[2] : null,
                                    element_tag: element.tagName,
                                    element_class: element.className,
                                    text_sample: text.substring(0, 100)
                                });
                            }
                            
                            if (hasEmail && (hasPercentage || hasScore)) {
                                results.elements_with_both.push({
                                    email: text.match(emailRegex)[0],
                                    percentage: hasPercentage ? text.match(percentageRegex)[1] : null,
                                    score: hasScore ? text.match(scoreRegex)[0] : null,
                                    element_tag: element.tagName,
                                    element_class: element.className,
                                    element_id: element.id,
                                    text_sample: text.substring(0, 150)
                                });
                            }
                        }
                    }
                    
                    return results;
                }
            """)
            
            print(f"📧 JavaScript found {len(js_result['emails_found'])} email elements")
            print(f"📊 JavaScript found {len(js_result['scores_found'])} score elements")
            print(f"⭐ JavaScript found {len(js_result['elements_with_both'])} elements with BOTH email and score!")
            
            if js_result['elements_with_both']:
                print("\n🎯 CANDIDATE DATA ELEMENTS:")
                for i, element in enumerate(js_result['elements_with_both'][:5]):
                    print(f"   Element {i+1}:")
                    print(f"     Email: {element['email']}")
                    print(f"     Score: {element.get('score', 'None')} | Percentage: {element.get('percentage', 'None')}%")
                    print(f"     Tag: {element['element_tag']} | Class: {element['element_class'][:50]}...")
                    print(f"     Text: {element['text_sample']}...")
                    print()
            
            # Debug 8: Save full page for analysis
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save screenshot
            screenshot_path = f"debug_screenshot_{timestamp}.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"📸 Screenshot saved: {screenshot_path}")
            
            # Save HTML
            html_path = f"debug_page_{timestamp}.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(await page.content())
            print(f"💾 HTML saved: {html_path}")
            
            # Debug 9: Interactive mode
            print("\n🔧 INTERACTIVE MODE")
            print("The browser will stay open. You can:")
            print("1. Inspect elements manually")
            print("2. Try different selectors in browser console")
            print("3. Identify the exact structure")
            
            input("Press ENTER when you're done investigating...")
            
        except Exception as e:
            print(f"❌ Debug error: {e}")
            await page.screenshot(path=f"debug_error_{int(asyncio.get_event_loop().time())}.png")
        
        finally:
            await context.close()


async def main():
    print("🐛 Testlify Structure Debugger")
    print("=" * 40)
    print("This tool will help us understand the exact HTML structure")
    print("of Testlify's assessment page to improve score extraction.")
    print("=" * 40)
    
    assessment_name = input("Enter assessment name to debug: ").strip()
    if not assessment_name:
        print("❌ Assessment name required!")
        return
    
    await debug_testlify_structure(assessment_name)
    
    print("\n✅ Debug complete!")
    print("Check the generated files:")
    print("• debug_screenshot_*.png - Visual of the page")
    print("• debug_page_*.html - Full HTML source")
    print("\nUse this information to improve the scraper!")


if __name__ == "__main__":
    asyncio.run(main())