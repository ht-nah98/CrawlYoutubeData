"""Database writers for scraper integration."""

from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy.orm import Session

from src.database.connection import DatabaseConnection, db
from src.database.models import Account, Video, VideoAnalytics, TrafficSource


class ScraperDatabaseWriter:
    """Writes scraper results to the database."""

    def __init__(self, db_connection: DatabaseConnection = None):
        """
        Initialize database writer.

        Args:
            db_connection: DatabaseConnection instance (uses global db if None)
        """
        self.db = db_connection or db

    def save_analytics(
        self,
        video_id: str,
        account_name: str,
        analytics_data: Dict[str, Any],
        channel_url: str = None,
        session: Session = None,
    ) -> VideoAnalytics:
        """
        Save analytics data to database.

        This method is designed to be called from the YouTube scraper.

        Args:
            video_id: YouTube video ID
            account_name: Account name (must exist in database)
            analytics_data: Analytics data dictionary containing:
                - top_metrics: Dict of top metrics
                - how_viewers_find: Dict of traffic sources
                - impressions_data: Dict of impressions details
                - publish_start_date: Video publish date
                - crawl_datetime: When the data was scraped
                - page_text: Raw page text for debugging
            channel_url: Optional channel URL to link video to channel
            session: Optional database session (creates new if None)

        Returns:
            Created or updated VideoAnalytics object
        """
        close_session = False
        if session is None:
            session = self.db.get_session()
            close_session = True

        try:
            # Get account
            account = session.query(Account).filter(Account.name == account_name).first()
            if not account:
                raise ValueError(f"Account '{account_name}' not found in database")

            # Create or get channel if channel_url is provided
            channel = None
            if channel_url:
                from src.database.models import Channel
                
                # Check if channel already exists for this account
                channel = session.query(Channel).filter(
                    Channel.account_id == account.id,
                    Channel.url == channel_url
                ).first()
                
                if not channel:
                    # Extract channel_id from URL
                    channel_id = self._extract_channel_id_from_url(channel_url)
                    
                    # Create new channel
                    channel = Channel(
                        account_id=account.id,
                        url=channel_url,
                        channel_id=channel_id
                    )
                    session.add(channel)
                    session.flush()  # Get channel.id
                    print(f"  ✓ Created channel in database: {channel_url}")

            # Get or create video
            video = session.query(Video).filter(Video.video_id == video_id).first()
            if not video:
                video = Video(video_id=video_id)
                session.add(video)
                session.flush()

            # Parse metrics from analytics data
            top_metrics = analytics_data.get('top_metrics', {})
            impressions_data = analytics_data.get('impressions_data', {})
            traffic_sources = analytics_data.get('how_viewers_find', {})

            # Create analytics record
            analytics = VideoAnalytics(
                video_id=video_id,
                account_id=account.id,
                impressions=self._parse_number(top_metrics.get('Impressions')),
                views=self._parse_number(top_metrics.get('Views')),
                unique_viewers=self._parse_number(top_metrics.get('Unique viewers')),
                ctr_percentage=self._parse_percentage(top_metrics.get('Impressions click-through rate')),
                views_from_impressions=self._parse_number(impressions_data.get('Views from impressions')),
                youtube_recommending_percentage=self._parse_percentage(
                    impressions_data.get('YouTube recommending your content')
                ),
                ctr_from_impressions_percentage=self._parse_percentage(
                    impressions_data.get('Click-through rate (from impressions)')
                ),
                avg_view_duration_seconds=self._parse_duration(
                    impressions_data.get('Average view duration (from impressions)')
                ),
                watch_time_hours=self._parse_float(
                    impressions_data.get('Watch time from impressions (hours)')
                ),
                publish_start_date=self._parse_date(analytics_data.get('publish_start_date')),
                top_metrics=top_metrics,
                traffic_sources=traffic_sources,
                impressions_data=impressions_data,
                page_text=analytics_data.get('page_text'),
                scraped_at=self._parse_timestamp(analytics_data.get('crawl_datetime')),
            )

            session.add(analytics)
            session.flush()  # Flush to get analytics.id before saving traffic sources

            # Add traffic sources if provided (after flush so analytics.id is available)
            if traffic_sources:
                self._save_traffic_sources(analytics, traffic_sources, session)

            session.commit()
            session.refresh(analytics)

            return analytics

        finally:
            if close_session:
                session.close()

    def bulk_save_analytics(
        self,
        videos_data: List[Dict[str, Any]],
        account_name: str,
        session: Session = None,
    ) -> List[VideoAnalytics]:
        """
        Bulk save multiple analytics records.

        Args:
            videos_data: List of analytics dictionaries, each containing:
                - video_id: YouTube video ID
                - (other fields as per save_analytics)
            account_name: Account name
            session: Optional database session

        Returns:
            List of created VideoAnalytics objects
        """
        close_session = False
        if session is None:
            session = self.db.get_session()
            close_session = True

        try:
            created = []
            for video_data in videos_data:
                video_id = video_data.pop('video_id', None)
                if not video_id:
                    continue

                analytics = self.save_analytics(
                    video_id=video_id,
                    account_name=account_name,
                    analytics_data=video_data,
                    session=session,
                )
                created.append(analytics)

            return created

        finally:
            if close_session:
                session.close()

    def get_account(self, account_name: str, session: Session = None) -> Account:
        """
        Get account from database.

        Args:
            account_name: Account name
            session: Optional database session

        Returns:
            Account object or None
        """
        close_session = False
        if session is None:
            session = self.db.get_session()
            close_session = True

        try:
            return session.query(Account).filter(Account.name == account_name).first()
        finally:
            if close_session:
                session.close()

    def get_video_analytics(
        self,
        video_id: str,
        account_name: str,
        session: Session = None,
    ) -> Optional[VideoAnalytics]:
        """
        Get latest analytics for a video.

        Args:
            video_id: YouTube video ID
            account_name: Account name
            session: Optional database session

        Returns:
            Latest VideoAnalytics object or None
        """
        close_session = False
        if session is None:
            session = self.db.get_session()
            close_session = True

        try:
            account = session.query(Account).filter(Account.name == account_name).first()
            if not account:
                return None

            return (
                session.query(VideoAnalytics)
                .filter(
                    VideoAnalytics.video_id == video_id,
                    VideoAnalytics.account_id == account.id,
                )
                .order_by(VideoAnalytics.scraped_at.desc())
                .first()
            )
        finally:
            if close_session:
                session.close()

    def _save_traffic_sources(
        self,
        analytics: VideoAnalytics,
        traffic_sources: Dict[str, Any],
        session: Session,
    ) -> None:
        """Save traffic sources breakdown."""
        for source_name, percentage in traffic_sources.items():
            if isinstance(percentage, str):
                percentage = self._parse_percentage(percentage)

            if percentage is not None:
                traffic = TrafficSource(
                    analytics_id=analytics.id,
                    source_name=source_name,
                    percentage=percentage,
                )
                session.add(traffic)

    # ==================== Parsing Utilities ====================

    @staticmethod
    def _parse_number(value: Any) -> Optional[int]:
        """Parse number from various formats."""
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            # Remove K, M, %, and other symbols
            value = value.replace('K', '').replace('M', '').replace('%', '').strip()
            try:
                return int(float(value))
            except (ValueError, AttributeError):
                return None
        return None

    @staticmethod
    def _parse_percentage(value: Any) -> Optional[float]:
        """Parse percentage value."""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            value = value.replace('%', '').strip()
            try:
                return float(value)
            except (ValueError, AttributeError):
                return None
        return None

    @staticmethod
    def _parse_float(value: Any) -> Optional[float]:
        """Parse float value."""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except (ValueError, AttributeError):
                return None
        return None

    @staticmethod
    def _parse_date(value: Any) -> Optional[datetime]:
        """Parse date value."""
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y'):
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
        return None

    @staticmethod
    def _parse_timestamp(value: Any) -> Optional[datetime]:
        """Parse timestamp value."""
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%Y-%m-%d %H:%M:%S'):
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
        return datetime.utcnow()

    @staticmethod
    def _parse_duration(duration_str: str) -> Optional[int]:
        """Parse duration string to seconds."""
        if not duration_str:
            return None

        try:
            parts = duration_str.split(':')
            if len(parts) == 2:  # MM:SS
                minutes, seconds = int(parts[0]), int(parts[1])
                return minutes * 60 + seconds
            elif len(parts) == 3:  # HH:MM:SS
                hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
                return hours * 3600 + minutes * 60 + seconds
        except (ValueError, AttributeError, IndexError):
            pass

        return None

    @staticmethod
    def _extract_channel_id_from_url(url: str) -> Optional[str]:
        """Extract channel ID from YouTube channel URL.
        
        Supports formats:
        - https://www.youtube.com/channel/UCxxxxxx
        - https://www.youtube.com/@username
        - https://www.youtube.com/c/channelname
        """
        if not url:
            return None
        
        import re
        
        # Extract channel ID from /channel/UCxxxxxx format
        match = re.search(r'/channel/([^/?]+)', url)
        if match:
            return match.group(1)
        
        # For @username or /c/ format, return the identifier
        match = re.search(r'/@([^/?]+)', url)
        if match:
            return match.group(1)
        
        match = re.search(r'/c/([^/?]+)', url)
        if match:
            return match.group(1)
        
        # If no pattern matches, return None
        return None


# Global instance for easy access
db_writer = ScraperDatabaseWriter()
