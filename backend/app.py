from flask import Flask, jsonify, render_template
from scraper import scrape_crunchbase
from enrichment import enrich_data
from database import (
    save_to_db,
    fetch_leads,
    is_already_in_db,
    get_progress_from_db,
    update_progress,
    get_leads_count
)
from apscheduler.schedulers.background import BackgroundScheduler
import sqlite3
import time

app = Flask(__name__)

error_count = 0

def get_leads_count():
    """Fetch the total number of rows in the leads table."""
    connection = sqlite3.connect('leads.db')
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM leads")
    count = cursor.fetchone()[0]

    connection.close()
    return count

def initialize_progress():
    """Initialize the scraping progress when the app starts."""
    global last_scraped_time, scraped_count, error_count

    last_scraped_time = time.strftime("%Y-%m-%d %H:%M:%S")

    scraped_count = get_leads_count()

    error_count = 0

    print(f"Progress initialized: Last scraped time: {last_scraped_time}, Scraped count: {scraped_count}, Errors: {error_count}")

@app.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('index.html')


@app.route('/api/leads', methods=['GET'])
def get_leads():
    """Fetch and return all leads from the database."""
    leads = fetch_leads()
    formatted_leads = [
        {"id": lead[0], "name": lead[1], "link": lead[2], "insights": lead[3], "email": lead[4]}
        for lead in leads
    ]
    return jsonify(formatted_leads)


@app.route('/api/progress', methods=['GET'])
def get_progress():
    """Fetch and return the progress of the scraping job."""
    global last_scraped_time, error_count

    scraped_count = get_leads_count()

    progress = {
        "last_update": last_scraped_time,  
        "scraped_count": scraped_count,   
        "error_count": error_count,       
    }
    return jsonify(progress)

@app.route('/api/scrape', methods=['POST'])
def scrape_and_enrich():
    """Trigger the scraping and enrichment process."""
    global last_scraped_time, scraped_count, error_count
    try:
        
        scraped_data = scrape_crunchbase()

        
        new_data = [entry for entry in scraped_data if not is_already_in_db(entry)]

        if not new_data:
            return jsonify({"status": "success", "message": "new leads to save."})

        
        enriched_data = enrich_data(new_data)
        save_to_db(enriched_data)

        
        last_scraped_time = time.strftime("%Y-%m-%d %H:%M:%S")
        scraped_count = get_leads_count()
        update_progress(last_scraped_time, scraped_count, error_count)

        return jsonify({"status": "success", "message": f"Scraped and saved {len(enriched_data)} new leads."})

    except Exception as e:
        error_count += 1
        update_progress(last_scraped_time, scraped_count, error_count)
        return jsonify({"status": "error", "message": f"An error occurred: {str(e)}"})


def scheduled_scraping_job():
    """Scheduled job to scrape and enrich data every 4 hours."""
    global last_scraped_time, scraped_count, error_count
    try:
        scraped_data = scrape_crunchbase()
        new_data = [entry for entry in scraped_data if not is_already_in_db(entry)]
        enriched_data = enrich_data(new_data)
        save_to_db(enriched_data)

        
        last_scraped_time = time.strftime("%Y-%m-%d %H:%M:%S")
        scraped_count = get_leads_count()
        update_progress(last_scraped_time, scraped_count, error_count)

        print(f"Scheduled scraping completed. Saved {len(enriched_data)} new leads.")

    except Exception as e:
        error_count += 1
        update_progress(last_scraped_time, scraped_count, error_count)
        print(f"Scheduled scraping encountered an error: {str(e)}")



scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_scraping_job, 'interval', seconds=45)
scheduler.start()


scrape_crunchbase()
initialize_progress()
if __name__ == '__main__':
    app.run(port=5000)
