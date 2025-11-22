"""Pydantic schemas for FastAPI request/response validation."""

from datetime import datetime, date
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field


# ==================== Account Schemas ====================

class AccountBase(BaseModel):
    """Base account schema."""

    name: str = Field(..., min_length=1, max_length=255, description="Account name")
    cookies_file: Optional[str] = Field(None, max_length=500, description="Path to cookies file")


class AccountCreate(AccountBase):
    """Schema for creating an account."""

    pass


class AccountUpdate(BaseModel):
    """Schema for updating an account."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    cookies_file: Optional[str] = Field(None, max_length=500)


class AccountResponse(AccountBase):
    """Schema for account response."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Channel Schemas ====================

class ChannelBase(BaseModel):
    """Base channel schema."""

    url: str = Field(..., description="YouTube channel URL")
    channel_id: Optional[str] = Field(None, max_length=50, description="YouTube channel ID")
    channel_name: Optional[str] = Field(None, max_length=255, description="Channel display name")


class ChannelCreate(ChannelBase):
    """Schema for creating a channel."""

    account_id: int = Field(..., description="Account ID")


class ChannelUpdate(BaseModel):
    """Schema for updating a channel."""

    url: Optional[str] = None
    channel_id: Optional[str] = None
    channel_name: Optional[str] = None


class ChannelResponse(ChannelBase):
    """Schema for channel response."""

    id: int
    account_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Video Schemas ====================

class VideoBase(BaseModel):
    """Base video schema."""

    video_id: str = Field(..., min_length=11, max_length=11, description="YouTube video ID")
    title: Optional[str] = Field(None, max_length=500, description="Video title")
    publish_date: Optional[date] = Field(None, description="Video publish date")


class VideoCreate(VideoBase):
    """Schema for creating a video."""

    channel_id: Optional[int] = Field(None, description="Channel ID")


class VideoUpdate(BaseModel):
    """Schema for updating a video."""

    title: Optional[str] = None
    publish_date: Optional[date] = None


class VideoResponse(VideoBase):
    """Schema for video response."""

    id: int
    channel_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Traffic Source Schemas ====================

class TrafficSourceBase(BaseModel):
    """Base traffic source schema."""

    source_name: str = Field(..., description="Traffic source name")
    percentage: float = Field(..., ge=0, le=100, description="Percentage (0-100)")


class TrafficSourceCreate(TrafficSourceBase):
    """Schema for creating traffic source."""

    analytics_id: int


class TrafficSourceResponse(TrafficSourceBase):
    """Schema for traffic source response."""

    id: int
    analytics_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Analytics Schemas ====================

class VideoAnalyticsBase(BaseModel):
    """Base analytics schema."""

    impressions: Optional[int] = None
    views: Optional[int] = None
    unique_viewers: Optional[int] = None
    ctr_percentage: Optional[float] = None
    views_from_impressions: Optional[int] = None
    youtube_recommending_percentage: Optional[float] = None
    ctr_from_impressions_percentage: Optional[float] = None
    avg_view_duration_seconds: Optional[int] = None
    watch_time_hours: Optional[float] = None
    publish_start_date: Optional[date] = None
    top_metrics: Optional[Dict[str, Any]] = None
    traffic_sources: Optional[Dict[str, Any]] = None
    impressions_data: Optional[Dict[str, Any]] = None
    page_text: Optional[str] = None


class VideoAnalyticsCreate(VideoAnalyticsBase):
    """Schema for creating analytics."""

    video_id: str = Field(..., min_length=11, max_length=11)
    account_id: int


class VideoAnalyticsUpdate(BaseModel):
    """Schema for updating analytics."""

    impressions: Optional[int] = None
    views: Optional[int] = None
    unique_viewers: Optional[int] = None
    ctr_percentage: Optional[float] = None
    views_from_impressions: Optional[int] = None
    youtube_recommending_percentage: Optional[float] = None
    ctr_from_impressions_percentage: Optional[float] = None
    avg_view_duration_seconds: Optional[int] = None
    watch_time_hours: Optional[float] = None
    top_metrics: Optional[Dict[str, Any]] = None
    traffic_sources: Optional[Dict[str, Any]] = None
    impressions_data: Optional[Dict[str, Any]] = None


class VideoAnalyticsResponse(VideoAnalyticsBase):
    """Schema for analytics response."""

    id: int
    video_id: str
    account_id: int
    scraped_at: datetime
    traffic_sources_breakdown: List[TrafficSourceResponse] = []

    class Config:
        from_attributes = True


# ==================== Aggregation Schemas ====================

class AnalyticsStatsResponse(BaseModel):
    """Schema for aggregated analytics statistics."""

    total_videos: int
    total_impressions: int
    total_views: int
    total_watch_time_hours: float
    average_ctr_percentage: Optional[float] = None
    average_views_per_video: float
    date_from: Optional[date] = None
    date_to: Optional[date] = None


class AnalyticsFilterParams(BaseModel):
    """Schema for analytics filtering parameters."""

    account_id: Optional[int] = None
    video_id: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    min_views: Optional[int] = None
    max_views: Optional[int] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)


# ==================== Scraping History Schemas ====================

class ScrapingHistoryResponse(BaseModel):
    """Schema for scraping history response."""

    id: int
    video_id: Optional[str]
    account_id: Optional[int]
    status: str
    error_message: Optional[str]
    attempts: int
    last_attempt_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Bulk Operations ====================

class BulkVideoCreate(BaseModel):
    """Schema for bulk creating videos."""

    channel_id: Optional[int] = None
    video_ids: List[str] = Field(..., min_items=1, description="List of video IDs")


class BulkAnalyticsCreate(BaseModel):
    """Schema for bulk creating analytics."""

    analytics: List[VideoAnalyticsCreate]


# ==================== Response Schemas ====================

class APIResponse(BaseModel):
    """Generic API response schema."""

    success: bool
    message: str
    data: Optional[Any] = None


class PaginatedResponse(BaseModel):
    """Paginated response schema."""

    total: int
    skip: int
    limit: int
    items: List[Any]
