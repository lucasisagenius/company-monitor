"""SQLite database module for tracking seen items."""
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional


DB_PATH = Path.home() / "company-monitor" / "monitor.db"


def get_db_connection() -> sqlite3.Connection:
    """Get a database connection and initialize schema if needed."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    init_schema(conn)
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    """Initialize database schema."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS seen_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            source_type TEXT NOT NULL,
            source_label TEXT,
            url TEXT NOT NULL,
            title TEXT,
            summary TEXT,
            published_date TEXT,
            fetched_at TEXT NOT NULL,
            notified INTEGER DEFAULT 0,
            UNIQUE(company_name, url)
        )
    """)
    conn.commit()


def filter_new_items(company_name: str, items: List[dict]) -> List[dict]:
    """Filter out items already seen in database.

    Args:
        company_name: Name of the company
        items: List of items with 'url' key

    Returns:
        List of items not yet in database
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    new_items = []
    for item in items:
        url = item.get("url")
        if not url:
            continue

        cursor.execute(
            "SELECT id FROM seen_items WHERE company_name = ? AND url = ?",
            (company_name, url)
        )
        if cursor.fetchone() is None:
            new_items.append(item)

    conn.close()
    return new_items


def mark_seen(company_name: str, source_type: str, source_label: Optional[str],
              url: str, title: Optional[str] = None,
              published_date: Optional[str] = None) -> None:
    """Mark an item as seen in the database.

    Args:
        company_name: Name of the company
        source_type: Type of source (website, sec_edgar, news, social)
        source_label: Human-readable label for the source
        url: URL of the item
        title: Title of the item
        published_date: Publication date (ISO format)
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    now = datetime.utcnow().isoformat()

    try:
        cursor.execute("""
            INSERT INTO seen_items
            (company_name, source_type, source_label, url, title, published_date, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (company_name, source_type, source_label, url, title, published_date, now))
        conn.commit()
    except sqlite3.IntegrityError:
        # Item already exists, that's okay
        pass
    finally:
        conn.close()


def mark_notified(company_name: str, urls: List[str]) -> None:
    """Mark items as notified (email sent).

    Args:
        company_name: Name of the company
        urls: List of item URLs
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    for url in urls:
        cursor.execute(
            "UPDATE seen_items SET notified = 1 WHERE company_name = ? AND url = ?",
            (company_name, url)
        )

    conn.commit()
    conn.close()


def get_all_items(company_name: Optional[str] = None) -> List[dict]:
    """Get all items from database, optionally filtered by company.

    Args:
        company_name: Optional company name filter

    Returns:
        List of item dictionaries
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    if company_name:
        cursor.execute(
            "SELECT * FROM seen_items WHERE company_name = ? ORDER BY fetched_at DESC",
            (company_name,)
        )
    else:
        cursor.execute("SELECT * FROM seen_items ORDER BY fetched_at DESC")

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def filter_by_date(items: List[dict], max_age_days: int = 7) -> List[dict]:
    """Filter items to only include those published within max_age_days.

    Args:
        items: List of items with 'published_date' field
        max_age_days: Maximum age in days (default: 7)

    Returns:
        List of items published within the date range
    """
    cutoff_date = datetime.utcnow() - \
        __import__('datetime').timedelta(days=max_age_days)

    filtered = []
    for item in items:
        pub_date_str = item.get('published_date')
        if not pub_date_str:
            # If no date, include it (be conservative)
            filtered.append(item)
            continue

        try:
            # Try to parse the date
            if pub_date_str.endswith('Z'):
                pub_date = datetime.fromisoformat(
                    pub_date_str.replace('Z', '+00:00'))
            else:
                # Try various formats
                try:
                    pub_date = datetime.fromisoformat(pub_date_str)
                except:
                    pub_date = datetime.strptime(
                        pub_date_str[:10], '%Y-%m-%d')

            # Include if within date range
            if pub_date >= cutoff_date:
                filtered.append(item)

        except Exception as e:
            # If we can't parse the date, include it (be conservative)
            filtered.append(item)

    return filtered
