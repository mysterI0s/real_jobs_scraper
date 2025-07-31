import asyncio
from playwright.async_api import async_playwright
import json
import pandas as pd
import random


async def scrape_jobs():
    all_jobs = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # Keep False for debugging
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--disable-extensions",
                "--no-first-run",
                "--disable-default-apps",
            ],
        )

        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
            extra_http_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            },
        )
        page = await context.new_page()

        # Add stealth measures
        await page.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """
        )

        for page_num in range(1, 6):
            print(f"🔎 Scraping page {page_num}...")

            url = f"https://weworkremotely.com/categories/remote-programming-jobs?page={page_num}"

            try:
                await page.goto(url, timeout=100000, wait_until="networkidle")

                # Add random delay to seem more human-like
                await asyncio.sleep(random.uniform(2, 4))

                # Wait for page to be ready - just wait for any job section to exist
                await page.wait_for_selector("section.jobs", timeout=15000)

                # Try multiple possible selectors for job listings
                possible_selectors = [
                    "section.jobs li a",
                    "section.jobs ul li a",
                    "section.jobs article ul li a",
                    ".jobs li a",
                    "li.feature a",
                    "article li a",
                ]

                job_list_items = None
                working_selector = None

                # Don't wait for visibility, just check if elements exist
                for selector in possible_selectors:
                    try:
                        job_list_items = await page.query_selector_all(selector)
                        if job_list_items and len(job_list_items) > 0:
                            working_selector = selector
                            print(
                                f"✅ Found {len(job_list_items)} jobs using selector: {selector}"
                            )
                            break
                        else:
                            print(f"⚠️ Selector '{selector}' found 0 elements")
                    except Exception as e:
                        print(f"⚠️ Selector '{selector}' failed: {e}")
                        continue

                if not job_list_items:
                    print(f"❌ No jobs found on page {page_num} with any selector")
                    # Save page content for debugging
                    content = await page.content()
                    with open(
                        f"debug_page_{page_num}.html", "w", encoding="utf-8"
                    ) as f:
                        f.write(content)
                    continue

                print(
                    f"📋 Found {len(job_list_items)} potential job items on page {page_num}"
                )

                # Filter out non-job links (like company pages, trending pages, etc.)
                filtered_jobs = []
                print("🔍 First few links found:")
                for idx, item in enumerate(
                    job_list_items[:5]
                ):  # Show first 5 links for debugging
                    link = await item.get_attribute("href")
                    text = await item.inner_text()
                    print(f"   Link {idx+1}: {link} | Text: {text[:50]}...")

                for item in job_list_items:
                    link = await item.get_attribute("href")
                    # Skip links that are clearly not job postings
                    if link and any(
                        skip in link
                        for skip in ["/company/", "/top-trending", "/categories"]
                    ):
                        continue
                    filtered_jobs.append(item)

                print(
                    f"📋 After filtering: {len(filtered_jobs)} actual job items on page {page_num}"
                )

                for i, item in enumerate(filtered_jobs):
                    try:
                        # Try different combinations for title and company selectors
                        title = "N/A"
                        company = "N/A"

                        # Try multiple selectors for title
                        title_selectors = ["span.title", ".title", "h2", ".job-title"]
                        for ts in title_selectors:
                            title_el = await item.query_selector(ts)
                            if title_el:
                                title = await title_el.inner_text()
                                break

                        # Try multiple selectors for company
                        company_selectors = [
                            "span.company",
                            ".company",
                            ".company-name",
                            "span:last-child",
                        ]
                        for cs in company_selectors:
                            company_el = await item.query_selector(cs)
                            if company_el:
                                company = await company_el.inner_text()
                                break

                        # Get the link
                        link = await item.get_attribute("href")

                        # Skip if this doesn't look like a job posting link
                        if not link or any(
                            skip in link
                            for skip in [
                                "/company/",
                                "/top-trending",
                                "/categories",
                                "mailto:",
                            ]
                        ):
                            continue

                        # If we couldn't find title/company in nested elements, try getting text directly
                        if title == "N/A" or company == "N/A":
                            full_text = await item.inner_text()
                            # Try to parse the text (usually title and company are on separate lines)
                            lines = [
                                line.strip()
                                for line in full_text.split("\n")
                                if line.strip()
                            ]
                            if len(lines) >= 2:
                                if title == "N/A":
                                    title = lines[0]
                                if company == "N/A":
                                    # Company is often in the format "Company Name" or "at Company Name"
                                    company_line = lines[1]
                                    if company_line.lower().startswith("at "):
                                        company = company_line[3:]
                                    else:
                                        company = company_line

                        # Skip if we still don't have meaningful data
                        if title == "N/A" or company == "N/A" or not link:
                            print(
                                f"   ⚠️ Skipping job {i+1}: insufficient data (title: {title}, company: {company}, link: {bool(link)})"
                            )
                            continue

                        full_link = (
                            f"https://weworkremotely.com{link}"
                            if link and link.startswith("/")
                            else link
                        )

                        job_data = {
                            "title": title.strip() if title else "N/A",
                            "company": company.strip() if company else "N/A",
                            "link": full_link,
                            "page": page_num,
                        }

                        all_jobs.append(job_data)
                        print(
                            f"   ✓ Job {i+1}: {job_data['title']} at {job_data['company']}"
                        )

                    except Exception as e:
                        print(f"⚠️ Error extracting job {i+1}: {e}")
                        continue

                # Add delay between pages
                await asyncio.sleep(random.uniform(3, 6))

            except Exception as e:
                print(f"❌ Error on page {page_num}: {e}")
                # Save page content for debugging
                try:
                    content = await page.content()
                    with open(
                        f"debug_page_{page_num}.html", "w", encoding="utf-8"
                    ) as f:
                        f.write(content)
                except:
                    pass
                continue

        await browser.close()

    # Save the results
    print(f"\n📊 Summary: Scraped {len(all_jobs)} jobs total")

    if all_jobs:
        with open("wework_jobs.json", "w", encoding="utf-8") as f:
            json.dump(all_jobs, f, indent=4, ensure_ascii=False)

        df = pd.DataFrame(all_jobs)
        df.to_csv("wework_jobs.csv", index=False)

        print("📁 Saved to 'wework_jobs.json' and 'wework_jobs.csv'")

        # Print some sample jobs
        print("\n🔍 Sample jobs found:")
        for job in all_jobs[:3]:
            print(f"   • {job['title']} at {job['company']}")
    else:
        print("❌ No jobs were scraped. Check the debug HTML files for more info.")


if __name__ == "__main__":
    asyncio.run(scrape_jobs())
