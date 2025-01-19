import re
import sqlite3
import time
import cohere
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import os
from dotenv import load_dotenv


load_dotenv()


COHERE_API_KEY = os.getenv("COHERE_API_KEY")
co = cohere.Client(COHERE_API_KEY)


def init_db():
    conn = sqlite3.connect("leads.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS leads
                      (id INTEGER PRIMARY KEY, 
                       name TEXT, 
                       link TEXT, 
                       email TEXT, 
                       insights TEXT)''')
    conn.commit()
    conn.close()


def save_to_db(data):
    conn = sqlite3.connect("leads.db")
    cursor = conn.cursor()
    for entry in data:
        cursor.execute("INSERT INTO leads (name, link, email, insights) VALUES (?, ?, ?, ?)",
                       (entry["name"], entry["link"], entry["email"], entry.get("insights", "No insights")))
    conn.commit()
    conn.close()


def extract_emails_from_text(text):
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return re.findall(email_pattern, text)


def parse_cohere_response(response_text):
    company_name = re.search(r"Name:\s*(.*?)\n", response_text)
    email = re.search(r"Email:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", response_text)
    website = re.search(r"Website:\s*(https?://[^\s]+)", response_text)
    insights = re.search(r"Insights:\s*(.*)", response_text)

    return {
        "name": company_name.group(1) if company_name else "Not available",
        "email": email.group(1) if email else "Not available",
        "link": website.group(1) if website else "Not available",
        "insights": insights.group(1) if insights else "Not available"
    }


def get_cohere_insights(query):
    retries = 5
    for attempt in range(retries):
        try:
            response = co.generate(
                model='command-xlarge',  
                prompt = 
    "Generate a list of startups in India with complete details. For each startup, "
    "provide the following:\n"
    "Name: [Startup name]\n"
    "Website: [Startup's official website]\n"
    "Email: [Valid contact email]\n"
    "Insights: [A brief description about the startup]\n\n"
    "Include only startups that have a valid website, email, and name. "
    "The insights should highlight the startup's focus or unique qualities. "
    "Generate random entries for startups that are not already known.",


                max_tokens=300,
                temperature=0.7
            )

            insights = response.generations[0].text.strip()
            return insights
        except Exception as e:
            print(f"Error while processing request: {e}")
            return None
    print("Max retries reached for Cohere.")
    return None


def process_and_store_cohere_data():
    cohere_response = get_cohere_insights("Top startups in India")
    if not cohere_response:
        print("No data received from Cohere.")
        return

    
    startups = cohere_response.split("\n\n")  
    parsed_data = []

    for startup in startups:
        parsed_startup = parse_cohere_response(startup)
        
        if (
            parsed_startup["name"] != "Not available" and
            parsed_startup["email"] != "Not available" and
            parsed_startup["link"] != "Not available" and
            parsed_startup["insights"] != "Not available"
        ):
            parsed_data.append(parsed_startup)
            print(f"Processed: {parsed_startup}")
        else:
            print(f"Skipped incomplete entry: {parsed_startup}")

    
    if parsed_data:
        save_to_db(parsed_data)
        print("Complete startups data saved to database.")
    else:
        print("No complete data to save.")


def scrape_crunchbase():
    driver_path = ChromeDriverManager().install()
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service)

    driver.get("https://www.crunchbase.com/")

    wait = WebDriverWait(driver, 30)
    try:
        search_box = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/chrome/div/app-header/div[1]/multi-search/form/input")))
        search_box.send_keys("startups")
        search_box.send_keys(Keys.RETURN)
        time.sleep(5)

        organizations_section = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/chrome/div/mat-sidenav-container/mat-sidenav-content/div/multi-search-results/page-layout/div/div/div/search-results-section[1]/div/div[2]/span/a")))
        organizations_section.click()
        time.sleep(3)

        data = []
        startups = driver.find_elements(By.CSS_SELECTOR, ".search-card-title")

        for startup in startups:
            name = startup.text
            link = startup.find_element(By.TAG_NAME, "a").get_attribute("href")

            driver.get(link)
            time.sleep(3)
            page_text = driver.find_element(By.TAG_NAME, "body").text
            emails = extract_emails_from_text(page_text)

            email = emails[0] if emails else "No email found"
            insights = get_cohere_insights(name) if email != "No email found" else "No insights available"
            data.append({"name": name, "link": link, "email": email, "insights": insights})

        driver.quit()
        return data
    except Exception as e:
        # print(f"Error during scraping: {e}")
        driver.quit()
        print("Fallback to Cohere for insights generation.")
        process_and_store_cohere_data()  
        return []


if __name__ == "__main__":
    init_db()
    leads = scrape_crunchbase()
    if leads:
        save_to_db(leads)
        print("Data saved to database successfully.")
    else:
        print("No leads were scraped or saved.")
