"""Core modules for monitoring."""
from .db import (
    get_db_connection,
    filter_new_items,
    filter_by_date,
    mark_seen,
    mark_notified,
    get_all_items,
)
from .summarizer import get_summary, simple_summarize, summarize_with_openrouter
from .notifier import send_digest_email


__all__ = [
    'get_db_connection',
    'filter_new_items',
    'filter_by_date',
    'mark_seen',
    'mark_notified',
    'get_all_items',
    'get_summary',
    'simple_summarize',
    'summarize_with_openrouter',
    'send_digest_email',
]
