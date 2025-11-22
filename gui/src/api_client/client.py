"""
Backend API Client
Handles all communication with the backend server
"""

import requests
from typing import List, Dict, Optional, Any
import json


class BackendAPIClient:
    """Client for communicating with YouTube Analytics backend API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize API client
        
        Args:
            base_url: Base URL of the backend API
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.timeout = 30
        self._connected = False
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """
        Make HTTP request to backend
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            **kwargs: Additional request parameters
            
        Returns:
            Response data (JSON)
            
        Raises:
            Exception: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(
                method, url, timeout=self.timeout, **kwargs
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            raise Exception(f"Cannot connect to backend server at {self.base_url}")
        except requests.exceptions.Timeout:
            raise Exception(f"Request timeout after {self.timeout} seconds")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"HTTP error: {e.response.status_code} - {e.response.text}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {e}")
    
    # ==================== Health Check ====================
    
    def health_check(self) -> bool:
        """
        Check if backend is available
        
        Returns:
            True if backend is healthy, False otherwise
        """
        try:
            response = self._request("GET", "/health")
            self._connected = response.get("status") == "healthy"
            return self._connected
        except:
            self._connected = False
            return False
    
    def is_connected(self) -> bool:
        """Check if client is connected to backend"""
        return self._connected
    
    # ==================== Account Endpoints ====================
    
    def get_accounts(self) -> List[Dict]:
        """
        Get all accounts
        
        Returns:
            List of account dictionaries
        """
        return self._request("GET", "/accounts")
    
    def create_account(self, name: str, cookies_file: str) -> Dict:
        """
        Create new account
        
        Args:
            name: Account name
            cookies_file: Path to cookies file
            
        Returns:
            Created account data
        """
        return self._request("POST", "/accounts", json={
            "name": name,
            "cookies_file": cookies_file
        })
    
    def get_account(self, account_id: int) -> Dict:
        """
        Get account by ID
        
        Args:
            account_id: Account ID
            
        Returns:
            Account data
        """
        return self._request("GET", f"/accounts/{account_id}")
    
    def update_account(self, account_id: int, name: Optional[str] = None, 
                      cookies_file: Optional[str] = None) -> Dict:
        """
        Update account
        
        Args:
            account_id: Account ID
            name: New account name (optional)
            cookies_file: New cookies file path (optional)
            
        Returns:
            Updated account data
        """
        data = {}
        if name:
            data["name"] = name
        if cookies_file:
            data["cookies_file"] = cookies_file
        
        return self._request("PUT", f"/accounts/{account_id}", json=data)
    
    def delete_account(self, account_id: int) -> Dict:
        """
        Delete account
        
        Args:
            account_id: Account ID
            
        Returns:
            Deletion confirmation
        """
        return self._request("DELETE", f"/accounts/{account_id}")
    
    # ==================== Channel Endpoints ====================
    
    def get_channels(self, account_id: Optional[int] = None) -> List[Dict]:
        """
        Get channels
        
        Args:
            account_id: Filter by account ID (optional)
            
        Returns:
            List of channel dictionaries
        """
        params = {"account_id": account_id} if account_id else {}
        return self._request("GET", "/channels", params=params)
    
    def create_channel(self, account_id: int, url: str, 
                      channel_id: Optional[str] = None,
                      channel_name: Optional[str] = None) -> Dict:
        """
        Create channel
        
        Args:
            account_id: Account ID
            url: Channel URL
            channel_id: YouTube channel ID (optional)
            channel_name: Channel name (optional)
            
        Returns:
            Created channel data
        """
        data = {
            "account_id": account_id,
            "url": url
        }
        if channel_id:
            data["channel_id"] = channel_id
        if channel_name:
            data["channel_name"] = channel_name
        
        return self._request("POST", "/channels", json=data)
    
    def get_channel(self, channel_id: int) -> Dict:
        """
        Get channel by ID
        
        Args:
            channel_id: Channel ID
            
        Returns:
            Channel data
        """
        return self._request("GET", f"/channels/{channel_id}")
    
    def delete_channel(self, channel_id: int) -> Dict:
        """
        Delete channel
        
        Args:
            channel_id: Channel ID
            
        Returns:
            Deletion confirmation
        """
        return self._request("DELETE", f"/channels/{channel_id}")
    
    # ==================== Video Endpoints ====================
    
    def get_videos(self, channel_id: Optional[int] = None, 
                   limit: int = 100, skip: int = 0) -> List[Dict]:
        """
        Get videos
        
        Args:
            channel_id: Filter by channel ID (optional)
            limit: Maximum number of results
            skip: Number of results to skip
            
        Returns:
            List of video dictionaries
        """
        params = {"limit": limit, "skip": skip}
        if channel_id:
            params["channel_id"] = channel_id
        
        return self._request("GET", "/videos", params=params)
    
    def create_video(self, video_id: str, channel_id: Optional[int] = None,
                    title: Optional[str] = None) -> Dict:
        """
        Create video
        
        Args:
            video_id: YouTube video ID
            channel_id: Channel ID (optional)
            title: Video title (optional)
            
        Returns:
            Created video data
        """
        data = {"video_id": video_id}
        if channel_id:
            data["channel_id"] = channel_id
        if title:
            data["title"] = title
        
        return self._request("POST", "/videos", json=data)
    
    def create_videos_bulk(self, video_ids: List[str], 
                          channel_id: Optional[int] = None) -> Dict:
        """
        Bulk create videos
        
        Args:
            video_ids: List of YouTube video IDs
            channel_id: Channel ID (optional)
            
        Returns:
            Bulk creation result
        """
        return self._request("POST", "/videos/bulk", json={
            "video_ids": video_ids,
            "channel_id": channel_id
        })
    
    # ==================== Analytics Endpoints ====================
    
    def get_analytics(self, account_id: Optional[int] = None,
                     video_id: Optional[str] = None,
                     limit: int = 100, skip: int = 0) -> List[Dict]:
        """
        Get analytics data
        
        Args:
            account_id: Filter by account ID (optional)
            video_id: Filter by video ID (optional)
            limit: Maximum number of results
            skip: Number of results to skip
            
        Returns:
            List of analytics dictionaries
        """
        params = {"limit": limit, "skip": skip}
        if account_id:
            params["account_id"] = account_id
        if video_id:
            params["video_id"] = video_id
        
        return self._request("GET", "/analytics", params=params)
    
    def get_account_stats(self, account_id: int) -> Dict:
        """
        Get account statistics
        
        Args:
            account_id: Account ID
            
        Returns:
            Account statistics
        """
        return self._request("GET", f"/analytics/account/{account_id}/stats")
    
    # ==================== Utility Methods ====================
    
    def get_api_info(self) -> Dict:
        """
        Get API information
        
        Returns:
            API info dictionary
        """
        return self._request("GET", "/")
    
    def __repr__(self) -> str:
        status = "connected" if self._connected else "disconnected"
        return f"<BackendAPIClient(url='{self.base_url}', status='{status}')>"
