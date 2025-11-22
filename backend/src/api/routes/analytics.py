"""API routes for analytics data."""

from typing import List
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from src.api.schemas import (
    VideoAnalyticsCreate,
    VideoAnalyticsResponse,
    VideoAnalyticsUpdate,
    BulkAnalyticsCreate,
    AnalyticsStatsResponse,
)
from src.api.dependencies import get_db
from src.database.models import VideoAnalytics, Video, Account, TrafficSource

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("", response_model=List[VideoAnalyticsResponse])
def list_analytics(
    account_id: int = Query(None),
    video_id: str = Query(None),
    date_from: date = Query(None),
    date_to: date = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """
    List analytics with optional filters.

    Query parameters:
    - account_id: Filter by account
    - video_id: Filter by video
    - date_from: Filter by scrape date (from)
    - date_to: Filter by scrape date (to)
    - skip: Pagination offset
    - limit: Pagination limit
    """
    query = db.query(VideoAnalytics)

    if account_id is not None:
        query = query.filter(VideoAnalytics.account_id == account_id)
    if video_id is not None:
        query = query.filter(VideoAnalytics.video_id == video_id)
    if date_from is not None:
        query = query.filter(VideoAnalytics.scraped_at >= date_from)
    if date_to is not None:
        query = query.filter(VideoAnalytics.scraped_at <= date_to)

    return query.order_by(VideoAnalytics.scraped_at.desc()).offset(skip).limit(limit).all()


@router.post("", response_model=VideoAnalyticsResponse, status_code=status.HTTP_201_CREATED)
def create_analytics(analytics: VideoAnalyticsCreate, db: Session = Depends(get_db)):
    """Create new analytics record."""
    # Verify video exists
    video = db.query(Video).filter(Video.video_id == analytics.video_id).first()
    if not video:
        # Create video if it doesn't exist
        video = Video(video_id=analytics.video_id)
        db.add(video)
        db.flush()

    # Verify account exists
    account = db.query(Account).filter(Account.id == analytics.account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {analytics.account_id} not found"
        )

    db_analytics = VideoAnalytics(
        video_id=analytics.video_id,
        account_id=analytics.account_id,
        impressions=analytics.impressions,
        views=analytics.views,
        unique_viewers=analytics.unique_viewers,
        ctr_percentage=analytics.ctr_percentage,
        views_from_impressions=analytics.views_from_impressions,
        youtube_recommending_percentage=analytics.youtube_recommending_percentage,
        ctr_from_impressions_percentage=analytics.ctr_from_impressions_percentage,
        avg_view_duration_seconds=analytics.avg_view_duration_seconds,
        watch_time_hours=analytics.watch_time_hours,
        publish_start_date=analytics.publish_start_date,
        top_metrics=analytics.top_metrics,
        traffic_sources=analytics.traffic_sources,
        impressions_data=analytics.impressions_data,
        page_text=analytics.page_text,
    )
    db.add(db_analytics)
    db.commit()
    db.refresh(db_analytics)
    return db_analytics


@router.post("/bulk", response_model=List[VideoAnalyticsResponse], status_code=status.HTTP_201_CREATED)
def bulk_create_analytics(bulk: BulkAnalyticsCreate, db: Session = Depends(get_db)):
    """Bulk create analytics records."""
    created_analytics = []

    for analytics_data in bulk.analytics:
        # Verify/create video
        video = db.query(Video).filter(Video.video_id == analytics_data.video_id).first()
        if not video:
            video = Video(video_id=analytics_data.video_id)
            db.add(video)
            db.flush()

        # Verify account
        account = db.query(Account).filter(Account.id == analytics_data.account_id).first()
        if not account:
            continue  # Skip if account doesn't exist

        db_analytics = VideoAnalytics(
            video_id=analytics_data.video_id,
            account_id=analytics_data.account_id,
            impressions=analytics_data.impressions,
            views=analytics_data.views,
            unique_viewers=analytics_data.unique_viewers,
            ctr_percentage=analytics_data.ctr_percentage,
            views_from_impressions=analytics_data.views_from_impressions,
            youtube_recommending_percentage=analytics_data.youtube_recommending_percentage,
            ctr_from_impressions_percentage=analytics_data.ctr_from_impressions_percentage,
            avg_view_duration_seconds=analytics_data.avg_view_duration_seconds,
            watch_time_hours=analytics_data.watch_time_hours,
            publish_start_date=analytics_data.publish_start_date,
            top_metrics=analytics_data.top_metrics,
            traffic_sources=analytics_data.traffic_sources,
            impressions_data=analytics_data.impressions_data,
            page_text=analytics_data.page_text,
        )
        db.add(db_analytics)
        created_analytics.append(db_analytics)

    db.commit()
    for analytics in created_analytics:
        db.refresh(analytics)

    return created_analytics


@router.get("/video/{video_id}", response_model=List[VideoAnalyticsResponse])
def get_video_analytics(
    video_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Get all analytics records for a specific video."""
    video = db.query(Video).filter(Video.video_id == video_id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video {video_id} not found"
        )

    return (
        db.query(VideoAnalytics)
        .filter(VideoAnalytics.video_id == video_id)
        .order_by(VideoAnalytics.scraped_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/account/{account_id}/stats", response_model=AnalyticsStatsResponse)
def get_account_stats(
    account_id: int,
    date_from: date = Query(None),
    date_to: date = Query(None),
    db: Session = Depends(get_db),
):
    """Get aggregated statistics for an account."""
    # Verify account exists
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {account_id} not found"
        )

    query = db.query(VideoAnalytics).filter(VideoAnalytics.account_id == account_id)

    if date_from is not None:
        query = query.filter(VideoAnalytics.scraped_at >= date_from)
    if date_to is not None:
        query = query.filter(VideoAnalytics.scraped_at <= date_to)

    # Get latest analytics for each video (avoid double-counting)
    latest_analytics = (
        db.query(VideoAnalytics)
        .filter(VideoAnalytics.account_id == account_id)
        .distinct(VideoAnalytics.video_id)
        .order_by(VideoAnalytics.video_id, VideoAnalytics.scraped_at.desc())
    )

    if date_from is not None:
        latest_analytics = latest_analytics.filter(VideoAnalytics.scraped_at >= date_from)
    if date_to is not None:
        latest_analytics = latest_analytics.filter(VideoAnalytics.scraped_at <= date_to)

    analytics_list = latest_analytics.all()

    total_videos = len(analytics_list)
    total_impressions = sum(a.impressions or 0 for a in analytics_list)
    total_views = sum(a.views or 0 for a in analytics_list)
    total_watch_time = sum(float(a.watch_time_hours or 0) for a in analytics_list)

    average_views = total_views / total_videos if total_videos > 0 else 0

    # Calculate average CTR
    ctr_list = [float(a.ctr_percentage) for a in analytics_list if a.ctr_percentage]
    average_ctr = sum(ctr_list) / len(ctr_list) if ctr_list else None

    return AnalyticsStatsResponse(
        total_videos=total_videos,
        total_impressions=total_impressions,
        total_views=total_views,
        total_watch_time_hours=total_watch_time,
        average_ctr_percentage=average_ctr,
        average_views_per_video=average_views,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/{analytics_id}", response_model=VideoAnalyticsResponse)
def get_analytics(analytics_id: int, db: Session = Depends(get_db)):
    """Get analytics by ID."""
    analytics = db.query(VideoAnalytics).filter(VideoAnalytics.id == analytics_id).first()
    if not analytics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analytics {analytics_id} not found"
        )
    return analytics


@router.put("/{analytics_id}", response_model=VideoAnalyticsResponse)
def update_analytics(analytics_id: int, analytics: VideoAnalyticsUpdate, db: Session = Depends(get_db)):
    """Update analytics record."""
    db_analytics = db.query(VideoAnalytics).filter(VideoAnalytics.id == analytics_id).first()
    if not db_analytics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analytics {analytics_id} not found"
        )

    # Update provided fields
    if analytics.impressions is not None:
        db_analytics.impressions = analytics.impressions
    if analytics.views is not None:
        db_analytics.views = analytics.views
    if analytics.unique_viewers is not None:
        db_analytics.unique_viewers = analytics.unique_viewers
    if analytics.ctr_percentage is not None:
        db_analytics.ctr_percentage = analytics.ctr_percentage
    if analytics.views_from_impressions is not None:
        db_analytics.views_from_impressions = analytics.views_from_impressions
    if analytics.youtube_recommending_percentage is not None:
        db_analytics.youtube_recommending_percentage = analytics.youtube_recommending_percentage
    if analytics.ctr_from_impressions_percentage is not None:
        db_analytics.ctr_from_impressions_percentage = analytics.ctr_from_impressions_percentage
    if analytics.avg_view_duration_seconds is not None:
        db_analytics.avg_view_duration_seconds = analytics.avg_view_duration_seconds
    if analytics.watch_time_hours is not None:
        db_analytics.watch_time_hours = analytics.watch_time_hours
    if analytics.top_metrics is not None:
        db_analytics.top_metrics = analytics.top_metrics
    if analytics.traffic_sources is not None:
        db_analytics.traffic_sources = analytics.traffic_sources
    if analytics.impressions_data is not None:
        db_analytics.impressions_data = analytics.impressions_data

    db.commit()
    db.refresh(db_analytics)
    return db_analytics


@router.delete("/{analytics_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_analytics(analytics_id: int, db: Session = Depends(get_db)):
    """Delete analytics record."""
    analytics = db.query(VideoAnalytics).filter(VideoAnalytics.id == analytics_id).first()
    if not analytics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analytics {analytics_id} not found"
        )

    db.delete(analytics)
    db.commit()
    return None
