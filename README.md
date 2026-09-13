# Boutique Lead Qualifier

An AI agent that takes a list of businesses (from the Toronto Boutique Finder project) and judges whether each one is ready for marketing/sales outreach — checking that their website is live, that it actually mentions the business, and then having an LLM weigh all the signals to produce a verdict and a reason.

## Why I built this
Built as the next step after finding leads: raw contact data isn't useful for outreach until you know it's current and worth pursuing. This automates that qualification step, combining deterministic checks (is the site up? does the name match?) with LLM judgment (is this a good outreach candidate?) — the kind of AI-assisted GTM workflow analyst roles are starting to expect.

## How it works
1. Reads a CSV of stores (name, address, phone, website, rating, reviews, category)
2. For each store: checks if the website actually loads, and whether the business name appears on the page
3. Sends all signals (rating, reviews, phone presence, website status, name match, a snippet of page content) to an LLM (via Groq's free API) which returns a marketing-readiness verdict, a 1-10 score, and a one-line reason
4. Outputs two files: a full audit CSV (every store + every signal + verdict) and a filtered CSV of only the stores that qualified — ready to hand to a sales team

## How to run it
1. Get a free API key at [console.groq.com](https://console.groq.com)
2. Create a `.env` file with `GROQ_API_KEY=your_key_here`
3. Install dependencies: `pip install requests python-dotenv beautifulsoup4`
4. Put a CSV of stores at `stores.csv` (matching the format produced by the Toronto Boutique Finder tool)
5. Run: `python lead_qualifier.py`
6. Check `lead_audit.csv` (everything, with reasoning) and `qualified_leads.csv` (only the qualified ones)

## Known limitations
- Some websites block automated requests (bot protection), which shows up as a failed check rather than a false pass — intentional, since an unverifiable site shouldn't be marked "ready."
- The AI's judgment is a heuristic, not a guarantee — it's meant to prioritize a lead list for a human to review, not replace that review entirely.

## Related projects
This is the third step in a small pipeline of tools:
1. [research-report-tool](https://github.com/ghazalmhr1-gif/research-report-tool) — topic-to-report research automation
2. [toronto-boutique-finder](https://github.com/ghazalmhr1-gif/toronto-boutique-finder) — finds and enriches local business leads
3. **boutique-lead-qualifier** (this repo) — verifies and scores those leads for outreach readiness
