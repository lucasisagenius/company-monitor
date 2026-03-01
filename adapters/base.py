"""Base adapter and FetchedItem dataclass."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class FetchedItem:
    """Represents a fetched item from a source."""
    url: str
    title: str
    published_date: Optional[str] = None
    description: Optional[str] = None
    source_label: Optional[str] = None
    fetched_at: str = None

    def __post_init__(self):
        if self.fetched_at is None:
            self.fetched_at = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "url": self.url,
            "title": self.title,
            "published_date": self.published_date,
            "description": self.description,
            "source_label": self.source_label,
            "fetched_at": self.fetched_at,
        }


class BaseAdapter(ABC):
    """Base class for all source adapters."""

    def __init__(self, config: dict):
        """Initialize adapter with config dict.

        Args:
            config: Dictionary with source configuration
        """
        self.config = config

    @abstractmethod
    def fetch(self) -> List[FetchedItem]:
        """Fetch items from the source.

        Returns:
            List of FetchedItem objects
        """
        pass
