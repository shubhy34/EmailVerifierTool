import streamlit as st
import requests
import re
from bs4 import BeautifulSoup
from serpapi import GoogleSearch
import pandas as pd

# Set your SerpAPI key
SERPAPI_KEY = "0a72b64bccab9ced37cbd5c071e9368b829facd6f6e0a7d42d3e89bf8c2f0d55"

# List of untrusted and trusted domains
IGNORE_SITES = ['intelius.com', 'rocketreach.co', 'zoominfo.com', 'aeroleads.com']
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
        st.error(f"Error fetching results: {e}")
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
    results = fetch_search_results(f'"@{domain}"')
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
    result = check_email_exact(email)
    if result:
        return result
    else:
        return check_domain_pattern(email)

# Streamlit UI
st.title("📧 Email Verifier Tool")
st.write("Enter email addresses manually or upload a .csv/.txt file.")

email_input = st.text_area("Enter emails separated by comma or newline")
file_upload = st.file_uploader("Or upload a .csv or .txt file", type=["csv", "txt"])

emails = []
if email_input:
    emails += [e.strip() for e in re.split(r'[\n,]+', email_input) if e.strip()]

if file_upload:
    if file_upload.name.endswith(".csv"):
        df_uploaded = pd.read_csv(file_upload, header=None)
        emails += df_uploaded.iloc[:, 0].dropna().astype(str).tolist()
    elif file_upload.name.endswith(".txt"):
        content = file_upload.read().decode("utf-8")
        emails += [e.strip() for e in re.split(r'[\n,]+', content) if e.strip()]

emails = list(set(emails))  # Remove duplicates

if emails:
    if st.button("🔍 Verify Emails"):
        results = []
        for email in emails:
            try:
                status = verify_email(email)
            except Exception as e:
                status = f"Error: {str(e)}"
            results.append({"Email": email, "Status": status})

        df_results = pd.DataFrame(results)
        st.write("## ✅ Verification Results")
        st.dataframe(df_results)

        csv = df_results.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Download Results", csv, "verification_results.csv", "text/csv")
else:
    st.info("Enter at least one email address or upload a file.")
