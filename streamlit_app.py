from serpapi import GoogleSearch
from bs4 import BeautifulSoup
import requests
import re

# 🔑 Your SerpAPI key
SERPAPI_KEY = "0a72b64bccab9ced37cbd5c071e9368b829facd6f6e0a7d42d3e89bf8c2f0d55"

# Sites we don't trust for verification
IGNORE_SITES = ['intelius.com', 'rocketreach.co', 'zoominfo.com', 'aeroleads.com']

# Sites we consider trusted (like WikiLeaks, news sites etc)
TRUSTED_SOURCES = ['wikileaks.org', 'nytimes.com', 'media.']

def is_valid_source(url):
    return not any(site in url for site in IGNORE_SITES)

def is_trusted_source(url):
    return any(site in url for site in TRUSTED_SOURCES)

def fetch_search_results(query, num=10):
    params = {
        "q": query,
        "num": num,
        "api_key": SERPAPI_KEY,
        "engine": "google",
    }
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        links = []
        if "organic_results" in results:
            for result in results["organic_results"]:
                links.append(result.get("link", ""))
        return links
    except Exception as e:
        print(f"Error fetching results: {e}")
        return []

def extract_domain(email):
    return email.split('@')[-1]

def check_email_exact(email):
    results = fetch_search_results(f'"{email}"')
    for url in results:
        if is_valid_source(url) and is_trusted_source(url):
            return "Verified (Trusted Source)"
    return None

def check_domain_pattern(email):
    domain = extract_domain(email)
    domain_query = f'"@{domain}"'
    results = fetch_search_results(domain_query)
    for url in results:
        if is_valid_source(url):
            try:
                r = requests.get(url, timeout=10)
                soup = BeautifulSoup(r.text, 'html.parser')
                found_emails = re.findall(r"[a-zA-Z0-9_.+-]+@" + re.escape(domain), soup.text)
                found_emails = list(set(found_emails))
                found_emails = [e for e in found_emails if e.lower() != email.lower()]
                if found_emails:
                    return f"Pattern Verified (Based on emails like: {', '.join(found_emails[:3])})"
            except:
                continue
    return "Not Verified"

def verify_email(email):
    print(f"Checking: {email}")
    result = check_email_exact(email)
    if result:
        return result
    else:
        return check_domain_pattern(email)

def run_verification():
    emails_input = input("Enter email(s), separated by comma: ")
    emails = [email.strip() for email in emails_input.split(',')]
    print("\n--- VERIFICATION RESULTS ---")
    for email in emails:
        status = verify_email(email)
        print(f"{email}: {status}")

if __name__ == "__main__":
    run_verification()
