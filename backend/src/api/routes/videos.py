"""API routes for video management."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.schemas import VideoCreate, VideoResponse, VideoUpdate, BulkVideoCreate
from src.api.dependencies import get_db
from src.database.models import Video, Channel

router = APIRouter(prefix="/videos", tags=["videos"])


@router.get("", response_model=List[VideoResponse])
def list_videos(channel_id: int = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List videos with optional channel filter."""
    query = db.query(Video)
    if channel_id is not None:
        query = query.filter(Video.channel_id == channel_id)
    return query.offset(skip).limit(limit).all()


@router.post("", response_model=VideoResponse, status_code=status.HTTP_201_CREATED)
def create_video(video: VideoCreate, db: Session = Depends(get_db)):
    """Create a new video."""
    # Check if video already exists
    existing = db.query(Video).filter(Video.video_id == video.video_id).first()
    if existing:
        return existing  # Return existing if already present

    # Verify channel exists if provided
    if video.channel_id is not None:
        channel = db.query(Channel).filter(Channel.id == video.channel_id).first()
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Channel {video.channel_id} not found"
            )

    db_video = Video(
        video_id=video.video_id,
        channel_id=video.channel_id,
        title=video.title,
        publish_date=video.publish_date
    )
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    return db_video


@router.post("/bulk", response_model=List[VideoResponse], status_code=status.HTTP_201_CREATED)
def bulk_create_videos(bulk_create: BulkVideoCreate, db: Session = Depends(get_db)):
    """Bulk create videos for a channel."""
    # Verify channel exists if provided
    if bulk_create.channel_id is not None:
        channel = db.query(Channel).filter(Channel.id == bulk_create.channel_id).first()
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Channel {bulk_create.channel_id} not found"
            )

    created_videos = []
    for video_id in bulk_create.video_ids:
        # Check if video already exists
        existing = db.query(Video).filter(Video.video_id == video_id).first()
        if existing:
            created_videos.append(existing)
            continue

        db_video = Video(
            video_id=video_id,
            channel_id=bulk_create.channel_id
        )
        db.add(db_video)
        created_videos.append(db_video)

    db.commit()
    for video in created_videos:
        db.refresh(video)

    return created_videos


@router.get("/{video_id}", response_model=VideoResponse)
def get_video(video_id: str, db: Session = Depends(get_db)):
    """Get video by video ID (YouTube ID)."""
    video = db.query(Video).filter(Video.video_id == video_id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video {video_id} not found"
        )
    return video


@router.put("/{video_id}", response_model=VideoResponse)
def update_video(video_id: str, video: VideoUpdate, db: Session = Depends(get_db)):
    """Update a video."""
    db_video = db.query(Video).filter(Video.video_id == video_id).first()
    if not db_video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video {video_id} not found"
        )

    if video.title is not None:
        db_video.title = video.title
    if video.publish_date is not None:
        db_video.publish_date = video.publish_date

    db.commit()
    db.refresh(db_video)
    return db_video


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_video(video_id: str, db: Session = Depends(get_db)):
    """Delete a video."""
    video = db.query(Video).filter(Video.video_id == video_id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video {video_id} not found"
        )

    db.delete(video)
    db.commit()
    return None
