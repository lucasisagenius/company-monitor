# Deployment Guide

This guide explains how to deploy and operate the Company Monitor Agent in production.

## Installation

### 1. Initial Setup

```bash
cd ~/company-monitor
chmod +x setup.sh
./setup.sh
```

### 2. Configuration

#### Email Setup (Required)

Update `.env` with your email provider:

**Gmail:**
```
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_SMTP_HOST=smtp.gmail.com
MAIL_SMTP_PORT=587
```

Instructions: https://support.google.com/accounts/answer/185833

**Outlook:**
```
MAIL_USERNAME=your-email@outlook.com
MAIL_PASSWORD=your_password
MAIL_SMTP_HOST=smtp.outlook.com
MAIL_SMTP_PORT=587
```

**Other providers:** Adjust SMTP_HOST and SMTP_PORT accordingly.

#### LLM Setup (Optional)

For AI-powered summarization, get an OpenRouter API key:

```
OPENROUTER_API_KEY=your_api_key
```

Get one at: https://openrouter.ai/

If not set, agent falls back to local extractive summarizer.

#### Company Configuration

Edit `config/companies.yaml`:

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

### 3. Test Configuration

Verify everything works:

```bash
source venv/bin/activate
python3 test_setup.py
```

## Deployment Options

### Option A: Cron Job (Recommended for regular checking)

Edit crontab:

```bash
crontab -e
```

Add entry (check 3 times daily at 8am, 2pm, 8pm):

```
0 8,14,20 * * * cd /Users/lucas/company-monitor && source venv/bin/activate && python3 scheduler.py --run-once
```

### Option B: Systemd Timer (Linux)

Create service file:

```bash
# /etc/systemd/system/company-monitor.service
[Unit]
Description=Company Monitor Agent
After=network.target

[Service]
Type=simple
User=lucas
WorkingDirectory=/Users/lucas/company-monitor
ExecStart=/Users/lucas/company-monitor/venv/bin/python3 scheduler.py --interval-hours 6
Restart=on-failure
RestartSec=300

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable company-monitor
sudo systemctl start company-monitor
sudo systemctl status company-monitor
```

### Option C: Launchd (macOS)

Create plist file:

```bash
# ~/Library/LaunchAgents/com.company-monitor.plist
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.company-monitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/lucas/company-monitor/venv/bin/python3</string>
        <string>/Users/lucas/company-monitor/scheduler.py</string>
        <string>--run-once</string>
    </array>
    <key>StartCalendarInterval</key>
    <array>
        <dict>
            <key>Hour</key>
            <integer>8</integer>
            <key>Minute</key>
            <integer>0</integer>
        </dict>
        <dict>
            <key>Hour</key>
            <integer>14</integer>
            <key>Minute</key>
            <integer>0</integer>
        </dict>
        <dict>
            <key>Hour</key>
            <integer>20</integer>
            <key>Minute</key>
            <integer>0</integer>
        </dict>
    </array>
    <key>StandardErrorPath</key>
    <string>/var/log/company-monitor.err</string>
    <key>StandardOutPath</key>
    <string>/var/log/company-monitor.log</string>
</dict>
</plist>
```

Load it:

```bash
launchctl load ~/Library/LaunchAgents/com.company-monitor.plist
launchctl list | grep company-monitor
```

### Option D: Docker (For containerized deployment)

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Create non-root user
RUN useradd -m monitor
USER monitor

CMD ["python3", "scheduler.py", "--run-once"]
```

Build and run:

```bash
docker build -t company-monitor .
docker run --env-file .env company-monitor
```

## Monitoring

### Check Logs

For cron jobs, logs are in syslog:

```bash
# macOS
log stream --predicate 'eventMessage contains "python"'

# Linux
journalctl -u company-monitor -f
```

### Database Status

```bash
# Check items tracked
sqlite3 monitor.db "SELECT COUNT(*) FROM seen_items;"

# View recent fetches
sqlite3 monitor.db "SELECT company_name, source_label, COUNT(*) FROM seen_items GROUP BY company_name, source_label ORDER BY company_name;"

# Check what was notified
sqlite3 monitor.db "SELECT COUNT(*) FROM seen_items WHERE notified = 1;"
```

### Manual Test Run

```bash
source venv/bin/activate
python3 scheduler.py --run-once 2>&1 | tee test_$(date +%Y%m%d_%H%M%S).log
```

## Troubleshooting

### No emails being sent

1. **Check .env**: Verify credentials are correct
   ```bash
   source .env && echo $MAIL_USERNAME
   ```

2. **Test SMTP connection**:
   ```bash
   python3 -c "
   import smtplib
   import os
   host = os.getenv('MAIL_SMTP_HOST')
   port = int(os.getenv('MAIL_SMTP_PORT', '587'))
   user = os.getenv('MAIL_USERNAME')
   pwd = os.getenv('MAIL_PASSWORD')

   try:
       with smtplib.SMTP(host, port) as s:
           s.starttls()
           s.login(user, pwd)
           print('✓ SMTP connection successful')
   except Exception as e:
       print(f'✗ SMTP error: {e}')
   "
   ```

3. **Check logs**: Look for SMTP errors in output

### No items fetched

1. **Run with verbose output**:
   ```bash
   python3 -c "
   import agent
   agent.run_once('config/companies.yaml')
   " 2>&1 | grep -i 'fetched\|failed\|error'
   ```

2. **Test individual adapters**:
   ```bash
   python3 -c "
   from adapters.news import NewsAdapter
   adapter = NewsAdapter({'query': 'test'})
   items = adapter.fetch()
   print(f'News items: {len(items)}')
   "
   ```

3. **Check network**: Some sources may be rate-limited or blocked

### Cron job not running

1. **Verify crontab entry**:
   ```bash
   crontab -l
   ```

2. **Check cron logs**:
   ```bash
   log stream --predicate 'process == "cron"'
   ```

3. **Test the command directly**:
   ```bash
   cd /Users/lucas/company-monitor && source venv/bin/activate && python3 scheduler.py --run-once
   ```

## Maintenance

### Weekly

- Check logs for errors
- Verify emails are being received
- Spot-check email content for accuracy

### Monthly

- Review `config/companies.yaml` for any broken sources
- Test adding new companies
- Check database size: `sqlite3 monitor.db ".size"`

### Quarterly

- Review SEC CIKs (in case of acquisitions/delisting)
- Test email with a company that has many recent updates
- Archive or clean up old database entries

### Archiving Old Data

```bash
# Backup database
cp monitor.db monitor.db.backup.$(date +%Y%m%d)

# Delete items older than 90 days
sqlite3 monitor.db "DELETE FROM seen_items WHERE fetched_at < date('now', '-90 days');"

# Verify
sqlite3 monitor.db "SELECT COUNT(*) FROM seen_items;"
```

## Performance Tuning

### Reduce Check Frequency

If getting too many emails:

```yaml
check_interval_hours: 12  # Change from 6 to 12
```

Or adjust cron:

```
0 8,20 * * *  # Instead of 8,14,20
```

### Reduce Sources

Remove slow or unreliable sources:

```yaml
companies:
  - name: "Company"
    sources:
      # - type: website  # Remove if slow
      - type: sec_edgar
      - type: news
```

### Disable LLM Summarization

Don't set `OPENROUTER_API_KEY` - agent will use fast local summarizer.

## Backup and Recovery

### Backup Configuration

```bash
# Backup daily
tar czf ~/backups/company-monitor-$(date +%Y%m%d).tar.gz \
  /Users/lucas/company-monitor/config/ \
  /Users/lucas/company-monitor/monitor.db \
  /Users/lucas/company-monitor/.env
```

### Restore Configuration

```bash
tar xzf ~/backups/company-monitor-YYYYMMDD.tar.gz -C /
```

### Reset Database

```bash
# Start over (lose all history)
rm monitor.db

# Agent will recreate it on next run
python3 scheduler.py --run-once
```

## Updating the Agent

```bash
# Backup current version
cp -r company-monitor company-monitor.backup

# Update from source
cd company-monitor
git pull  # If using git

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Test
python3 test_setup.py
```

## Support

For issues, check:
- TESTING.md - Debug individual components
- README.md - Basic usage
- Adapter source code for specific failures
