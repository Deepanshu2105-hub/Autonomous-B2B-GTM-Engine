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


🔄 Legacy Data Migration Tool (V1 → V2)
To ensure a smooth transition from the manual V1 tracker to the fully autonomous V2 JSON-based architecture, I engineered a Python-based data migration pipeline using pandas.

Features:

Dynamically standardizes legacy column headers.

Implements case-insensitive deduplication to prevent duplicate outreach.

Scrubs incomplete records (missing email addresses).

Exports a strictly formatted v2_ready_leads.csv for immediate ingestion.

To run the pipeline:
python migrate_v1_to_v2.py old_v1_tracker.csv

🎯 ICP Lead Scoring Engine (RevOps)
Scraping thousands of leads is easy; knowing which 10 to call first is how operations drives revenue. I engineered an object-oriented Lead Scoring algorithm to automatically grade and prioritize prospects based on intent.

Features:

Dynamic Intent Dictionary: Awards points for high-intent B2B triggers (e.g., 'Founder', 'Raised Funding', 'Scaling') and penalizes negative-intent keywords.

Automated Tiering: Segments the outbound pipeline into Tier 1 (Hot), Tier 2 (Warm), and Tier 3 (Cold).

Stable Sorting: Exports a strictly prioritized v2_prioritized_leads.csv so sales teams always engage the highest-converting prospects first.

To run the engine:
python lead_scorer.py v2_ready_leads.csv

