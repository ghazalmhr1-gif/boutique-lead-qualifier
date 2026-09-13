import os
import sys
import csv
import json
import argparse
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"

def check_website(url):
    if not url:
        return "missing", ""
    try:
        resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            return f"error_{resp.status_code}", ""
        text = BeautifulSoup(resp.text, "html.parser").get_text(separator=" ", strip=True)
        return "live", text[:1500]
    except requests.exceptions.RequestException:
        return "unreachable", ""

def name_appears(name, page_text):
    if not name or not page_text:
        return False
    key_words = [w.lower() for w in name.split() if len(w) > 2]
    if not key_words:
        return False
    lower_text = page_text.lower()
    return any(w in lower_text for w in key_words)

def ask_groq(row, website_status, name_match, page_snippet):
    if not GROQ_API_KEY:
        return "unknown", 0, "GROQ_API_KEY not set"

    prompt = f"""You are evaluating a business lead for a marketing/sales outreach list.

Business: {row['name']}
Category: {row.get('category', '')}
Address: {row.get('address', '')}
Phone listed: {'yes' if row.get('phone') else 'no'}
Google rating: {row.get('rating', 'N/A')} ({row.get('reviews', 'N/A')} reviews)
Website status: {website_status}
Business name found on website: {name_match}
Website content snippet: {page_snippet if page_snippet else 'N/A'}

Judge whether this is a good candidate for marketing/sales outreach right now.
Respond ONLY with strict JSON in this exact format, no other text:
{{"marketing_ready": "yes" or "no", "score": <integer 1-10>, "reason": "<one short sentence>"}}
"""

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 200,
    }
    try:
        resp = requests.post(GROQ_URL, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"].strip()
        start = content.find("{")
        end = content.rfind("}") + 1
        parsed = json.loads(content[start:end])
        return parsed.get("marketing_ready", "unknown"), parsed.get("score", 0), parsed.get("reason", "")
    except Exception as e:
        return "unknown", 0, f"AI check failed: {e}"

def process_row(row):
    website_status, page_snippet = check_website(row.get("website", ""))
    match = name_appears(row.get("name", ""), page_snippet)
    verdict, score, reason = ask_groq(row, website_status, match, page_snippet)
    row["website_status"] = website_status
    row["name_match"] = match
    row["marketing_ready"] = verdict
    row["ai_score"] = score
    row["ai_reason"] = reason
    return row

def main():
    parser = argparse.ArgumentParser(description="Qualify store leads for marketing/sales readiness.")
    parser.add_argument("--input", default="stores.csv", help="Input CSV (default: stores.csv)")
    parser.add_argument("--audit-out", default="lead_audit.csv", help="Full audit output CSV")
    parser.add_argument("--qualified-out", default="qualified_leads.csv", help="Filtered qualified leads CSV")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Input file not found: {args.input}")
        sys.exit(1)

    with open(args.input, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print("No rows found in input CSV.")
        sys.exit(0)

    print(f"Processing {len(rows)} stores...")
    processed = []
    for i, row in enumerate(rows, 1):
        print(f"  [{i}/{len(rows)}] {row.get('name', 'unknown')}")
        processed.append(process_row(row))

    audit_fields = list(processed[0].keys())
    with open(args.audit_out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=audit_fields)
        writer.writeheader()
        writer.writerows(processed)

    qualified = [r for r in processed if str(r.get("marketing_ready", "")).lower() == "yes"]
    with open(args.qualified_out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=audit_fields)
        writer.writeheader()
        writer.writerows(qualified)

    print(f"\nDone. {len(qualified)}/{len(processed)} stores qualified as marketing-ready.")
    print(f"Full audit: {args.audit_out}")
    print(f"Qualified leads: {args.qualified_out}")

if __name__ == "__main__":
    main()
