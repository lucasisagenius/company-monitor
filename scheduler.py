"""Scheduler for running the monitoring agent."""
import os
import sys
import argparse
import schedule
import time
from pathlib import Path
from dotenv import load_dotenv

from agent import run_once


def main():
    """Main scheduler entry point."""
    parser = argparse.ArgumentParser(
        description='Company monitoring agent scheduler'
    )
    parser.add_argument(
        '--run-once',
        action='store_true',
        help='Run once and exit (for use with cron)'
    )
    parser.add_argument(
        '--interval-hours',
        type=int,
        default=6,
        help='Check interval in hours for continuous mode (default: 6)'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config/companies.yaml',
        help='Path to config file'
    )

    args = parser.parse_args()

    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)

    # Load environment variables from .env file
    env_file = project_dir / '.env'
    load_dotenv(dotenv_path=str(env_file))

    if args.run_once:
        # Run once and exit
        print("Running monitoring agent once...")
        run_once(args.config)
        sys.exit(0)
    else:
        # Run in loop with interval
        interval_hours = args.interval_hours
        print(f"Starting scheduler with {interval_hours}h interval")
        print("Press Ctrl+C to stop")

        # Schedule the job
        schedule.every(interval_hours).hours.do(run_once, config_path=args.config)

        # Run the scheduler loop
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\nScheduler stopped")
            sys.exit(0)


if __name__ == '__main__':
    main()
