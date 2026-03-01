"""News adapter for Google News RSS."""
import requests
from typing import List
from .base import FetchedItem, BaseAdapter
from .website import parse_rss_feed, BROWSER_HEADERS


class NewsAdapter(BaseAdapter):
    """Adapter for fetching financial news via Google News RSS."""

    def fetch(self) -> List[FetchedItem]:
        """Fetch news items from Google News RSS."""
        query = self.config.get('query')
        label = self.config.get('label', 'Financial News')

        if not query:
            print("Query not provided for news adapter")
            return []

        try:
            # Build Google News RSS URL
            url = (
                f"https://news.google.com/rss/search?"
                f"q={query.replace(' ', '%20')}&"
                f"hl=en-US&gl=US&ceid=US:en"
            )

            response = requests.get(url, headers=BROWSER_HEADERS, timeout=10)
            response.raise_for_status()

            # Parse RSS feed
            rss_items = parse_rss_feed(response.content, url)

            items = []
            for rss_item in rss_items:
                items.append(FetchedItem(
                    url=rss_item['url'],
                    title=rss_item.get('title', 'Untitled'),
                    published_date=rss_item.get('published_date'),
                    source_label=label
                ))

            return items

        except Exception as e:
            print(f"Failed to fetch news for query '{query}': {e}")
            return []
