"""
File Controller for Freddie
============================
Handles file and folder operations.
"""

import logging
import os
import shutil
from pathlib import Path
from typing import Tuple, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class FileController:
    """Controls file and folder operations."""

    def __init__(self):
        self.home_dir = Path.home()
        self.desktop_dir = self.home_dir / "Desktop"
        self.documents_dir = self.home_dir / "Documents"
        self.downloads_dir = self.home_dir / "Downloads"

    def create_folder(self, name: str, location: str = None) -> Tuple[bool, str]:
        """
        Create a new folder.

        Args:
            name: Name of the folder
            location: Location to create folder (default: Desktop)

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if location:
                base_path = self._resolve_path(location)
            else:
                base_path = self.desktop_dir

            folder_path = base_path / name

            if folder_path.exists():
                return False, f"Folder '{name}' already exists"

            folder_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created folder: {folder_path}")
            return True, f"Created folder '{name}' at {base_path}"

        except Exception as e:
            logger.error(f"Failed to create folder: {e}")
            return False, f"Error creating folder: {str(e)}"

    def create_file(self, name: str, content: str = "", location: str = None) -> Tuple[bool, str]:
        """
        Create a new text file.

        Args:
            name: Name of the file
            content: Optional content to write
            location: Location to create file (default: Documents)

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if location:
                base_path = self._resolve_path(location)
            else:
                base_path = self.documents_dir

            file_path = base_path / name

            if file_path.exists():
                return False, f"File '{name}' already exists"

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"Created file: {file_path}")
            return True, f"Created file '{name}' at {base_path}"

        except Exception as e:
            logger.error(f"Failed to create file: {e}")
            return False, f"Error creating file: {str(e)}"

    def open_file(self, name: str, location: str = None) -> Tuple[bool, str]:
        """
        Open a file using the default application.

        Args:
            name: Name of the file
            location: Location of the file (default: Documents)

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if location:
                base_path = self._resolve_path(location)
            else:
                base_path = self.documents_dir

            file_path = base_path / name

            if not file_path.exists():
                return False, f"File '{name}' not found"

            # Open with default application
            if os.name == 'nt':
                os.startfile(str(file_path))
            else:
                os.system(f"xdg-open '{file_path}'")

            logger.info(f"Opened file: {file_path}")
            return True, f"Opening '{name}'"

        except Exception as e:
            logger.error(f"Failed to open file: {e}")
            return False, f"Error opening file: {str(e)}"

    def open_folder(self, path: str) -> Tuple[bool, str]:
        """
        Open a folder in file explorer.

        Args:
            path: Path to the folder

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            folder_path = self._resolve_path(path)

            if not folder_path.exists():
                return False, f"Folder '{path}' not found"

            if not folder_path.is_dir():
                return False, f"'{path}' is not a folder"

            # Open in file explorer
            if os.name == 'nt':
                os.startfile(str(folder_path))
            else:
                os.system(f"xdg-open '{folder_path}'")

            logger.info(f"Opened folder: {folder_path}")
            return True, f"Opening folder '{path}'"

        except Exception as e:
            logger.error(f"Failed to open folder: {e}")
            return False, f"Error opening folder: {str(e)}"

    def delete_file(self, name: str, location: str = None) -> Tuple[bool, str]:
        """
        Delete a file.

        Note: This requires confirmation in the main assistant.

        Args:
            name: Name of the file
            location: Location of the file (default: Documents)

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if location:
                base_path = self._resolve_path(location)
            else:
                base_path = self.documents_dir

            file_path = base_path / name

            if not file_path.exists():
                return False, f"File '{name}' not found"

            file_path.unlink()
            logger.info(f"Deleted file: {file_path}")
            return True, f"Deleted '{name}'"

        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return False, f"Error deleting file: {str(e)}"

    def delete_folder(self, name: str, location: str = None) -> Tuple[bool, str]:
        """
        Delete an empty folder.

        Note: This requires confirmation in the main assistant.

        Args:
            name: Name of the folder
            location: Location of the folder (default: Desktop)

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if location:
                base_path = self._resolve_path(location)
            else:
                base_path = self.desktop_dir

            folder_path = base_path / name

            if not folder_path.exists():
                return False, f"Folder '{name}' not found"

            if not folder_path.is_dir():
                return False, f"'{name}' is not a folder"

            # Use rmtree for non-empty folders (use with caution!)
            shutil.rmtree(folder_path)
            logger.info(f"Deleted folder: {folder_path}")
            return True, f"Deleted folder '{name}'"

        except Exception as e:
            logger.error(f"Failed to delete folder: {e}")
            return False, f"Error deleting folder: {str(e)}"

    def rename_file(self, old_name: str, new_name: str, location: str = None) -> Tuple[bool, str]:
        """
        Rename a file.

        Args:
            old_name: Current name of the file
            new_name: New name for the file
            location: Location of the file (default: Documents)

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if location:
                base_path = self._resolve_path(location)
            else:
                base_path = self.documents_dir

            old_path = base_path / old_name
            new_path = base_path / new_name

            if not old_path.exists():
                return False, f"File '{old_name}' not found"

            if new_path.exists():
                return False, f"A file named '{new_name}' already exists"

            old_path.rename(new_path)
            logger.info(f"Renamed file: {old_name} -> {new_name}")
            return True, f"Renamed '{old_name}' to '{new_name}'"

        except Exception as e:
            logger.error(f"Failed to rename file: {e}")
            return False, f"Error renaming file: {str(e)}"

    def copy_file(self, source: str, destination: str) -> Tuple[bool, str]:
        """
        Copy a file from source to destination.

        Args:
            source: Source file path
            destination: Destination path

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            source_path = self._resolve_path(source)
            dest_path = self._resolve_path(destination)

            if not source_path.exists():
                return False, f"Source file '{source}' not found"

            shutil.copy2(source_path, dest_path)
            logger.info(f"Copied file: {source} -> {destination}")
            return True, f"Copied '{source}' to '{destination}'"

        except Exception as e:
            logger.error(f"Failed to copy file: {e}")
            return False, f"Error copying file: {str(e)}"

    def move_file(self, source: str, destination: str) -> Tuple[bool, str]:
        """
        Move a file from source to destination.

        Args:
            source: Source file path
            destination: Destination path

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            source_path = self._resolve_path(source)
            dest_path = self._resolve_path(destination)

            if not source_path.exists():
                return False, f"Source file '{source}' not found"

            shutil.move(source_path, dest_path)
            logger.info(f"Moved file: {source} -> {destination}")
            return True, f"Moved '{source}' to '{destination}'"

        except Exception as e:
            logger.error(f"Failed to move file: {e}")
            return False, f"Error moving file: {str(e)}"

    def search_files(self, pattern: str, location: str = None) -> List[str]:
        """
        Search for files matching a pattern.

        Args:
            pattern: Search pattern (e.g., "*.txt")
            location: Location to search (default: Documents)

        Returns:
            List of matching file paths
        """
        try:
            if location:
                base_path = self._resolve_path(location)
            else:
                base_path = self.documents_dir

            matches = list(base_path.glob(f"**/{pattern}"))
            results = [str(m) for m in matches[:50]]  # Limit results
            logger.info(f"Found {len(results)} files matching '{pattern}'")
            return results

        except Exception as e:
            logger.error(f"Failed to search files: {e}")
            return []

    def _resolve_path(self, path_str: str) -> Path:
        """Resolve a path string to a Path object."""
        path_lower = path_str.lower()

        # Handle special locations
        if "desktop" in path_lower:
            return self.desktop_dir
        elif "document" in path_lower:
            return self.documents_dir
        elif "download" in path_lower:
            return self.downloads_dir
        elif "home" in path_lower or "~" in path_str:
            return self.home_dir
        else:
            # Return as absolute or relative path
            return Path(path_str)


# Singleton instance
_file_controller: Optional[FileController] = None


def get_file_controller() -> FileController:
    """Get the singleton FileController instance."""
    global _file_controller
    if _file_controller is None:
        _file_controller = FileController()
    return _file_controller
