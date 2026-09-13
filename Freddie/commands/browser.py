"""
Browser Controller for Freddie
===============================
Handles web browser operations.
"""

import logging
import webbrowser
from typing import Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)


class BrowserController:
    """Controls web browser operations."""

    def __init__(self):
        # Common website URLs
        self.sites = {
            "google": "https://www.google.com",
            "youtube": "https://www.youtube.com",
            "github": "https://www.github.com",
            "reddit": "https://www.reddit.com",
            "twitter": "https://www.twitter.com",
            "facebook": "https://www.facebook.com",
            "instagram": "https://www.instagram.com",
            "linkedin": "https://www.linkedin.com",
            "amazon": "https://www.amazon.com",
            "netflix": "https://www.netflix.com",
            "stackoverflow": "https://stackoverflow.com",
        }

    def open_url(self, url: str) -> bool:
        """
        Open a URL in the default browser.

        Args:
            url: The URL to open

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure URL has protocol
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            webbrowser.open(url)
            logger.info(f"Opened URL: {url}")
            return True
        except Exception as e:
            logger.error(f"Failed to open URL '{url}': {e}")
            return False

    def open_site(self, site_name: str) -> bool:
        """
        Open a known website by name.

        Args:
            site_name: Name of the site (e.g., 'youtube', 'github')

        Returns:
            True if successful, False otherwise
        """
        site_name_lower = site_name.lower().strip()

        if site_name_lower in self.sites:
            return self.open_url(self.sites[site_name_lower])
        else:
            logger.warning(f"Unknown site: {site_name_lower}")
            return False

    def search_google(self, query: str) -> bool:
        """
        Search Google for a query.

        Args:
            query: Search query

        Returns:
            True if successful, False otherwise
        """
        try:
            encoded_query = quote(query)
            search_url = f"https://www.google.com/search?q={encoded_query}"
            return self.open_url(search_url)
        except Exception as e:
            logger.error(f"Failed to search Google for '{query}': {e}")
            return False

    def search_youtube(self, query: str) -> bool:
        """
        Search YouTube for a query.

        Args:
            query: Search query

        Returns:
            True if successful, False otherwise
        """
        try:
            encoded_query = quote(query)
            search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
            return self.open_url(search_url)
        except Exception as e:
            logger.error(f"Failed to search YouTube for '{query}': {e}")
            return False

    def search_github(self, query: str) -> bool:
        """
        Search GitHub for a query.

        Args:
            query: Search query

        Returns:
            True if successful, False otherwise
        """
        try:
            encoded_query = quote(query)
            search_url = f"https://github.com/search?q={encoded_query}"
            return self.open_url(search_url)
        except Exception as e:
            logger.error(f"Failed to search GitHub for '{query}': {e}")
            return False

    def add_site(self, name: str, url: str) -> None:
        """
        Add a custom site to the known sites list.

        Args:
            name: Name identifier for the site
            url: Full URL of the site
        """
        self.sites[name.lower()] = url
        logger.info(f"Added custom site: {name} -> {url}")

    def remove_site(self, name: str) -> bool:
        """
        Remove a site from the known sites list.

        Args:
            name: Name identifier for the site

        Returns:
            True if removed, False if not found
        """
        name_lower = name.lower()
        if name_lower in self.sites:
            del self.sites[name_lower]
            logger.info(f"Removed site: {name}")
            return True
        return False

    def get_known_sites(self) -> list:
        """Get list of known site names."""
        return list(self.sites.keys())


# Singleton instance
_browser_controller: Optional[BrowserController] = None


def get_browser_controller() -> BrowserController:
    """Get the singleton BrowserController instance."""
    global _browser_controller
    if _browser_controller is None:
        _browser_controller = BrowserController()
    return _browser_controller
