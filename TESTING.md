# Testing Guide

This document describes how to test the Company Monitor Agent.

## Quick Tests

### 1. Setup Test

Verify all components are working:

```bash
source venv/bin/activate
python3 test_setup.py
```

Expected output:
```
✓ All tests passed!
```

### 2. Individual Adapter Tests

#### SEC EDGAR Adapter

```bash
python3 -c "
from adapters.sec_edgar import SECEdgarAdapter

config = {
    'cik': '0001045810',  # Nvidia
    'form_types': ['8-K', '10-Q', '10-K'],
    'label': 'SEC Filings'
}

adapter = SECEdgarAdapter(config)
items = adapter.fetch()
print(f'✓ SEC adapter: {len(items)} items')
"
```

#### News Adapter

```bash
python3 -c "
from adapters.news import NewsAdapter

config = {
    'query': 'Microsoft Azure',
    'label': 'Financial News'
}

adapter = NewsAdapter(config)
items = adapter.fetch()
print(f'✓ News adapter: {len(items)} items')
"
```

#### Website Adapter

```bash
python3 -c "
from adapters.website import WebsiteAdapter

config = {
    'url': 'https://investor.microsoft.com/',
    'label': 'Investor Relations'
}

adapter = WebsiteAdapter(config)
items = adapter.fetch()
print(f'✓ Website adapter: {len(items)} items')
"
```

#### Social Adapter (Twitter)

```bash
python3 -c "
from adapters.social import SocialAdapter

config = {
    'platform': 'twitter',
    'handle': 'nvidia',
    'label': 'Twitter'
}

adapter = SocialAdapter(config)
items = adapter.fetch()
print(f'✓ Social adapter: {len(items)} items')
"
```

### 3. Database Test

```bash
python3 -c "
from core import filter_new_items, mark_seen, get_all_items

# Create test data
test_items = [
    {'url': 'https://example.com/1', 'title': 'Test 1'},
    {'url': 'https://example.com/2', 'title': 'Test 2'},
]

# Filter new (should be 2)
new = filter_new_items('TestCo', test_items)
print(f'✓ New items: {len(new)}')

# Mark seen
for item in new:
    mark_seen('TestCo', 'test', 'Test', item['url'], item['title'])

# Filter again (should be 0)
dups = filter_new_items('TestCo', test_items)
print(f'✓ Deduplication: {len(dups)}')

# Verify in DB
items = get_all_items('TestCo')
print(f'✓ DB tracking: {len(items)} items')
"
```

### 4. Summarizer Test

```bash
python3 -c "
from core.summarizer import simple_summarize

text = '''
This is a test article about company updates. It contains multiple sentences and paragraphs.
The company has announced new products and services that will benefit customers.
Investors should pay attention to these developments as they may impact stock performance.
The management team is confident about the future prospects of the company.
'''

summary = simple_summarize(text, max_words=20)
print(f'✓ Summarizer: {len(summary.split())} words')
print(f'  Summary: {summary}')
"
```

## End-to-End Test

### Setup Test Config

Create a minimal test config:

```yaml
# config/test.yaml
notification_email: "test@example.com"
check_interval_hours: 6

companies:
  - name: "Microsoft"
    ticker: "MSFT"
    sources:
      - type: "sec_edgar"
        cik: "0000789019"
        form_types: ["8-K"]
```

### Run Test (without email)

```bash
python3 -c "
import yaml
from adapters import ADAPTER_REGISTRY
from core import filter_new_items, mark_seen

# Load config
with open('config/test.yaml') as f:
    config = yaml.safe_load(f)

company = config['companies'][0]
print(f\"Testing: {company['name']}\")

for source in company['sources']:
    print(f\"  {source['type']}: \", end='')
    adapter_class = ADAPTER_REGISTRY[source['type']]
    adapter = adapter_class(source)
    items = adapter.fetch()
    print(f\"{len(items)} items\")

    # Test deduplication
    item_dicts = [item.to_dict() for item in items[:1]]
    new = filter_new_items(company['name'], item_dicts)
    mark_seen(company['name'], source['type'], '', item_dicts[0]['url'])
    dup = filter_new_items(company['name'], item_dicts)
    print(f\"    Dedup: {len(new)} new → {len(dup)} dups\")
"
```

### Full Run (dry-run, no email)

To test the full agent without email:

```bash
# Temporarily modify notifier.py to mock email:
# In core/notifier.py, change send_digest_email to just print items

python3 agent.py
```

Or edit `config/companies.yaml` temporarily and run:

```bash
python3 scheduler.py --run-once
```

## Database Inspection

```bash
# Count items by company
sqlite3 monitor.db "SELECT company_name, COUNT(*) FROM seen_items GROUP BY company_name;"

# List recent items
sqlite3 monitor.db "SELECT company_name, title, fetched_at FROM seen_items ORDER BY fetched_at DESC LIMIT 10;"

# Count by source
sqlite3 monitor.db "SELECT source_type, COUNT(*) FROM seen_items GROUP BY source_type;"
```

## Troubleshooting

### SEC EDGAR fails
- Verify CIK format (10 digits with leading zeros)
- Check: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=<your_cik>&type=&dateb=&owner=exclude&count=100

### Website adapter returns no items
- Website structure may have changed
- Check if site requires JavaScript (not supported)
- Try accessing URL directly in browser

### News adapter returns no items
- Google News may have rate-limited the IP
- Try a different query

### Social adapter fails
- Nitter instances may be down
- Try manually checking: https://nitter.net/nvidia

### Summarizer fails silently
- Falls back to local summarizer (no error)
- Check if OPENROUTER_API_KEY is set for LLM use

## Logs

The agent prints detailed logs. Save them:

```bash
python3 scheduler.py --run-once 2>&1 | tee monitoring_$(date +%Y%m%d_%H%M%S).log
```

## Performance Notes

- SEC EDGAR: ~1 second per request
- News: ~2-3 seconds per query
- Website: ~2-5 seconds (depends on site)
- Social: ~2-3 seconds per handle
- Summarization: ~1-2 seconds per item (local); ~3-5 seconds (OpenRouter)

Total for 1 company with 4 sources: ~20-30 seconds
Total for 3 companies with 4 sources each: ~1-2 minutes
