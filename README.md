# Company Website Update Monitor Agent

An autonomous agent that monitors updates from invested companies across multiple sources (official websites, SEC filings, financial news, social media) and sends email digests with AI-generated summaries.

## Setup

### 1. Install Dependencies

```bash
cd ~/company-monitor
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example `.env` file and fill in your credentials:

```bash
cp .env.example .env
# Edit .env with your:
# - OpenRouter API key (for LLM summarization)
# - Email credentials (Gmail or other SMTP provider)
```

### 3. Configure Companies

Edit `config/companies.yaml` to add/modify companies you want to monitor:

```yaml
notification_email: "your-email@example.com"
check_interval_hours: 6

companies:
  - name: "Company Name"
    ticker: "TICKER"
    sources:
      - type: website
        url: "https://investors.example.com/news"
        label: "Investor Relations"
      - type: sec_edgar
        cik: "0001234567"
        form_types: ["8-K", "10-Q", "10-K"]
      - type: news
        query: "Company Name product"
        label: "Financial News"
      - type: social
        platform: twitter
        handle: "company_handle"
        label: "Twitter"
```

## Usage

### Run Once (for Cron Jobs)

```bash
python scheduler.py --run-once
```

This fetches updates once and exits. Perfect for cron jobs:

```bash
# Check every 6 hours (0 8, 14, 20 = 8am, 2pm, 8pm)
0 8,14,20 * * * cd ~/company-monitor && /usr/bin/python3 scheduler.py --run-once
```

### Run Continuously

```bash
# Check every 6 hours (default)
python scheduler.py --interval-hours 6

# Or with custom interval
python scheduler.py --interval-hours 4
```

Press Ctrl+C to stop.

## How It Works

1. **Fetch**: For each company and source, the appropriate adapter fetches items
   - Website: Searches for RSS feeds, API endpoints, and news links
   - SEC EDGAR: Uses SEC's free REST API for filings
   - News: Google News RSS feed
   - Social: Twitter via Nitter RSS

2. **Deduplicate**: Items already seen are filtered out using SQLite database

3. **Summarize**: New items are summarized using OpenRouter API (Mistral 7B)
   - Falls back to local extractive summarizer if API unavailable
   - PDF content is automatically extracted and summarized

4. **Notify**: Email digest sent with grouped items, summaries, and links

5. **Track**: Items marked as seen/notified in database to prevent duplicates

## Database

SQLite database at `monitor.db` tracks:
- All fetched items (URL, title, date, source)
- Which items have been notified

View items:
```bash
sqlite3 monitor.db "SELECT company_name, source_label, title FROM seen_items LIMIT 20;"
```

## Configuration Details

### Supported Source Types

- **website**: Generic website + RSS scraper
- **sec_edgar**: SEC EDGAR filings (requires CIK)
- **news**: Google News RSS (requires search query)
- **social**: Twitter via Nitter RSS; LinkedIn stub (no free API)

### Email Providers

**Gmail (SMTP):**
```
MAIL_SMTP_HOST=smtp.gmail.com
MAIL_SMTP_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your_app_password  # Not your regular password!
```

See: https://support.google.com/accounts/answer/185833

**Outlook:**
```
MAIL_SMTP_HOST=smtp.outlook.com
MAIL_SMTP_PORT=587
MAIL_USERNAME=your-email@outlook.com
MAIL_PASSWORD=your_password
```

## Troubleshooting

### Email not sending
1. Verify credentials in `.env`
2. Check SMTP host/port for your provider
3. Gmail users: Use an [App Password](https://support.google.com/accounts/answer/185833), not your regular password

### No items fetched
1. Check network connectivity
2. Verify URLs in config are correct
3. Check adapter logs for specific failures
4. Website adapters may fail due to site changes (no guaranteed stability)

### Summaries not generated
1. Verify `OPENROUTER_API_KEY` is set
2. Check OpenRouter account has credits
3. Agent falls back to local summarizer if API unavailable

## Reused Components

This agent reuses functions from `stock-monitor-app`:
- Website scraping and RSS parsing
- Date extraction from various formats
- PDF text extraction
- Fallback summarization logic
- Email notification infrastructure

## License

See parent directory.
