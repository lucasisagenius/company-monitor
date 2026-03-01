"""Website and RSS feed adapter."""
import re
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from typing import List, Optional
from .base import FetchedItem, BaseAdapter


BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0'
}


def get_content_with_requests(url: str) -> Optional[BeautifulSoup]:
    """Fetch page content using requests."""
    try:
        response = requests.get(url, headers=BROWSER_HEADERS, timeout=30, allow_redirects=True)
        response.raise_for_status()

        if len(response.content) < 1000:
            return None

        return BeautifulSoup(response.content, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Request failed {url}: {e}")
        return None


def normalize_url(href: str, base_url: str) -> Optional[str]:
    """Normalize URL to avoid duplicates and invalid links."""
    if not href:
        return None

    # If already a full URL, return as-is
    if href.startswith('http'):
        return href

    # Remove anchors and query params
    href = href.split('#')[0].split('?')[0]

    # Handle relative paths
    if href.startswith('/'):
        # Absolute path from domain root
        from urllib.parse import urlparse
        parsed_base = urlparse(base_url)
        return f"{parsed_base.scheme}://{parsed_base.netloc}{href}"
    else:
        # Relative path
        base_parts = base_url.rstrip('/').split('/')
        href_parts = href.lstrip('/').split('/')

        # Avoid duplicate path segments
        if len(base_parts) > 3:
            last_base_part = base_parts[-1]
            if href_parts and href_parts[0] == last_base_part:
                base_parts = base_parts[:-1]

        # Build new URL
        result_url = '/'.join(base_parts) + '/' + '/'.join(href_parts)

        # Clean up duplicate slashes
        result_url = re.sub(r'/+', '/', result_url)

        return result_url


def is_valid_url(url: str) -> bool:
    """Validate URL format."""
    if not url:
        return False

    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False
        path = parsed.path
    except:
        return False

    # Check for invalid patterns in path only (not scheme)
    invalid_patterns = [
        r'//+',  # Multiple consecutive slashes
        r'/[^/]+/[^/]+/[^/]+/[^/]+/[^/]+/[^/]+',  # Too deep path
        r'\.\./',  # Relative path indicators
    ]

    for pattern in invalid_patterns:
        if re.search(pattern, path):
            return False

    # Check path depth
    path_parts = path.split('/') if path else []
    if len(path_parts) > 6:  # More realistic limit
        return False

    # Check for repeated path segments
    seen_parts = set()
    for part in path_parts:
        if part in seen_parts and part:
            return False
        seen_parts.add(part)

    return True


def try_api_endpoints(base_url: str) -> List[dict]:
    """Try common API endpoints for fetching news/announcements."""
    api_endpoints = [
        '/api/news',
        '/api/announcements',
        '/api/press-releases',
        '/api/ir/news',
        '/api/investor/news',
        '/news/api',
        '/announcements/api'
    ]

    news_items = []

    for endpoint in api_endpoints:
        try:
            api_url = base_url.rstrip('/') + endpoint
            response = requests.get(api_url, headers=BROWSER_HEADERS, timeout=10)
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        for item in data:
                            if 'title' in item and 'url' in item:
                                news_items.append({
                                    'url': item['url'],
                                    'title': item['title'],
                                    'published_date': item.get('date') or item.get('published_date')
                                })
                    elif isinstance(data, dict) and 'data' in data:
                        for item in data['data']:
                            if 'title' in item and 'url' in item:
                                news_items.append({
                                    'url': item['url'],
                                    'title': item['title'],
                                    'published_date': item.get('date') or item.get('published_date')
                                })
                except:
                    pass
        except:
            continue

    return news_items


def parse_rss_date(date_str: str) -> Optional[datetime]:
    """Parse RSS date formats."""
    try:
        formats = [
            '%a, %d %b %Y %H:%M:%S %z',
            '%a, %d %b %Y %H:%M:%S %Z',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue

        return None
    except:
        return None


def parse_rss_feed(content: bytes, feed_url: str) -> List[dict]:
    """Parse RSS/Atom feed content."""
    try:
        soup = BeautifulSoup(content, 'xml')

        items = soup.find_all('item')
        if not items:
            items = soup.find_all('entry')  # Atom format

        news_items = []
        seven_days_ago = datetime.utcnow() - timedelta(days=7)

        for item in items:
            try:
                # Extract title
                title_elem = item.find('title')
                title = title_elem.get_text(strip=True) if title_elem else ''

                # Extract link
                link_elem = item.find('link')
                link = link_elem.get_text(strip=True) if link_elem else ''
                if not link and link_elem:
                    link = link_elem.get('href', '')

                # Extract date
                date_elem = item.find('pubDate') or item.find('published') or item.find('date')
                published_date = None
                if date_elem:
                    date_str = date_elem.get_text(strip=True)
                    published_date = parse_rss_date(date_str)

                if title and link:
                    if published_date is None or published_date >= seven_days_ago:
                        news_items.append({
                            'url': normalize_url(link, feed_url),
                            'title': title,
                            'published_date': published_date.isoformat() if published_date else None
                        })
            except Exception as e:
                print(f"Failed to parse RSS item: {e}")
                continue

        return news_items
    except Exception as e:
        print(f"Failed to parse RSS: {e}")
        return []


def find_rss_feeds(soup: BeautifulSoup, base_url: str) -> List[dict]:
    """Find and parse RSS feeds from a webpage."""
    news_items = []
    rss_links = []

    # Find RSS feed links in link tags
    for link in soup.find_all('link'):
        rel = link.get('rel', [])
        if isinstance(rel, list):
            rel = ' '.join(rel)
        rel = rel.lower()

        if 'rss' in rel or 'feed' in rel or 'alternate' in rel:
            href = link.get('href')
            if href:
                rss_links.append(normalize_url(href, base_url))

    # Find RSS feed links in anchor tags
    for link in soup.find_all('a', href=True):
        href = link.get('href', '').lower()
        text = link.get_text(strip=True).lower()

        if 'rss' in href or 'feed' in href or 'rss' in text or 'feed' in text:
            rss_links.append(normalize_url(link.get('href'), base_url))

    # Try common RSS paths
    common_rss_paths = [
        '/rss', '/feed', '/rss.xml', '/feed.xml', '/news/rss', '/news/feed',
        '/press/rss', '/press/feed', '/ir/rss', '/ir/feed'
    ]

    for path in common_rss_paths:
        rss_links.append(base_url.rstrip('/') + path)

    # Deduplicate
    rss_links = list(set([u for u in rss_links if u]))

    # Parse feeds
    for rss_url in rss_links[:3]:  # Limit to first 3
        try:
            if not is_valid_url(rss_url):
                continue

            print(f"Trying to parse RSS: {rss_url}")
            response = requests.get(rss_url, headers=BROWSER_HEADERS, timeout=10)
            if response.status_code == 200:
                rss_news = parse_rss_feed(response.content, rss_url)
                if rss_news:
                    print(f"Parsed {len(rss_news)} items from RSS {rss_url}")
                    news_items.extend(rss_news)
        except Exception as e:
            print(f"Failed to parse RSS {rss_url}: {e}")
            continue

    return news_items


def extract_date_from_element(link_element, soup: BeautifulSoup) -> Optional[datetime]:
    """Extract date from a link element or surrounding elements.

    Uses 4 strategies:
    1. Extract from link text
    2. Extract from parent element
    3. Search nearby date elements
    4. Extract from URL
    """
    try:
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # 2024-01-15
            r'(\d{4}/\d{2}/\d{2})',  # 2024/01/15
            r'(\d{2}-\d{2}-\d{4})',  # 01-15-2024
            r'(\d{2}/\d{2}/\d{4})',  # 01/15/2024
            r'(\w+ \d{1,2},? \d{4})',  # January 15, 2024
            r'(\d{1,2} \w+ \d{4})',  # 15 January 2024
            r'(\d{2}/\d{2}/\d{2})',  # 01/15/24
            r'(\d{2}-\d{2}-\d{2})',  # 01-15-24
            r'(\d{1,2}/\d{1,2}/\d{4})',  # 1/15/2024
            r'(\d{1,2}-\d{1,2}-\d{4})',  # 1-15-2024
        ]

        month_map = {
            'january': '01', 'jan': '01',
            'february': '02', 'feb': '02',
            'march': '03', 'mar': '03',
            'april': '04', 'apr': '04',
            'may': '05',
            'june': '06', 'jun': '06',
            'july': '07', 'jul': '07',
            'august': '08', 'aug': '08',
            'september': '09', 'sep': '09',
            'october': '10', 'oct': '10',
            'november': '11', 'nov': '11',
            'december': '12', 'dec': '12'
        }

        def validate_date(year: str, month: str, day: str) -> bool:
            """Validate date reasonableness."""
            try:
                year, month, day = int(year), int(month), int(day)
                if year < 1990 or year > 2030:
                    return False
                if month < 1 or month > 12:
                    return False
                if day < 1 or day > 31:
                    return False
                datetime(year, month, day)
                return True
            except:
                return False

        def parse_date_string(date_str: str) -> Optional[datetime]:
            """Parse date string with multiple formats."""
            try:
                for month_name, month_num in month_map.items():
                    if month_name in date_str.lower():
                        date_str = re.sub(r'\b' + month_name + r'\b', month_num, date_str.lower())
                        break

                formats = [
                    '%Y-%m-%d', '%Y/%m/%d', '%m-%d-%Y', '%m/%d/%Y',
                    '%d %m %Y', '%m %d %Y', '%d/%m/%y', '%m/%d/%y',
                    '%d/%m/%Y', '%d-%m-%Y'
                ]

                for fmt in formats:
                    try:
                        parsed = datetime.strptime(date_str, fmt)
                        if 1990 <= parsed.year <= 2030:
                            return parsed
                    except:
                        continue

                return None
            except:
                return None

        # Strategy 1: Extract from link text
        link_text = link_element.get_text(strip=True)
        for pattern in date_patterns:
            match = re.search(pattern, link_text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                parsed_date = parse_date_string(date_str)
                if parsed_date:
                    return parsed_date

        # Strategy 2: Extract from parent element
        parent = link_element.parent
        if parent:
            parent_text = parent.get_text(strip=True)
            for pattern in date_patterns:
                match = re.search(pattern, parent_text, re.IGNORECASE)
                if match:
                    date_str = match.group(1)
                    parsed_date = parse_date_string(date_str)
                    if parsed_date:
                        return parsed_date

        # Strategy 3: Search nearby date elements
        nearby_selectors = [
            '.date', '.time', '.publish-date', '.news-date', '.post-date',
            '.article-date', '.entry-date', '.meta-date', '.timestamp',
            '[class*="date"]', '[class*="time"]', '[class*="publish"]',
            'time', '[datetime]', 'span[class*="date"]', 'div[class*="date"]'
        ]

        for selector in nearby_selectors:
            nearby_date = link_element.find_previous_sibling(selector)
            if not nearby_date:
                nearby_date = link_element.find_next_sibling(selector)
            if not nearby_date and parent:
                nearby_date = parent.find(selector)

            if nearby_date:
                datetime_attr = nearby_date.get('datetime')
                if datetime_attr:
                    try:
                        parsed_date = datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                        if 1990 <= parsed_date.year <= 2030:
                            return parsed_date
                    except:
                        pass

                date_text = nearby_date.get_text(strip=True)
                for pattern in date_patterns:
                    match = re.search(pattern, date_text, re.IGNORECASE)
                    if match:
                        date_str = match.group(1)
                        parsed_date = parse_date_string(date_str)
                        if parsed_date:
                            return parsed_date

        # Strategy 4: Extract from URL
        href = link_element.get('href', '')
        if href:
            url_date_patterns = [
                r'/(\d{4})/(\d{2})/(\d{2})/',
                r'(\d{4})-(\d{2})-(\d{2})',
                r'(\d{4})_(\d{2})_(\d{2})',
                r'/(\d{4})/(\d{2})/(\d{2})$',
                r'date=(\d{4})-(\d{2})-(\d{2})',
                r'publish=(\d{4})-(\d{2})-(\d{2})',
            ]

            for pattern in url_date_patterns:
                match = re.search(pattern, href)
                if match:
                    try:
                        year, month, day = match.groups()
                        if validate_date(year, month, day):
                            return datetime(int(year), int(month), int(day))
                    except:
                        continue

        return None

    except Exception as e:
        print(f"Date extraction failed: {e}")
        return None


class WebsiteAdapter(BaseAdapter):
    """Adapter for website news/announcements."""

    def fetch(self) -> List[FetchedItem]:
        """Fetch items from website."""
        url = self.config.get('url')
        label = self.config.get('label', 'Website')

        if not url or not is_valid_url(url):
            print(f"Invalid URL: {url}")
            return []

        items = []

        # Try to fetch main page
        soup = get_content_with_requests(url)
        if not soup:
            print(f"Failed to fetch {url}")
            return []

        # Try API endpoints first
        base_domain = '/'.join(url.split('/')[:3])
        api_items = try_api_endpoints(base_domain)
        for api_item in api_items:
            items.append(FetchedItem(
                url=api_item['url'],
                title=api_item.get('title', 'Untitled'),
                published_date=api_item.get('published_date'),
                source_label=label
            ))

        # Try RSS feeds
        rss_items = find_rss_feeds(soup, url)
        for rss_item in rss_items:
            items.append(FetchedItem(
                url=rss_item['url'],
                title=rss_item.get('title', 'Untitled'),
                published_date=rss_item.get('published_date'),
                source_label=label
            ))

        # Try to find news links on the page
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '')
            text = link.get_text(strip=True)

            # Look for news-related links
            if any(keyword in href.lower() or keyword in text.lower()
                   for keyword in ['news', 'announcement', 'press', 'release', 'update']):

                normalized_url = normalize_url(href, url)
                if normalized_url and is_valid_url(normalized_url):
                    # Try to extract date
                    pub_date = extract_date_from_element(link, soup)

                    items.append(FetchedItem(
                        url=normalized_url,
                        title=text or 'Untitled',
                        published_date=pub_date.isoformat() if pub_date else None,
                        source_label=label
                    ))

        return items
