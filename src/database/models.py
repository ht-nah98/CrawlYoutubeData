"""SQLAlchemy ORM models for YouTube Analytics database."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, Integer, String, DateTime, Float, Date, Text, ForeignKey, Numeric, JSON, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Account(Base):
    """Represents a YouTube account."""

    __tablename__ = 'accounts'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    cookies_file = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    channels = relationship('Channel', back_populates='account', cascade='all, delete-orphan')
    analytics = relationship('VideoAnalytics', back_populates='account', cascade='all, delete-orphan')
    scraping_history = relationship('ScrapingHistory', back_populates='account', cascade='all, delete-orphan')

    def __repr__(self) -> str:
        return f"<Account(id={self.id}, name='{self.name}')>"


class Channel(Base):
    """Represents a YouTube channel."""

    __tablename__ = 'channels'

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('accounts.id', ondelete='CASCADE'), nullable=False)
    url = Column(String(500), nullable=False)
    channel_id = Column(String(50))
    channel_name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    account = relationship('Account', back_populates='channels')
    videos = relationship('Video', back_populates='channel', cascade='all, delete-orphan')

    __table_args__ = (
        UniqueConstraint('account_id', 'channel_id', name='uq_account_channel_id'),
        Index('idx_channels_account_id', 'account_id'),
        Index('idx_channels_url', 'url'),
    )

    def __repr__(self) -> str:
        return f"<Channel(id={self.id}, url='{self.url}')>"


class Video(Base):
    """Represents a YouTube video."""

    __tablename__ = 'videos'

    id = Column(Integer, primary_key=True)
    video_id = Column(String(11), unique=True, nullable=False)
    channel_id = Column(Integer, ForeignKey('channels.id', ondelete='SET NULL'))
    title = Column(String(500))
    publish_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    channel = relationship('Channel', back_populates='videos')
    analytics = relationship('VideoAnalytics', back_populates='video', cascade='all, delete-orphan')
    scraping_history = relationship('ScrapingHistory', back_populates='video', cascade='all, delete-orphan')

    __table_args__ = (
        Index('idx_videos_video_id', 'video_id'),
        Index('idx_videos_channel_id', 'channel_id'),
    )

    def __repr__(self) -> str:
        return f"<Video(video_id='{self.video_id}')>"


class VideoAnalytics(Base):
    """Represents analytics data for a YouTube video."""

    __tablename__ = 'video_analytics'

    id = Column(Integer, primary_key=True)
    video_id = Column(String(11), ForeignKey('videos.video_id', ondelete='CASCADE'), nullable=False)
    account_id = Column(Integer, ForeignKey('accounts.id', ondelete='CASCADE'), nullable=False)

    # Numeric metrics
    impressions = Column(Integer)
    views = Column(Integer)
    unique_viewers = Column(Integer)
    ctr_percentage = Column(Numeric(5, 2))
    views_from_impressions = Column(Integer)
    youtube_recommending_percentage = Column(Numeric(5, 2))
    ctr_from_impressions_percentage = Column(Numeric(5, 2))
    avg_view_duration_seconds = Column(Integer)
    watch_time_hours = Column(Numeric(10, 2))

    # Dates
    publish_start_date = Column(Date)
    scraped_at = Column(DateTime, default=datetime.utcnow)

    # Raw JSON data
    top_metrics = Column(JSON)
    traffic_sources = Column(JSON)
    impressions_data = Column(JSON)
    page_text = Column(Text)

    # Relationships
    video = relationship('Video', back_populates='analytics')
    account = relationship('Account', back_populates='analytics')
    traffic_sources_breakdown = relationship('TrafficSource', back_populates='analytics', cascade='all, delete-orphan')

    __table_args__ = (
        UniqueConstraint('video_id', 'account_id', 'scraped_at', name='uq_video_account_timestamp'),
        Index('idx_video_analytics_video_id', 'video_id'),
        Index('idx_video_analytics_account_id', 'account_id'),
        Index('idx_video_analytics_scraped_at', 'scraped_at'),
        Index('idx_video_analytics_video_account', 'video_id', 'account_id'),
    )

    def __repr__(self) -> str:
        return f"<VideoAnalytics(video_id='{self.video_id}', views={self.views})>"


class TrafficSource(Base):
    """Represents traffic source breakdown for a video's analytics."""

    __tablename__ = 'traffic_sources'

    id = Column(Integer, primary_key=True)
    analytics_id = Column(Integer, ForeignKey('video_analytics.id', ondelete='CASCADE'), nullable=False)
    source_name = Column(String(100))
    percentage = Column(Numeric(5, 2))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    analytics = relationship('VideoAnalytics', back_populates='traffic_sources_breakdown')

    __table_args__ = (
        Index('idx_traffic_sources_analytics_id', 'analytics_id'),
        Index('idx_traffic_sources_source_name', 'source_name'),
    )

    def __repr__(self) -> str:
        return f"<TrafficSource(source='{self.source_name}', percentage={self.percentage})>"


class ScrapingHistory(Base):
    """Tracks scraping attempts and history."""

    __tablename__ = 'scraping_history'

    id = Column(Integer, primary_key=True)
    video_id = Column(String(11), ForeignKey('videos.video_id', ondelete='SET NULL'))
    account_id = Column(Integer, ForeignKey('accounts.id', ondelete='SET NULL'))
    status = Column(String(50), default='pending')  # 'success', 'failed', 'skipped', 'pending'
    error_message = Column(Text)
    attempts = Column(Integer, default=0)
    last_attempt_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    video = relationship('Video', back_populates='scraping_history')
    account = relationship('Account', back_populates='scraping_history')

    __table_args__ = (
        Index('idx_scraping_history_video_account', 'video_id', 'account_id'),
        Index('idx_scraping_history_status', 'status'),
        Index('idx_scraping_history_created_at', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<ScrapingHistory(video_id='{self.video_id}', status='{self.status}')>"
