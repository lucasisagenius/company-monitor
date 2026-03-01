"""Main orchestrator agent for monitoring company updates."""
import os
import sys
import yaml
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv

from adapters import ADAPTER_REGISTRY
from core import (
    filter_new_items,
    filter_by_date,
    mark_seen,
    mark_notified,
    get_summary,
    send_digest_email,
)


def load_config(config_path: str = "config/companies.yaml") -> dict:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Failed to load config: {e}")
        return {}


def run_once(config_path: str = "config/companies.yaml") -> None:
    """Run the monitoring agent once."""
    # Load environment variables from .env file
    project_dir = Path(__file__).parent
    env_file = project_dir / '.env'
    load_dotenv(dotenv_path=str(env_file))

    config = load_config(config_path)

    if not config:
        print("Failed to load configuration")
        return

    notification_email = config.get('notification_email')
    if not notification_email or notification_email == "your-email@example.com":
        print("ERROR: notification_email not configured in config.yaml")
        print("Please update config/companies.yaml with your email address")
        return

    # Get notification age threshold (default: 7 days)
    notification_age_days = config.get('notification_age_days', 7)

    companies = config.get('companies', [])
    if not companies:
        print("No companies configured")
        return

    print(f"Starting monitoring run for {len(companies)} companies")

    for company_config in companies:
        company_name = company_config.get('name')
        sources = company_config.get('sources', [])

        print(f"\n{'='*60}")
        print(f"Processing: {company_name}")
        print(f"{'='*60}")

        all_new_items = []
        urls_to_notify = []

        for source_config in sources:
            source_type = source_config.get('type')
            adapter_class = ADAPTER_REGISTRY.get(source_type)

            if not adapter_class:
                print(f"Unknown source type: {source_type}")
                continue

            try:
                print(f"\nFetching from {source_type}: {source_config.get('label', source_type)}")
                adapter = adapter_class(source_config)
                fetched_items = adapter.fetch()
                print(f"Fetched {len(fetched_items)} items")

                # Convert FetchedItem to dict for database operations
                item_dicts = [item.to_dict() for item in fetched_items]

                # Filter out items we've already seen
                new_items = filter_new_items(company_name, item_dicts)
                print(f"Found {len(new_items)} new items")

                # Filter out items older than notification_age_days
                recent_items = filter_by_date(new_items, max_age_days=notification_age_days)
                if len(recent_items) < len(new_items):
                    skipped = len(new_items) - len(recent_items)
                    print(f"Skipped {skipped} items older than {notification_age_days} days")

                # Mark items as seen immediately (before summarization)
                # This prevents re-notification if summarization fails
                for item in recent_items:
                    mark_seen(
                        company_name=company_name,
                        source_type=source_type,
                        source_label=source_config.get('label'),
                        url=item['url'],
                        title=item.get('title'),
                        published_date=item.get('published_date')
                    )
                    urls_to_notify.append(item['url'])

                all_new_items.extend(recent_items)

            except Exception as e:
                print(f"Error processing {source_type}: {e}")
                continue

        # Summarize and send digest if we have new items
        if all_new_items:
            print(f"\nSummarizing {len(all_new_items)} new items for {company_name}")

            items_with_summaries = []
            for item in all_new_items:
                print(f"  Summarizing: {item.get('title', 'Untitled')[:60]}...")
                summary = get_summary(item)
                item['summary'] = summary
                items_with_summaries.append(item)

            # Send email
            print(f"\nSending digest email to {notification_email}")
            success = send_digest_email(company_name, items_with_summaries, notification_email)

            if success:
                # Mark items as notified
                mark_notified(company_name, urls_to_notify)
                print(f"Marked {len(urls_to_notify)} items as notified")
        else:
            print(f"No new items found for {company_name}")

    print(f"\n{'='*60}")
    print("Monitoring run completed")
    print(f"{'='*60}")


if __name__ == '__main__':
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)

    config_path = sys.argv[1] if len(sys.argv) > 1 else "config/companies.yaml"
    run_once(config_path)
