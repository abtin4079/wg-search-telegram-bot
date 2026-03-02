"""Utility functions for file operations and messaging."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def load_last_seen(file_path: Path) -> str:
    """Load the last seen listing ID from file.
    
    Args:
        file_path: Path to the file storing the last seen listing ID
        
    Returns:
        The last seen listing ID, or empty string if file doesn't exist
    """
    try:
        return file_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        logger.debug(f"Last seen file not found: {file_path}")
        return ""
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return ""


def save_last_seen(listing_id: str, file_path: Path) -> bool:
    """Save the last seen listing ID to file.
    
    Args:
        listing_id: The listing ID to save
        file_path: Path to the file for storing the listing ID
        
    Returns:
        True if successful, False otherwise
    """
    try:
        file_path.write_text(listing_id, encoding="utf-8")
        logger.debug(f"Saved last_seen for {file_path.name}: {listing_id}")
        return True
    except Exception as e:
        logger.error(f"Error saving to {file_path}: {e}")
        return False
