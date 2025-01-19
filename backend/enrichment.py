import cohere
import re
import os
from dotenv import load_dotenv

load_dotenv()

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
co = cohere.Client(COHERE_API_KEY)

def get_cohere_insights(query):
    try:
        response = co.generate(
            model='command-xlarge',
            prompt=f"Provide insights for the startup '{query}'. Please include:\n"
                   "Name: [name]\nEmail: [email]\nWebsite: [website]\nInsights: [details]",
            max_tokens=150,
            temperature=0.7
        )
        return response.generations[0].text.strip()
    except Exception as e:
        print(f"Cohere error: {e}")
        return "No insights available."

def parse_cohere_response(response_text):
    company_name = re.search(r"Name:\s*(.*?)\n", response_text)
    email = re.search(r"Email:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", response_text)
    website = re.search(r"Website:\s*(https?://[^\s]+)", response_text)
    insights = re.search(r"Insights:\s*(.*)", response_text)

    return {
        "name": company_name.group(1) if company_name else "Not available",
        "email": email.group(1) if email else "Not available",
        "link": website.group(1) if website else "Not available",
        "insights": insights.group(1) if insights else "No insights"
    }

def enrich_data(data):
    enriched = []
    for entry in data:
        cohere_response = get_cohere_insights(entry["name"])
        enriched_entry = parse_cohere_response(cohere_response)
        enriched_entry.update({"link": entry["link"], "email": entry["email"]})
        enriched.append(enriched_entry)
    return enriched
