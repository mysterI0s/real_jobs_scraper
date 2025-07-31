# 🕷️ WeWorkRemotely Job Scraper (Playwright + Python)

This script scrapes remote programming jobs from [WeWorkRemotely](https://weworkremotely.com/categories/remote-programming-jobs) using **Playwright** with **async Python**.

It collects job title, company name, and job link from multiple pages and saves them into:
- `wework_jobs.json`
- `wework_jobs.csv`

## 📦 Features

- 🔄 Scrapes multiple pages (5 by default)
- ⚡ Uses Playwright for fast, headless browser automation
- ✅ Saves output in both JSON and CSV formats
- 🔍 Handles missing jobs or network issues gracefully

---

## 🛠️ Environment Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/weworkremotely-scraper.git
cd weworkremotely-scraper
```
### 2. Create a virtual environment (optional but recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```
### 3. Install dependencies
```bash
pip install -r requirements.txt
pip install playwright
```
### 4. Install Playwright browsers
```bash
playwright install
```
## 🚀 Run the Scraper
```bash
python real_jobs_scraper.py
```
Or with async runner:
```bash
python -m asyncio real_jobs_scraper.py
```
## 📚 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

Let me know if you’d like to:
- Add logging support  
- Deploy it as a scheduled job  
- Extend it to scrape more job types or sites
