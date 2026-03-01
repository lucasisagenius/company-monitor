"""Social media adapter for Twitter and LinkedIn."""
import requests
from typing import List
from .base import FetchedItem, BaseAdapter
from .website import parse_rss_feed, BROWSER_HEADERS


NITTER_INSTANCES = [
    'https://nitter.net',
    'https://nitter.privacydev.net',
    'https://nitter.poast.org',
    'https://nitter.1d4.us',
    'https://nitter.unixfox.eu',
    'https://nitter.namazso.eu',
    'https://nitter.moomoo.me',
]


class SocialAdapter(BaseAdapter):
    """Adapter for social media sources (Twitter via Nitter, LinkedIn)."""

    def fetch(self) -> List[FetchedItem]:
        """Fetch items from social media."""
        platform = self.config.get('platform', '').lower()
        label = self.config.get('label', 'Social Media')

        if platform == 'twitter':
            return self._fetch_twitter(label)
        elif platform == 'linkedin':
            return self._fetch_linkedin(label)
        else:
            print(f"Unknown social platform: {platform}")
            return []

    def _fetch_twitter(self, label: str) -> List[FetchedItem]:
        """Fetch tweets via Nitter RSS.

        Note: Nitter is a free Twitter proxy and public instances are often unreliable.
        This is not critical - if Twitter fetching fails, the rest of the agent continues.
        """
        handle = self.config.get('handle')
        if not handle:
            print("Handle not provided for Twitter")
            return []

        items = []
        last_error = None

        for i, nitter_url in enumerate(NITTER_INSTANCES):
            try:
                rss_url = f"{nitter_url}/{handle}/rss"
                response = requests.get(
                    rss_url,
                    headers=BROWSER_HEADERS,
                    timeout=5  # Shorter timeout for Nitter
                )

                if response.status_code == 200:
                    rss_items = parse_rss_feed(response.content, rss_url)
                    for rss_item in rss_items:
                        items.append(FetchedItem(
                            url=rss_item['url'],
                            title=rss_item.get('title', 'Tweet'),
                            published_date=rss_item.get('published_date'),
                            source_label=f"{label} (@{handle})"
                        ))

                    if items:
                        print(f"  ✓ Fetched {len(items)} tweets from @{handle}")
                        return items

            except requests.exceptions.Timeout:
                last_error = "timeout"
                continue
            except requests.exceptions.ConnectionError:
                last_error = "connection refused"
                continue
            except Exception as e:
                last_error = type(e).__name__
                continue

        # If we get here, all Nitter instances failed (expected for public instances)
        if last_error:
            print(f"  ⚠ Twitter unavailable (@{handle}) - {last_error}")
            print(f"    (Nitter instances are often down - this is OK, continuing...)")
        else:
            print(f"  ⚠ Twitter data unavailable for @{handle}")

        return items

    def _fetch_linkedin(self, label: str) -> List[FetchedItem]:
        """Fetch LinkedIn posts (stub - no free API available)."""
        print("LinkedIn scraping not available (no free API)")
        return []
