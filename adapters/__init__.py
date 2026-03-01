"""Adapters for different source types."""
from .base import FetchedItem, BaseAdapter
from .website import WebsiteAdapter
from .sec_edgar import SECEdgarAdapter
from .news import NewsAdapter
from .social import SocialAdapter


ADAPTER_REGISTRY = {
    'website': WebsiteAdapter,
    'sec_edgar': SECEdgarAdapter,
    'news': NewsAdapter,
    'social': SocialAdapter,
}


__all__ = [
    'FetchedItem',
    'BaseAdapter',
    'ADAPTER_REGISTRY',
    'WebsiteAdapter',
    'SECEdgarAdapter',
    'NewsAdapter',
    'SocialAdapter',
]
