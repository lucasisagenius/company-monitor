"""SEC EDGAR adapter for fetching SEC filings."""
import requests
from typing import List
from .base import FetchedItem, BaseAdapter


class SECEdgarAdapter(BaseAdapter):
    """Adapter for SEC EDGAR filings."""

    def fetch(self) -> List[FetchedItem]:
        """Fetch SEC filings for company using data.sec.gov REST API."""
        cik = self.config.get('cik')
        form_types = self.config.get('form_types', ['8-K', '10-Q', '10-K'])
        label = self.config.get('label', 'SEC Filings')

        if not cik:
            print("CIK not provided for SEC adapter")
            return []

        # Format CIK with leading zeros (10 digits)
        cik_formatted = cik.lstrip('0').rjust(10, '0') if cik.startswith('0') else cik.zfill(10)

        try:
            # Fetch company submissions JSON from SEC
            url = f"https://data.sec.gov/submissions/CIK{cik_formatted}.json"
            headers = {
                'User-Agent': 'MonitorAgent contact@example.com',
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            items = []

            # Extract recent filings
            if 'filings' in data and 'recent' in data['filings']:
                recent = data['filings']['recent']

                for i in range(len(recent.get('form', []))):
                    form = recent['form'][i]

                    # Filter by form type
                    if form not in form_types:
                        continue

                    # Extract filing details
                    accession_number = recent['accessionNumber'][i]
                    filing_date = recent['filingDate'][i]
                    report_date = recent['reportDate'][i]

                    # Build filing URL
                    accession_formatted = accession_number.replace('-', '')
                    filing_url = (
                        f"https://www.sec.gov/cgi-bin/viewer?"
                        f"action=view&cik={cik_formatted}&accession_number={accession_number}&"
                        f"xbrl_type=v"
                    )

                    title = f"{form} - {report_date}"

                    items.append(FetchedItem(
                        url=filing_url,
                        title=title,
                        published_date=filing_date,
                        source_label=label
                    ))

            return items

        except Exception as e:
            print(f"Failed to fetch SEC filings for CIK {cik}: {e}")
            return []
