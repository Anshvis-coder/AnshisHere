"""
Application Controller for Freddie
===================================
Handles opening and closing applications.
"""

import logging
import subprocess
import os
from typing import Tuple, Optional
from config import APP_PATHS

logger = logging.getLogger(__name__)


class AppController:
    """Controls application launching and management."""

    def __init__(self):
        self.app_paths = APP_PATHS.copy()
        self._running_apps: dict = {}  # Track running apps by name

    def open_application(self, app_name: str) -> Tuple[bool, str]:
        """
        Open an application by name.

        Args:
            app_name: Name of the application to open

        Returns:
            Tuple of (success: bool, message: str)
        """
        app_name_lower = app_name.lower().strip()

        # Map common names to configured apps
        app_mapping = {
            "chrome": "chrome",
            "google chrome": "chrome",
            "firefox": "firefox",
            "browser": "chrome",  # Default browser
            "edge": "edge",
            "notepad": "notepad",
            "text editor": "notepad",
            "calculator": "calculator",
            "calc": "calculator",
            "vscode": "vscode",
            "visual studio code": "vscode",
            "code": "vscode",
            "explorer": "file_explorer",
            "file explorer": "file_explorer",
            "folder": "file_explorer",
            "task manager": "task_manager",
            "settings": "settings",
            "control panel": "settings",
        }

        # Find the app key
        app_key = app_mapping.get(app_name_lower, app_name_lower)

        # Get the path for this app
        app_path = self.app_paths.get(app_key)

        if not app_path:
            # Try to find it in PATH
            try:
                # For Windows, try using 'start' command
                if os.name == 'nt':
                    subprocess.Popen(f"start {app_name_lower}", shell=True)
                    logger.info(f"Started application via shell: {app_name_lower}")
                    return True, f"Opening {app_name}"
                else:
                    # Linux/Mac fallback
                    subprocess.Popen([app_name_lower])
                    logger.info(f"Started application: {app_name_lower}")
                    return True, f"Opening {app_name}"
            except Exception as e:
                logger.error(f"Failed to start application '{app_name}': {e}")
                return False, f"Could not find or start '{app_name}'"

        try:
            # Expand environment variables
            expanded_path = os.path.expandvars(app_path)

            if os.name == 'nt':
                # Windows
                if app_path.startswith("ms-"):
                    # URI scheme (like ms-settings:)
                    os.startfile(expanded_path)
                else:
                    subprocess.Popen([expanded_path])
            else:
                # Linux/Mac
                subprocess.Popen([expanded_path])

            logger.info(f"Opened application: {app_name}")
            self._running_apps[app_key] = True
            return True, f"Opening {app_name}"

        except FileNotFoundError:
            logger.warning(f"Application not found: {app_path}")
            return False, f"'{app_name}' is not installed or path is incorrect"
        except Exception as e:
            logger.error(f"Error opening application '{app_name}': {e}")
            return False, f"Error opening '{app_name}': {str(e)}"

    def close_application(self, app_name: str) -> Tuple[bool, str]:
        """
        Close an application by name.

        Note: This is a simplified implementation. Proper app closing
        would require more sophisticated process management.

        Args:
            app_name: Name of the application to close

        Returns:
            Tuple of (success: bool, message: str)
        """
        app_name_lower = app_name.lower().strip()

        # Map to process names
        process_mapping = {
            "chrome": "chrome.exe",
            "firefox": "firefox.exe",
            "edge": "msedge.exe",
            "notepad": "notepad.exe",
            "calculator": "calculator.exe",
            "vscode": "code.exe",
            "explorer": "explorer.exe",
        }

        process_name = process_mapping.get(app_name_lower, f"{app_name_lower}.exe")

        try:
            if os.name == 'nt':
                # Windows - use taskkill
                subprocess.run(
                    ["taskkill", "/IM", process_name, "/T"],
                    capture_output=True,
                    timeout=5
                )
                logger.info(f"Closed application: {app_name}")
                return True, f"Closing {app_name}"
            else:
                # Linux/Mac - use pkill
                subprocess.run(
                    ["pkill", "-f", process_name],
                    capture_output=True,
                    timeout=5
                )
                logger.info(f"Closed application: {app_name}")
                return True, f"Closing {app_name}"

        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout closing application: {app_name}")
            return False, f"Timeout while trying to close '{app_name}'"
        except Exception as e:
            logger.error(f"Error closing application '{app_name}': {e}")
            return False, f"Could not close '{app_name}': {str(e)}"

    def get_running_apps(self) -> list:
        """Get list of tracked running applications."""
        return list(self._running_apps.keys())

    def add_app_path(self, app_name: str, path: str) -> None:
        """Add a custom application path."""
        self.app_paths[app_name.lower()] = path
        logger.info(f"Added app path: {app_name} -> {path}")

    def remove_app_path(self, app_name: str) -> None:
        """Remove an application path."""
        if app_name.lower() in self.app_paths:
            del self.app_paths[app_name.lower()]
            logger.info(f"Removed app path: {app_name}")


# Singleton instance
_app_controller: Optional[AppController] = None


def get_app_controller() -> AppController:
    """Get the singleton AppController instance."""
    global _app_controller
    if _app_controller is None:
        _app_controller = AppController()
    return _app_controller
