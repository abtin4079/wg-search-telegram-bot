"""Shared bot state for metrics and tracking."""

from datetime import datetime

# Global metrics tracking
metrics = {
    "checks_total": 0,
    "listings_found": 0,
    "errors": 0,
    "notifications_sent": 0,
}

# Bot start time for uptime tracking
bot_start_time = datetime.now()
