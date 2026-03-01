# Quick Start Guide

Get the Company Monitor Agent running in 5 minutes.

## What You Need

- OpenRouter API key (free with credits): https://openrouter.ai/
- Email account + SMTP password (Gmail App Password recommended)
- Python 3.8+

## Step 1: Activate Environment

```bash
cd ~/company-monitor
source venv/bin/activate
```

## Step 2: Configure `.env`

Edit `.env` and add your credentials:

```bash
nano .env
```

For Gmail:
```
OPENROUTER_API_KEY=sk-or-v1-...
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_SMTP_HOST=smtp.gmail.com
MAIL_SMTP_PORT=587
```

**Getting Gmail App Password:**
1. Go to https://myaccount.google.com/apppasswords
2. Select Mail and Windows Computer
3. Copy the 16-character password
4. Use this as `MAIL_PASSWORD` (ignore spaces)

## Step 3: Configure Companies

Edit `config/companies.yaml`:

```bash
nano config/companies.yaml
```

Update:
- `notification_email` - Your email address
- Companies to monitor (or keep the defaults)

## Step 4: Test

```bash
python3 scheduler.py --run-once
```

You should see:
```
============================================================
Processing: Company Name
============================================================
Fetching from sec_edgar: SEC Filings
Fetched XX items
...
Email sent successfully to your-email@gmail.com
```

Check your email for the digest!

## Step 5: Deploy

Choose one option:

### Option A: Cron (macOS/Linux)

```bash
crontab -e
```

Add:
```
0 8,14,20 * * * cd /Users/lucas/company-monitor && source venv/bin/activate && python3 scheduler.py --run-once
```

This runs at 8am, 2pm, and 8pm daily.

### Option B: Continuous (Background)

```bash
python3 scheduler.py --interval-hours 6 &
```

### Option C: More Options

See DEPLOYMENT.md for Systemd, Launchd, Docker, etc.

## Troubleshooting

### "No items fetched"

Website scrapers are fragile. SEC EDGAR and News usually work:

```yaml
sources:
  - type: sec_edgar
    cik: "0001234567"  # Get CIK from https://www.sec.gov/cgi-bin/browse-edgar
  - type: news
    query: "Company Name"
```

### "Email not sending"

Test your SMTP credentials:

```bash
python3 -c "
import smtplib, os
s = smtplib.SMTP(os.getenv('MAIL_SMTP_HOST'), int(os.getenv('MAIL_SMTP_PORT')))
s.starttls()
s.login(os.getenv('MAIL_USERNAME'), os.getenv('MAIL_PASSWORD'))
print('✓ SMTP OK')
s.quit()
"
```

### "404 Not Found" errors

Website URLs change. Use SEC EDGAR + News instead (more reliable):

```yaml
# Good sources:
- type: sec_edgar
- type: news

# Fragile (may break):
- type: website  # Avoid if possible
```

## Useful Commands

```bash
# Activate environment
source venv/bin/activate

# Run once
python3 scheduler.py --run-once

# Run continuously (Ctrl+C to stop)
python3 scheduler.py --interval-hours 6

# Check database
sqlite3 monitor.db "SELECT company_name, COUNT(*) FROM seen_items GROUP BY company_name;"

# View recent items
sqlite3 monitor.db "SELECT company_name, title, fetched_at FROM seen_items ORDER BY fetched_at DESC LIMIT 10;"

# Clear database
rm monitor.db

# Reset config
cp config/companies.yaml.bak config/companies.yaml
```

## Next Steps

1. **Add more companies** - Edit `config/companies.yaml`
2. **Adjust timing** - Change `check_interval_hours` or cron schedule
3. **Reduce noise** - Remove slow/unreliable sources
4. **Enable LLM** - Set `OPENROUTER_API_KEY` for AI summaries (optional)

## Getting Help

- See **README.md** - Full documentation
- See **TESTING.md** - Debug individual adapters
- See **DEPLOYMENT.md** - Production setup
- See **IMPLEMENTATION_SUMMARY.md** - Technical details

## Key URLs

- OpenRouter: https://openrouter.ai/
- Gmail App Password: https://myaccount.google.com/apppasswords
- SEC EDGAR: https://www.sec.gov/cgi-bin/browse-edgar
- Nitter (Twitter): https://nitter.net/
- Google News: https://news.google.com/

---

**That's it!** Your agent is now monitoring company updates and sending email digests.
