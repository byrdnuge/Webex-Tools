"""
API utilities for interacting with the Cisco Webex API.
"""
import os
from typing import Any, Dict, List, Optional, Union

import requests
from rich.console import Console

console = Console()

class WebexAPI:
    """Client for interacting with the Cisco Webex API."""
    
    BASE_URL = "https://webexapis.com/v1"
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize the Webex API client.
        
        Args:
            token: The Webex API token. If not provided, it will be read from the
                  WEBEX_ACCESS_TOKEN environment variable.
        """
        self.token = token or os.environ.get("WEBEX_ACCESS_TOKEN")
        if not self.token:
            raise ValueError(
                "Webex API token not provided and WEBEX_ACCESS_TOKEN environment variable not set."
            )
        
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        })
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a GET request to the Webex API.
        
        Args:
            endpoint: The API endpoint to call (without the base URL).
            params: Optional query parameters.
            
        Returns:
            The JSON response as a dictionary.
            
        Raises:
            requests.HTTPError: If the request fails.
        """
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a POST request to the Webex API.
        
        Args:
            endpoint: The API endpoint to call (without the base URL).
            data: The data to send in the request body.
            
        Returns:
            The JSON response as a dictionary.
            
        Raises:
            requests.HTTPError: If the request fails.
        """
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()
    
    def put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a PUT request to the Webex API.
        
        Args:
            endpoint: The API endpoint to call (without the base URL).
            data: The data to send in the request body.
            
        Returns:
            The JSON response as a dictionary.
            
        Raises:
            requests.HTTPError: If the request fails.
        """
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        response = self.session.put(url, json=data)
        response.raise_for_status()
        return response.json()
    
    def delete(self, endpoint: str) -> None:
        """
        Make a DELETE request to the Webex API.
        
        Args:
            endpoint: The API endpoint to call (without the base URL).
            
        Raises:
            requests.HTTPError: If the request fails.
        """
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        response = self.session.delete(url)
        response.raise_for_status()
    
    def get_all_pages(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get all pages of results from a paginated API endpoint.
        
        Args:
            endpoint: The API endpoint to call (without the base URL).
            params: Optional query parameters.
            
        Returns:
            A list of all items across all pages.
            
        Raises:
            requests.HTTPError: If any request fails.
        """
        if params is None:
            params = {}
        
        all_items = []
        next_link = None
        
        # Get first page
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Add items from first page
        if "items" in data:
            all_items.extend(data["items"])
        
        # Check for Link header for pagination
        if "Link" in response.headers:
            links = response.headers["Link"].split(",")
            for link in links:
                if 'rel="next"' in link:
                    next_link = link.split(";")[0].strip("<>")
        
        # Get remaining pages
        while next_link:
            response = self.session.get(next_link)
            response.raise_for_status()
            data = response.json()
            
            if "items" in data:
                all_items.extend(data["items"])
            
            next_link = None
            if "Link" in response.headers:
                links = response.headers["Link"].split(",")
                for link in links:
                    if 'rel="next"' in link:
                        next_link = link.split(";")[0].strip("<>")
        
        return all_items
