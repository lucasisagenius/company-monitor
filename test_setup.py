#!/usr/bin/env python3
"""Quick test to verify the setup works."""
import os
import sys
from pathlib import Path

# Change to project directory
os.chdir(Path(__file__).parent)

print("Testing imports...")

try:
    from adapters import ADAPTER_REGISTRY
    print("✓ Adapters imported successfully")
except Exception as e:
    print(f"✗ Failed to import adapters: {e}")
    sys.exit(1)

try:
    from core import (
        get_db_connection,
        filter_new_items,
        mark_seen,
        send_digest_email,
        get_summary,
    )
    print("✓ Core modules imported successfully")
except Exception as e:
    print(f"✗ Failed to import core: {e}")
    sys.exit(1)

try:
    import yaml
    print("✓ YAML support available")
except Exception as e:
    print(f"✗ YAML not available: {e}")
    sys.exit(1)

print("\nTesting database...")
try:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM seen_items")
    count = cursor.fetchone()[0]
    conn.close()
    print(f"✓ Database initialized ({count} items tracked)")
except Exception as e:
    print(f"✗ Database error: {e}")
    sys.exit(1)

print("\nTesting config...")
try:
    with open('config/companies.yaml', 'r') as f:
        config = yaml.safe_load(f)
    companies = config.get('companies', [])
    print(f"✓ Config loaded ({len(companies)} companies)")
except Exception as e:
    print(f"✗ Config error: {e}")
    sys.exit(1)

print("\nTesting adapters...")
for adapter_type, adapter_class in ADAPTER_REGISTRY.items():
    print(f"  ✓ {adapter_type}: {adapter_class.__name__}")

print("\n✓ All tests passed!")
print("\nNext steps:")
print("1. Configure .env with your API keys and email")
print("2. Update config/companies.yaml with your email and companies")
print("3. Run: python scheduler.py --run-once")
