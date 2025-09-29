import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime
import os

class JobYaariScraper:
    def __init__(self):
        self.base_url = "https://www.jobyaari.com/category"
        self.categories = ["engineering", "science", "commerce", "education"]
        self.jobs_data = []

    def fetch_html(self, url):
        try:
            response = requests.get(url, timeout=10, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def parse_job_card(self, job_card):
        try:
            title_elem = job_card.select_one(".ribbon1-shape span")
            title = title_elem.get_text(strip=True) if title_elem else "N/A"

            org_elem = job_card.select_one(".drop__profession")
            organization = org_elem.get_text(strip=True) if org_elem else "N/A"

            salary_elem = job_card.select_one(".salary-price span:last-child")
            salary = salary_elem.get_text(strip=True) if salary_elem else "N/A"

            exp_elem = job_card.select_one(".drop__exp span:last-child")
            experience = exp_elem.get_text(strip=True) if exp_elem else "N/A"

            qual_elem = job_card.select_one(".salary")
            qualification = qual_elem.get_text(strip=True) if qual_elem else "N/A"

            loc_elem = job_card.select_one(".location span:last-child")
            location = loc_elem.get_text(strip=True) if loc_elem else "N/A"

            tags = [t.get_text(strip=True) for t in job_card.select(".tags-item")]

            post_elem = job_card.select_one(".post-item")
            post_date_raw = post_elem.get_text(strip=True).replace("Posted", "").strip() if post_elem else "N/A"

            # Clean the date: remove "Last date:" and convert to DD/MM/YYYY
            def clean_date(val):
                if val == "N/A":
                    return val
                val = re.sub(r'Last\s*date[:\-]?', '', val, flags=re.I).strip()
                for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d %b %Y", "%d %B %Y"):
                    try:
                        dt = datetime.strptime(val, fmt)
                        return dt.strftime("%d/%m/%Y")
                    except:
                        continue
                return val
            last_date = clean_date(post_date_raw)
            return {
                "title": title,
                "organization": organization,
                "salary": salary,
                "experience": experience,
                "qualification": qualification,
                "location": location,
                "tags": ", ".join(tags) if tags else "N/A",
                "last_date": last_date
            }
        except Exception as e:
            print(f"Error parsing job card: {e}")
            return None

    def scrape_category(self, category):
        url = f"{self.base_url}/{category}"
        print(f"Scraping {category} category...")
        soup = self.fetch_html(url)
        if not soup:
            return
        job_cards = soup.find_all("div", class_="drop__card")
        print(f"Found {len(job_cards)} job cards in {category} category")
        for job_card in job_cards:
            job_data = self.parse_job_card(job_card)
            if job_data:
                job_data["category"] = category
                self.jobs_data.append(job_data)

    def scrape(self):
        print("Starting JobYaari Scraper...")
        for category in self.categories:
            self.scrape_category(category)
        if not self.jobs_data:
            print("No data extracted")
            return None
        df = pd.DataFrame(self.jobs_data)
        print(f"Extracted {len(df)} job postings")
        return df

    def save_to_excel(self, df, filename="data/jobyaari_jobs.xlsx"):
        # Create data folder if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        df.to_excel(filename, index=False)
        print(f"Saved data to {filename}")


if __name__ == "__main__":
    scraper = JobYaariScraper()
    df = scraper.scrape()
    if df is not None:
        scraper.save_to_excel(df)
