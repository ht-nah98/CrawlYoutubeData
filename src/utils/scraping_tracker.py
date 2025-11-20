"""
Scraping Tracker for YouTube Analytics Scraper
Tracks which videos have been scraped and when to avoid redundant scraping
"""
import json
import os
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from .constants import PROFILE_DIR
from .logger import get_logger

logger = get_logger(__name__)


class ScrapingTracker:
    """Tracks scraping history to avoid redundant scraping"""
    
    def __init__(self, tracker_file: Optional[str] = None):
        """
        Initialize ScrapingTracker
        
        Args:
            tracker_file: Path to tracker file (default: profile/scraping_tracker.json)
        """
        if tracker_file is None:
            tracker_file = os.path.join(PROFILE_DIR, 'scraping_tracker.json')
        
        self.tracker_file = tracker_file
        self._tracker_data: Dict[str, Dict] = {}
        self.load()
    
    def load(self) -> None:
        """Load tracker data from file"""
        if os.path.exists(self.tracker_file):
            try:
                with open(self.tracker_file, 'r', encoding='utf-8') as f:
                    self._tracker_data = json.load(f)
                logger.debug(f"Loaded tracker data: {len(self._tracker_data)} videos tracked")
            except Exception as e:
                logger.warning(f"Error loading tracker file: {e}")
                self._tracker_data = {}
        else:
            self._tracker_data = {}
    
    def save(self) -> bool:
        """Save tracker data to file"""
        try:
            # Ensure directory exists
            tracker_dir = os.path.dirname(self.tracker_file)
            if tracker_dir and not os.path.exists(tracker_dir):
                os.makedirs(tracker_dir, exist_ok=True)
            
            with open(self.tracker_file, 'w', encoding='utf-8') as f:
                json.dump(self._tracker_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving tracker file: {e}")
            return False
    
    def mark_scraped(self, video_id: str, timestamp: Optional[datetime] = None) -> None:
        """
        Mark a video as scraped
        
        Args:
            video_id: Video ID
            timestamp: Timestamp (default: now)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        self._tracker_data[video_id] = {
            'last_scraped': timestamp.isoformat(),
            'scrape_count': self._tracker_data.get(video_id, {}).get('scrape_count', 0) + 1
        }
        logger.debug(f"Marked video {video_id} as scraped at {timestamp.isoformat()}")
    
    def mark_multiple_scraped(self, video_ids: List[str], timestamp: Optional[datetime] = None) -> None:
        """
        Mark multiple videos as scraped
        
        Args:
            video_ids: List of video IDs
            timestamp: Timestamp (default: now)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        for video_id in video_ids:
            self.mark_scraped(video_id, timestamp)
    
    def get_last_scraped(self, video_id: str) -> Optional[datetime]:
        """
        Get last scraped timestamp for a video
        
        Args:
            video_id: Video ID
            
        Returns:
            Last scraped datetime or None
        """
        video_data = self._tracker_data.get(video_id)
        if video_data and 'last_scraped' in video_data:
            try:
                return datetime.fromisoformat(video_data['last_scraped'])
            except Exception:
                return None
        return None
    
    def get_scrape_count(self, video_id: str) -> int:
        """
        Get scrape count for a video
        
        Args:
            video_id: Video ID
            
        Returns:
            Number of times video has been scraped
        """
        return self._tracker_data.get(video_id, {}).get('scrape_count', 0)
    
    def should_scrape(self, video_id: str, min_interval_hours: int = 24) -> bool:
        """
        Check if a video should be scraped based on last scraped time
        
        Args:
            video_id: Video ID
            min_interval_hours: Minimum hours between scrapes (default: 24)
            
        Returns:
            True if should scrape, False otherwise
        """
        last_scraped = self.get_last_scraped(video_id)
        
        if last_scraped is None:
            # Never scraped, should scrape
            return True
        
        # Check if enough time has passed
        time_since_last = datetime.now() - last_scraped
        hours_since_last = time_since_last.total_seconds() / 3600
        
        should_scrape = hours_since_last >= min_interval_hours
        
        if not should_scrape:
            logger.debug(f"Video {video_id} was scraped {hours_since_last:.1f} hours ago, skipping (min interval: {min_interval_hours}h)")
        
        return should_scrape
    
    def filter_videos_to_scrape(self, video_ids: List[str], min_interval_hours: int = 24) -> List[str]:
        """
        Filter videos that should be scraped
        
        Args:
            video_ids: List of video IDs to check
            min_interval_hours: Minimum hours between scrapes
            
        Returns:
            List of video IDs that should be scraped
        """
        videos_to_scrape = []
        skipped_count = 0
        
        for video_id in video_ids:
            if self.should_scrape(video_id, min_interval_hours):
                videos_to_scrape.append(video_id)
            else:
                skipped_count += 1
        
        if skipped_count > 0:
            logger.info(f"Filtered {skipped_count} videos (scraped recently), {len(videos_to_scrape)} videos to scrape")
        
        return videos_to_scrape
    
    def get_statistics(self) -> Dict:
        """
        Get scraping statistics
        
        Returns:
            Dictionary with statistics
        """
        total_videos = len(self._tracker_data)
        total_scrapes = sum(data.get('scrape_count', 0) for data in self._tracker_data.values())
        
        # Videos scraped in last 24 hours
        recent_count = 0
        for video_id, data in self._tracker_data.items():
            last_scraped = self.get_last_scraped(video_id)
            if last_scraped:
                hours_ago = (datetime.now() - last_scraped).total_seconds() / 3600
                if hours_ago <= 24:
                    recent_count += 1
        
        return {
            'total_videos_tracked': total_videos,
            'total_scrapes': total_scrapes,
            'videos_scraped_last_24h': recent_count,
            'average_scrapes_per_video': total_scrapes / total_videos if total_videos > 0 else 0
        }
    
    def cleanup_old_entries(self, days_to_keep: int = 90) -> int:
        """
        Remove entries older than specified days
        
        Args:
            days_to_keep: Number of days to keep entries
            
        Returns:
            Number of entries removed
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        removed_count = 0
        
        video_ids_to_remove = []
        for video_id, data in self._tracker_data.items():
            last_scraped = self.get_last_scraped(video_id)
            if last_scraped and last_scraped < cutoff_date:
                video_ids_to_remove.append(video_id)
        
        for video_id in video_ids_to_remove:
            del self._tracker_data[video_id]
            removed_count += 1
        
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old tracker entries (older than {days_to_keep} days)")
            self.save()
        
        return removed_count



