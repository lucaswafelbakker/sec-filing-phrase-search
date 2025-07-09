# SEC Filing Phrase Search App

This Streamlit app searches through 10-K and 10-Q filings of Russell 2000 companies for a specific phrase.

## Features

- Searches SEC filings between 2024-01-01 and 2025-06-30 for all companies in Russell 2000
- Retrieves and scans SEC filings for phrase: `"of accrued performance-based compensation"`
- Displays contextual snippets if found

## How to Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deployment

You can deploy this app using [Streamlit Cloud](https://streamlit.io/cloud) by uploading the contents of this repo.

## Notes

Make sure to set a valid SEC `User-Agent` header in the app.
