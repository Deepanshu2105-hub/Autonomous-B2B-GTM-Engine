Autonomous B2B Go-To-Market Engine
A fully autonomous, 6-agent outbound pipeline engineered entirely inside Google Sheets using Google Apps Script and the Groq API (LLaMA-3). Operating cost: $0.00.

Architecture & Capabilities:

Agent 0 (Stateful Prospecting): Generates strict JSON leads based on an ICP prompt. Engineered with a dynamic "Exclusion Array" that scrapes the Google Sheet database before API calls to force the stateless LLM to bypass previously contacted companies, ensuring infinite, deduplicated scaling.

Agent 1 (Scraper & Verifier): Bypasses basic bot-protection to scrape prospect website <title> tags and meta descriptions for context. Automatically verifies site uptime and cross-references email domains.

Agents 2 & 3 (NLP Qualifier & Copywriter): Analyzes scraped context to identify buying signals and drafts highly personalized, 3-sentence cold emails.

Agents 4 & 5 (Integration): Pushes approved email copy directly into Gmail Drafts and triggers an automated status notification via MailApp.

📊 V1 Analytics Dashboard (Included)
I built a local Python web application using streamlit and pandas to visualize the historical outreach data from my V1 manual tracker.

Parses legacy CSV exports.

Calculates total API cost savings.

Visualizes pipeline velocity over time.

To run locally:
pip install -r requirements.txt
streamlit run app.py
