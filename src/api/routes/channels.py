"""API routes for channel management."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.schemas import ChannelCreate, ChannelResponse, ChannelUpdate
from src.api.dependencies import get_db
from src.database.models import Channel, Account

router = APIRouter(prefix="/channels", tags=["channels"])


@router.get("", response_model=List[ChannelResponse])
def list_channels(account_id: int = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List channels with optional account filter."""
    query = db.query(Channel)
    if account_id is not None:
        query = query.filter(Channel.account_id == account_id)
    return query.offset(skip).limit(limit).all()


@router.post("", response_model=ChannelResponse, status_code=status.HTTP_201_CREATED)
def create_channel(channel: ChannelCreate, db: Session = Depends(get_db)):
    """Create a new channel for an account."""
    # Verify account exists
    account = db.query(Account).filter(Account.id == channel.account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {channel.account_id} not found"
        )

    db_channel = Channel(
        account_id=channel.account_id,
        url=channel.url,
        channel_id=channel.channel_id,
        channel_name=channel.channel_name
    )
    db.add(db_channel)
    db.commit()
    db.refresh(db_channel)
    return db_channel


@router.get("/{channel_id}", response_model=ChannelResponse)
def get_channel(channel_id: int, db: Session = Depends(get_db)):
    """Get channel by ID."""
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Channel {channel_id} not found"
        )
    return channel


@router.put("/{channel_id}", response_model=ChannelResponse)
def update_channel(channel_id: int, channel: ChannelUpdate, db: Session = Depends(get_db)):
    """Update a channel."""
    db_channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not db_channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Channel {channel_id} not found"
        )

    if channel.url is not None:
        db_channel.url = channel.url
    if channel.channel_id is not None:
        db_channel.channel_id = channel.channel_id
    if channel.channel_name is not None:
        db_channel.channel_name = channel.channel_name

    db.commit()
    db.refresh(db_channel)
    return db_channel


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_channel(channel_id: int, db: Session = Depends(get_db)):
    """Delete a channel."""
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Channel {channel_id} not found"
        )

    db.delete(channel)
    db.commit()
    return None
