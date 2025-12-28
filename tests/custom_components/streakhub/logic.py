"""Pure functions for streak calculation logic.

This module contains all core calculation logic as pure functions.
No I/O, no side effects, no Home Assistant dependencies.
All functions take `today` as a parameter for deterministic behavior.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import TypedDict


class HistoryEntry(TypedDict):
    """A completed streak in history."""

    start: str  # ISO 8601 date string
    end: str  # ISO 8601 date string
    days: int


class TrackerData(TypedDict):
    """Data structure for a single tracker."""

    streak_start: str  # ISO 8601 date string
    history: list[HistoryEntry]


class Top3Entry(TypedDict):
    """An entry in the top 3 ranking."""

    rank: int
    start: str  # ISO 8601 date string
    end: str | None  # None = current streak (still running)
    days: int


class StorageData(TypedDict):
    """Root storage data structure."""

    trackers: dict[str, TrackerData]


def calculate_streak(streak_start: date, today: date) -> int:
    """Calculate current streak value in days.

    The streak counts the days WITHOUT the event. The day of the event
    (button press) belongs to NO streak.

    Args:
        streak_start: First day of the current streak (first day WITHOUT event).
        today: The current date.

    Returns:
        0 if today < streak_start (we are on event day).
        Otherwise returns the number of days since streak_start (inclusive).

    Examples:
        >>> calculate_streak(date(2025, 1, 15), date(2025, 1, 15))
        1
        >>> calculate_streak(date(2025, 1, 15), date(2025, 1, 17))
        3
        >>> calculate_streak(date(2025, 1, 16), date(2025, 1, 15))  # Event day
        0
    """
    if today < streak_start:
        return 0
    return (today - streak_start).days + 1


def calculate_top_3(
    streak_start: date,
    history: list[HistoryEntry],
    today: date,
) -> list[Top3Entry]:
    """Calculate top 3 streaks from history and current streak.

    Sorting rules:
    1. Primary: Number of days (descending, more days = better)
    2. Secondary: Start date (descending, newer = better on tie)

    Args:
        streak_start: First day of the current streak.
        history: List of completed streaks.
        today: The current date.

    Returns:
        List of up to 3 entries, sorted by days (descending).
        Current streak has end=None.

    Examples:
        >>> calculate_top_3(date(2025, 1, 20), [], date(2025, 1, 25))
        [{'rank': 1, 'start': '2025-01-20', 'end': None, 'days': 6}]
    """
    current_streak_days = calculate_streak(streak_start, today)

    # Collect all streaks
    all_streaks: list[Top3Entry] = []

    # Add history entries
    for h in history:
        all_streaks.append(
            Top3Entry(
                rank=0,
                start=h["start"],
                end=h["end"],
                days=h["days"],
            )
        )

    # Add current streak (end=None means "still running")
    all_streaks.append(
        Top3Entry(
            rank=0,
            start=streak_start.isoformat(),
            end=None,
            days=current_streak_days,
        )
    )

    # Sort by days (descending), then by start date (descending/newer first)
    top_3 = sorted(
        all_streaks,
        key=lambda x: (x["days"], x["start"]),
        reverse=True,
    )[:3]

    # Assign ranks
    for i, streak in enumerate(top_3):
        streak["rank"] = i + 1

    return top_3


def calculate_rank(top_3: list[Top3Entry]) -> int:
    """Get rank of current streak from top 3 list.

    Args:
        top_3: The top 3 list from calculate_top_3().

    Returns:
        1, 2, or 3 if current streak is in top 3.
        0 if current streak is not in top 3.

    Examples:
        >>> top_3 = [{'rank': 1, 'start': '2025-01-20', 'end': None, 'days': 10}]
        >>> calculate_rank(top_3)
        1
    """
    for streak in top_3:
        if streak["end"] is None:  # Current streak marker
            return streak["rank"]
    return 0


def process_event(
    tracker_data: TrackerData,
    event_day: date,
) -> tuple[TrackerData, HistoryEntry | None]:
    """Process a button press / event.

    When the button is pressed on day X:
    - Event day (day WITH event): X
    - Last day of old streak: X - 1
    - First day of new streak: X + 1
    - Streak value on event day: 0

    Args:
        tracker_data: Current tracker data (not mutated).
        event_day: The day the event occurred.

    Returns:
        Tuple of:
        - Updated TrackerData with new streak_start
        - HistoryEntry if old streak had days > 0, else None

    Note:
        Does NOT mutate input; returns new objects.

    Examples:
        >>> data = {'streak_start': '2025-01-01', 'history': []}
        >>> new_data, entry = process_event(data, date(2025, 1, 14))
        >>> new_data['streak_start']
        '2025-01-15'
        >>> entry['days']
        13
    """
    old_start = date.fromisoformat(tracker_data["streak_start"])
    old_streak_end = event_day - timedelta(days=1)
    new_streak_start = event_day + timedelta(days=1)

    # Calculate old streak duration
    old_streak_days = (old_streak_end - old_start).days + 1

    # Create history entry only if streak had positive days
    history_entry: HistoryEntry | None = None
    if old_streak_days > 0:
        history_entry = HistoryEntry(
            start=tracker_data["streak_start"],
            end=old_streak_end.isoformat(),
            days=old_streak_days,
        )

    # Create new tracker data (immutable update)
    new_history = list(tracker_data["history"])
    if history_entry is not None:
        new_history.append(history_entry)

    new_tracker_data = TrackerData(
        streak_start=new_streak_start.isoformat(),
        history=new_history,
    )

    return new_tracker_data, history_entry


def validate_set_streak_start(
    current_start: date,
    new_start: date,
    today: date,
) -> str | None:
    """Validate parameters for set_streak_start service.

    Args:
        current_start: Current streak start date.
        new_start: Requested new streak start date.
        today: The current date.

    Returns:
        None if valid.
        Translation key string if invalid:
        - "date_in_future": new_start is in the future
        - "date_before_streak_start": new_start <= current_start

    Examples:
        >>> validate_set_streak_start(date(2025, 1, 10), date(2025, 1, 15), date(2025, 1, 20))
        >>> validate_set_streak_start(date(2025, 1, 10), date(2025, 1, 25), date(2025, 1, 20))
        'date_in_future'
    """
    # Check: new_start must not be in the future
    # Maximum allowed: today + 1 (meaning event was today)
    max_allowed = today + timedelta(days=1)
    if new_start > max_allowed:
        return "date_in_future"

    # Check: new_start must be after current streak_start
    if new_start <= current_start:
        return "date_before_streak_start"

    return None


def process_set_streak_start(
    tracker_data: TrackerData,
    new_start: date,
) -> tuple[TrackerData, HistoryEntry | None]:
    """Process set_streak_start service call.

    This is used for missed button presses. The new_start is the first day
    WITHOUT the event, meaning the event happened on new_start - 1.

    Args:
        tracker_data: Current tracker data (not mutated).
        new_start: The new streak start date (first day WITHOUT event).

    Returns:
        Same as process_event().

    Note:
        Validation should be done by caller using validate_set_streak_start().

    Examples:
        >>> data = {'streak_start': '2025-01-20', 'history': []}
        >>> new_data, entry = process_set_streak_start(data, date(2025, 1, 25))
        >>> new_data['streak_start']
        '2025-01-25'
        >>> entry['days']
        4
    """
    # The event day is the day before new_start
    event_day = new_start - timedelta(days=1)
    return process_event(tracker_data, event_day)


def create_initial_tracker_data(initial_date: date) -> TrackerData:
    """Create initial tracker data for a new tracker.

    Args:
        initial_date: The initial streak start date.

    Returns:
        New TrackerData with empty history.
    """
    return TrackerData(
        streak_start=initial_date.isoformat(),
        history=[],
    )


def create_initial_storage_data() -> StorageData:
    """Create initial empty storage data.

    Returns:
        New StorageData with empty trackers dict.
    """
    return StorageData(trackers={})
