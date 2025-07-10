import streamlit as st
import yfinance as yf
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import re
import io

# Constants
PHRASE = "accrued performance-based compensation"
START_DATE = "2024-01-01"
END_DATE = "2025-06-30"

RUSSELL_2000_CSV_URL = "https://raw.githubusercontent.com/datasets/russell-2000/master/data/russell-2000.csv"

# Helper functions
@st.cache_data(show_spinner=False)
def load_russell_2000_tickers():
    df = requests.get(RUSSELL_2000_CSV_URL).content.decode('utf-8').splitlines()
    tickers = [line.split(',')[0].strip() for line in df if line]
    return tickers

@st.cache_data(show_spinner=True)
def get_filings_metadata(ticker, start_date, end_date):
    # SEC EDGAR API search URL
    base_url = "https://data.sec.gov/submissions/CIK{}.json"

    # Convert ticker to CIK - EDGAR needs CIK padded with zeros
    cik = get_cik_for_ticker(ticker)
    if not cik:
        return []

    url = base_url.format(cik.zfill(10))
    headers = {'User-Agent': 'YourName your.email@example.com'}

    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        return []

    data = resp.json()
    filings = data.get('filings', {}).get('recent', {})
    accession_numbers = filings.get('accessionNumber', [])
    filing_dates = filings.get('filingDate', [])
    forms = filings.get('form', [])

    results = []
    for form, date, acc_num in zip(forms, filing_dates, accession_numbers):
        if form in ['10-Q', '10-K'] and start_date <= date <= end_date:
            results.append({'form': form, 'date': date, 'accession': acc_num, 'ticker': ticker})
    return results

@st.cache_data(show_spinner=True)
def get_cik_for_ticker(ticker):
    # Query SEC ticker to CIK mapping
    mapping_url = "https://www.sec.gov/files/company_tickers_exchange.json"
    headers = {'User-Agent': 'LucasWafelbakker lucaswafelbakker@gmail.com'}
    resp = requests.get(mapping_url, headers=headers)
    if resp.status_code != 200:
        return None
    data = resp.json()

    # The SEC endpoint sometimes returns a list of company mappings and sometimes
    # a dict whose values are the mappings (historical behaviour).  Support both
    # shapes so the app keeps working if the SEC changes the response format.
    if isinstance(data, dict):
        items = data.values()
    else:  # list or other iterable
        items = data

    for item in items:
        # Guard against unexpected structures
        try:
            if item.get("ticker", "").upper() == ticker.upper():
                return str(item.get("cik"))
        except AttributeError:
            # "item" isn't a mapping (dict-like), skip it
            continue
    return None

def download_filing_text(cik, accession):
    # Compose URL to filing text file (txt format)
    base = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-','')}/{accession}-index.html"
    headers = {'User-Agent': 'LucasWafelbakker lucaswafelbakker@gmail.com'}
    r = requests.get(base, headers=headers)
    if r.status_code != 200:
        return None
    soup = BeautifulSoup(r.text, 'html.parser')
    # Try to find link to full filing document (txt)
    doc_link = None
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.endswith('.txt') and accession.replace('-', '') in href:
            doc_link = 'https://www.sec.gov' + href
            break
    if not doc_link:
        return None
    r2 = requests.get(doc_link, headers=headers)
    if r2.status_code != 200:
        return None
    return r2.text

def search_phrase_in_text(text, phrase):
    # Case-insensitive search, return snippet if found
    pattern = re.compile(r'.{0,60}' + re.escape(phrase) + r'.{0,60}', re.IGNORECASE)
    matches = pattern.findall(text)
    return matches

# Streamlit UI
st.title("SEC Filing Phrase Search: Russell 2000 (No Market Cap Filter)")
st.write(f"Searching filings from {START_DATE} to {END_DATE} for phrase: **{PHRASE}**")

with st.spinner("Loading Russell 2000 tickers..."):
    tickers = load_russell_2000_tickers()

if st.button("Search filings for phrase"):
    results = []
    for ticker in tickers:
        filings = get_filings_metadata(ticker, START_DATE, END_DATE)
        if not filings:
            continue
        cik = get_cik_for_ticker(ticker)
        for f in filings:
            text = download_filing_text(cik, f['accession'])
            if not text:
                continue
            matches = search_phrase_in_text(text, PHRASE)
            if matches:
                for m in matches:
                    results.append({
                        "Ticker": ticker,
                        "Date": f['date'],
                        "Form": f['form'],
                        "Snippet": m
                    })
    if results:
        st.write(f"### Found {len(results)} matches:")
        for r in results:
            st.write(f"**{r['Ticker']}** | {r['Date']} | {r['Form']}")
            st.write(f"> {r['Snippet']}")
            st.write("---")
    else:
        st.write("No matches found.")
