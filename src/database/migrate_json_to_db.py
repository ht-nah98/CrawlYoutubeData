"""
Migration script to import JSON analytics data into PostgreSQL database.

This script reads all analytics_results_*.json files and imports them into the database.
It handles account identification, video tracking, and duplicate prevention.
"""

import json
import os
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from src.database.connection import DatabaseConnection, db
from src.database.models import Account, Channel, Video, VideoAnalytics, TrafficSource
from src.utils.constants import PROJECT_ROOT


class JsonToDbMigrator:
    """Handles migration of JSON data to PostgreSQL database."""

    def __init__(self, db_connection: DatabaseConnection = None, base_path: str = None):
        """
        Initialize migrator.

        Args:
            db_connection: DatabaseConnection instance
            base_path: Base path to search for JSON files (default: project root)
        """
        self.db = db_connection or db
        self.base_path = Path(base_path or PROJECT_ROOT)
        self.stats = {
            'files_found': 0,
            'files_processed': 0,
            'accounts_created': 0,
            'videos_created': 0,
            'analytics_created': 0,
            'duplicates_skipped': 0,
            'errors': 0,
        }

    def find_analytics_files(self) -> list:
        """Find all analytics_results_*.json files."""
        files = list(self.base_path.glob("analytics_results_*.json"))
        self.stats['files_found'] = len(files)
        print(f"Found {len(files)} analytics files to migrate")
        return files

    def extract_account_name(self, filename: str) -> str:
        """Extract account name from filename."""
        # Format: analytics_results_{AccountName}.json
        name = filename.replace("analytics_results_", "").replace(".json", "")
        return name

    def migrate_file(self, file_path: Path, session: Session) -> bool:
        """
        Migrate a single JSON file.

        Args:
            file_path: Path to JSON file
            session: Database session

        Returns:
            True if successful, False otherwise
        """
        try:
            account_name = self.extract_account_name(file_path.name)

            # Read JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not isinstance(data, list):
                print(f"⚠ Skipping {file_path.name}: Not a JSON array")
                return False

            print(f"\nProcessing {file_path.name} ({len(data)} videos)")

            # Get or create account
            account = session.query(Account).filter(Account.name == account_name).first()
            if not account:
                account = Account(
                    name=account_name,
                    cookies_file=f"profile/youtube_cookies_{account_name}.json"
                )
                session.add(account)
                session.flush()
                self.stats['accounts_created'] += 1
                print(f"  ✓ Created account: {account_name}")

            # Process each video's analytics
            for i, record in enumerate(data, 1):
                try:
                    video_id = record.get('video_id')
                    if not video_id:
                        print(f"  ⚠ Skipping record {i}: No video_id")
                        continue

                    # Check if analytics already exists
                    existing = session.query(VideoAnalytics).filter(
                        VideoAnalytics.video_id == video_id,
                        VideoAnalytics.account_id == account.id
                    ).first()

                    if existing:
                        self.stats['duplicates_skipped'] += 1
                        print(f"  - Skipped {i}/{len(data)}: {video_id} (already exists)")
                        continue

                    # Create or get video
                    video = session.query(Video).filter(Video.video_id == video_id).first()
                    if not video:
                        video = Video(video_id=video_id)
                        session.add(video)
                        session.flush()
                        self.stats['videos_created'] += 1

                    # Parse metrics
                    analytics = self._parse_analytics(record, video_id, account.id)

                    session.add(analytics)
                    session.flush()
                    self.stats['analytics_created'] += 1

                    if i % 10 == 0:
                        print(f"  ✓ Processed {i}/{len(data)} records")

                except Exception as e:
                    self.stats['errors'] += 1
                    print(f"  ✗ Error processing record {i}: {e}")
                    continue

            session.commit()
            self.stats['files_processed'] += 1
            print(f"✓ Successfully migrated {file_path.name}")
            return True

        except json.JSONDecodeError as e:
            self.stats['errors'] += 1
            print(f"✗ Error reading {file_path.name}: Invalid JSON - {e}")
            return False
        except Exception as e:
            self.stats['errors'] += 1
            print(f"✗ Error processing {file_path.name}: {e}")
            return False

    def _parse_analytics(self, record: dict, video_id: str, account_id: int) -> VideoAnalytics:
        """Parse analytics record from JSON."""
        # Extract numeric metrics from top_metrics
        top_metrics = record.get('top_metrics', {})
        impressions_data = record.get('impressions_data', {})

        def parse_number(value) -> int:
            """Parse number from various formats."""
            if isinstance(value, (int, float)):
                return int(value)
            if isinstance(value, str):
                # Remove K, M, %, and other symbols
                value = value.replace('K', '').replace('M', '').replace('%', '').strip()
                try:
                    return int(float(value))
                except ValueError:
                    return None
            return None

        def parse_percentage(value) -> float:
            """Parse percentage value."""
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                value = value.replace('%', '').strip()
                try:
                    return float(value)
                except ValueError:
                    return None
            return None

        def parse_float(value) -> float:
            """Parse float value."""
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                try:
                    return float(value)
                except ValueError:
                    return None
            return None

        # Parse publish date
        publish_date = None
        publish_str = record.get('publish_start_date')
        if publish_str:
            try:
                publish_date = datetime.strptime(publish_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        # Create analytics record
        analytics = VideoAnalytics(
            video_id=video_id,
            account_id=account_id,
            impressions=parse_number(top_metrics.get('Impressions')),
            views=parse_number(top_metrics.get('Views')),
            unique_viewers=parse_number(top_metrics.get('Unique viewers')),
            ctr_percentage=parse_percentage(top_metrics.get('Impressions click-through rate')),
            views_from_impressions=parse_number(impressions_data.get('Views from impressions')),
            youtube_recommending_percentage=parse_percentage(
                impressions_data.get('YouTube recommending your content')
            ),
            ctr_from_impressions_percentage=parse_percentage(
                impressions_data.get('Click-through rate (from impressions)')
            ),
            avg_view_duration_seconds=self._parse_duration(
                impressions_data.get('Average view duration (from impressions)')
            ),
            watch_time_hours=parse_float(impressions_data.get('Watch time from impressions (hours)')),
            publish_start_date=publish_date,
            top_metrics=top_metrics,
            traffic_sources=record.get('how_viewers_find'),
            impressions_data=impressions_data,
            page_text=record.get('page_text'),
            scraped_at=self._parse_timestamp(record.get('crawl_datetime')),
        )

        return analytics

    def _parse_duration(self, duration_str: str) -> int:
        """Parse duration string to seconds."""
        if not duration_str:
            return None

        # Format: "MM:SS" or "HH:MM:SS"
        try:
            parts = duration_str.split(':')
            if len(parts) == 2:  # MM:SS
                minutes, seconds = int(parts[0]), int(parts[1])
                return minutes * 60 + seconds
            elif len(parts) == 3:  # HH:MM:SS
                hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
                return hours * 3600 + minutes * 60 + seconds
        except (ValueError, AttributeError):
            pass

        return None

    def _parse_timestamp(self, timestamp_str: str):
        """Parse timestamp from various formats."""
        if not timestamp_str:
            return None

        # Try Vietnamese format: DD/MM/YYYY
        try:
            return datetime.strptime(timestamp_str, '%d/%m/%Y')
        except (ValueError, AttributeError):
            pass

        # Try ISO format: YYYY-MM-DD
        try:
            return datetime.strptime(timestamp_str, '%Y-%m-%d')
        except (ValueError, AttributeError):
            pass

        return datetime.utcnow()

    def run(self) -> dict:
        """
        Run migration for all JSON files.

        Returns:
            Migration statistics
        """
        print("=" * 60)
        print("Starting JSON to PostgreSQL Migration")
        print("=" * 60)

        # Ensure database tables exist
        self.db.create_tables()

        files = self.find_analytics_files()
        if not files:
            print("No analytics files found to migrate")
            return self.stats

        with self.db.session_scope() as session:
            for file_path in sorted(files):
                self.migrate_file(file_path, session)

        # Print summary
        self._print_summary()
        return self.stats

    def _print_summary(self):
        """Print migration summary."""
        print("\n" + "=" * 60)
        print("Migration Summary")
        print("=" * 60)
        print(f"Files found:         {self.stats['files_found']}")
        print(f"Files processed:     {self.stats['files_processed']}")
        print(f"Accounts created:    {self.stats['accounts_created']}")
        print(f"Videos created:      {self.stats['videos_created']}")
        print(f"Analytics created:   {self.stats['analytics_created']}")
        print(f"Duplicates skipped:  {self.stats['duplicates_skipped']}")
        print(f"Errors:              {self.stats['errors']}")
        print("=" * 60)


def main():
    """Run migration from command line."""
    migrator = JsonToDbMigrator()
    migrator.run()


if __name__ == "__main__":
    main()
