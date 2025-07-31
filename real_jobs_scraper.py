import requests
from bs4 import BeautifulSoup
import csv
import json
import time

# Base URL for remote programming jobs (page 1)
BASE_URL = "https://weworkremotely.com/categories/remote-programming-jobs"

# List to store all job dictionaries
jobs = []


def scrape_page(page_num):
    """
    Scrape a single page of job listings.
    Args:
        page_num (int): The page number to scrape.
    Returns:
        list of dict: List of jobs found on the page.
    """
    # Construct URL for the current page
    url = BASE_URL if page_num == 1 else f"{BASE_URL}/page/{page_num}"
    print(f"Scraping page {page_num}: {url}")

    # Send GET request to fetch page content
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve page {page_num}, status: {response.status_code}")
        return None  # Stop if page not found or error

    # Parse the HTML content with BeautifulSoup
    soup = BeautifulSoup(response.text, "html.parser")

    # Find the section containing job listings
    job_section = soup.find("section", class_="jobs")
    if not job_section:
        print("No jobs section found, possibly end of pages.")
        return None

    # Find all <li> elements representing job posts, excluding 'view-all' links
    job_posts = job_section.find_all("li", class_=lambda c: c != "view-all")
    if not job_posts:
        print("No jobs found on this page.")
        return None

    jobs_on_page = []  # Temporary list for jobs on this page

    for job in job_posts:
        # Extract the link to the job posting
        link = job.find("a", href=True)
        if not link:
            continue  # Skip if no link

        job_url = "https://weworkremotely.com" + link["href"]

        # Extract company name
        company = job.find("span", class_="company")
        company_name = company.text.strip() if company else "N/A"

        # Extract job title
        title = job.find("span", class_="title")
        job_title = title.text.strip() if title else "N/A"

        # Extract location or region
        region = job.find("span", class_="region")
        location = region.text.strip() if region else "Worldwide"

        # Append the job as a dictionary
        jobs_on_page.append(
            {
                "title": job_title,
                "company": company_name,
                "location": location,
                "url": job_url,
            }
        )

    return jobs_on_page


def save_to_csv(filename, data):
    """
    Save list of jobs to a CSV file.
    Args:
        filename (str): CSV filename.
        data (list): List of job dicts.
    """
    with open(filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "company", "location", "url"])
        writer.writeheader()
        writer.writerows(data)
    print(f"✅ Saved {len(data)} jobs to {filename}")


def save_to_json(filename, data):
    """
    Save list of jobs to a JSON file.
    Args:
        filename (str): JSON filename.
        data (list): List of job dicts.
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved {len(data)} jobs to {filename}")


def main():
    page = 1

    while True:
        scraped_jobs = scrape_page(page)
        if not scraped_jobs:
            break  # Stop if no jobs or error on this page

        jobs.extend(scraped_jobs)
        page += 1

        # Sleep for 2 seconds to be polite and avoid rate-limiting
        time.sleep(2)

    if jobs:
        save_to_csv("weworkremotely_jobs.csv", jobs)
        save_to_json("weworkremotely_jobs.json", jobs)
    else:
        print("No jobs found.")


if __name__ == "__main__":
    main()
