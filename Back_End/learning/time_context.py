"""
Time Context Extractor: Add time-context metadata to economic outcomes.

Phase 4 Step 5: Economic Time Awareness
- Captures temporal context for mission completions and opportunity normalizations
- Fields: hour_of_day, day_of_week, elapsed_time_sec
- Observability only (no scheduling logic or decision-making changes)
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional


def _parse_iso_timestamp(timestamp_str: str) -> Optional[datetime]:
    """Parse ISO format timestamp string to datetime object."""
    if not isinstance(timestamp_str, str):
        return None
    
    try:
        # Handle ISO format with or without timezone
        # Remove timezone info if present for simplicity
        if '+' in timestamp_str:
            timestamp_str = timestamp_str.split('+')[0]
        elif timestamp_str.endswith('Z'):
            timestamp_str = timestamp_str[:-1]
        
        # Parse the datetime string
        return datetime.fromisoformat(timestamp_str.replace('Z', ''))
    except (ValueError, TypeError):
        return None


def extract_time_context(
    timestamp_str: str,
    start_time_str: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extract time context metadata from a timestamp.
    
    Args:
        timestamp_str: ISO-format timestamp (e.g., "2026-02-07T14:50:49.146715+00:00")
        start_time_str: Optional ISO-format start timestamp for elapsed time calculation
    
    Returns:
        Dictionary with:
        - hour_of_day (0-23): Hour when outcome occurred
        - day_of_week (0-6): Day of week (0=Monday, 6=Sunday)
        - elapsed_time_sec: Seconds from mission start to completion/outcome
    """
    try:
        # Parse the outcome timestamp
        ts = _parse_iso_timestamp(timestamp_str)
        if ts is None:
            raise ValueError("Invalid timestamp format")
        
        time_context = {
            "hour_of_day": ts.hour,
            "day_of_week": ts.weekday(),  # 0=Monday, 6=Sunday
        }
        
        # Calculate elapsed time if start time provided
        if start_time_str:
            try:
                start_ts = _parse_iso_timestamp(start_time_str)
                if start_ts is None:
                    raise ValueError("Invalid start timestamp format")
                
                elapsed = ts - start_ts
                time_context["elapsed_time_sec"] = int(elapsed.total_seconds())
            except Exception:
                # If parsing fails, skip elapsed time
                time_context["elapsed_time_sec"] = None
        else:
            time_context["elapsed_time_sec"] = None
        
        return time_context
    
    except Exception as e:
        # Return safe defaults on error
        return {
            "hour_of_day": None,
            "day_of_week": None,
            "elapsed_time_sec": None
        }


def get_day_name(day_of_week: int) -> str:
    """Convert day_of_week (0-6) to day name."""
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    if 0 <= day_of_week <= 6:
        return days[day_of_week]
    return "Unknown"


def get_time_period(hour_of_day: int) -> str:
    """Categorize hour into time period."""
    if hour_of_day is None:
        return "Unknown"
    if 0 <= hour_of_day < 6:
        return "Night"
    elif 6 <= hour_of_day < 12:
        return "Morning"
    elif 12 <= hour_of_day < 18:
        return "Afternoon"
    else:
        return "Evening"


def is_business_hours(hour_of_day: int, day_of_week: int) -> bool:
    """Determine if time is during typical business hours (Mon-Fri, 9-16)."""
    if hour_of_day is None or day_of_week is None:
        return False
    # Monday=0, Friday=4; 9-16 (9 AM to 4 PM)
    return 0 <= day_of_week <= 4 and 9 <= hour_of_day < 17

