"""Common test fixtures for StreakHub integration tests."""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

# Add tests directory to Python path
tests_dir = Path(__file__).parent
if str(tests_dir) not in sys.path:
    sys.path.insert(0, str(tests_dir))

# Use pytest-homeassistant-custom-component plugin
pytest_plugins = "pytest_homeassistant_custom_component"

# Extend custom_components.__path__ to include our test custom_components directory
# This is required because pytest-homeassistant-custom-component provides its own
# custom_components module, so we need to add our directory to its search path
import custom_components

custom_components_dir = tests_dir / "custom_components"
if str(custom_components_dir) not in custom_components.__path__:
    custom_components.__path__.insert(0, str(custom_components_dir))


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable loading of custom integrations in Home Assistant."""
    return None


@pytest.fixture(autouse=True)
async def set_utc(hass: Any) -> None:
    """Set timezone to UTC for all tests.

    This is critical for consistent behavior with freezegun.
    Home Assistant's dt_util.now() uses DEFAULT_TIME_ZONE internally,
    which must match the timezone used in freeze_time() calls.

    All freeze_time() calls MUST use UTC (+00:00 or Z).
    """
    await hass.config.async_set_time_zone("UTC")


# =============================================================================
# Config Entry Fixtures
# =============================================================================


@pytest.fixture
def basic_config_entry_data() -> dict[str, Any]:
    """Return basic config entry data."""
    return {
        "name": "Zucker",
        "initial_date": "2025-01-01",
    }


@pytest.fixture
def basic_config_entry(basic_config_entry_data: dict[str, Any]) -> Any:
    """Create a basic config entry for testing."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        domain="streakhub",
        data=basic_config_entry_data,
        unique_id="zucker",
        title="Zucker",
        version=1,
    )


@pytest.fixture
def config_entry_without_date() -> Any:
    """Create a config entry without initial_date (should default to today)."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        domain="streakhub",
        data={
            "name": "Test Tracker",
        },
        unique_id="test_tracker",
        title="Test Tracker",
        version=1,
    )


@pytest.fixture
def config_entry_with_history() -> Any:
    """Create a config entry with pre-existing history data in storage."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        domain="streakhub",
        data={
            "name": "Mit History",
            "initial_date": "2025-01-15",
        },
        unique_id="mit_history",
        title="Mit History",
        version=1,
    )


# =============================================================================
# Edge Case Fixtures
# =============================================================================


@pytest.fixture
def config_entry_leap_year() -> Any:
    """Config entry starting on Feb 29 (leap year)."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        domain="streakhub",
        data={
            "name": "Schaltjahr Test",
            "initial_date": "2024-02-29",
        },
        unique_id="schaltjahr_test",
        title="Schaltjahr Test",
        version=1,
    )


@pytest.fixture
def config_entry_year_boundary() -> Any:
    """Config entry crossing year boundary."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        domain="streakhub",
        data={
            "name": "Jahreswechsel",
            "initial_date": "2024-12-30",
        },
        unique_id="jahreswechsel",
        title="Jahreswechsel",
        version=1,
    )


@pytest.fixture
def config_entry_long_streak() -> Any:
    """Config entry for testing very long streaks."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        domain="streakhub",
        data={
            "name": "Langer Streak",
            "initial_date": "2020-01-01",
        },
        unique_id="langer_streak",
        title="Langer Streak",
        version=1,
    )


# =============================================================================
# Storage Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_storage_data_empty() -> dict[str, Any]:
    """Return empty storage data structure."""
    return {"trackers": {}}


@pytest.fixture
def mock_storage_data_with_history() -> dict[str, Any]:
    """Return storage data with existing history."""
    return {
        "trackers": {
            "mit_history": {
                "streak_start": "2025-01-15",
                "history": [
                    {"start": "2024-11-01", "end": "2024-11-10", "days": 10},
                    {"start": "2024-12-01", "end": "2024-12-25", "days": 25},
                ],
            }
        }
    }


@pytest.fixture
def mock_storage_data_multiple_trackers() -> dict[str, Any]:
    """Return storage data with multiple trackers."""
    return {
        "trackers": {
            "zucker": {
                "streak_start": "2025-01-01",
                "history": [],
            },
            "sport": {
                "streak_start": "2025-01-10",
                "history": [
                    {"start": "2024-01-01", "end": "2024-03-31", "days": 91},
                ],
            },
        }
    }


# =============================================================================
# Helper Functions
# =============================================================================


def get_date_from_state(state: str) -> str:
    """Extract ISO date string from state value.

    Handles both plain date strings and datetime strings.
    """
    if "T" in state:
        return state.split("T")[0]
    return state


# =============================================================================
# Storage Data Generator
# =============================================================================


def build_storage_data(
    tracker_id: str,
    current_streak_start: date,
    history_streaks: list[tuple[date, int]] | None = None,
    last_event_date: date | None = None,
    goal: int = 0,
) -> dict[str, Any]:
    """Generate storage data for hass_storage fixture.

    This function creates properly formatted storage data that can be used
    with the hass_storage fixture to pre-populate history for tests.

    Args:
        tracker_id: Tracker ID (e.g., "mit_history", must match config entry unique_id)
        current_streak_start: Start date of the current streak
        history_streaks: List of (start_date, days) tuples for historical streaks.
                        The end date is calculated as start_date + days - 1.
        last_event_date: Date of the last event (for undo functionality).
                        If set, undo is possible. If None, undo is not possible.
        goal: Streak goal in days (0 = no goal, >0 = goal in days)

    Returns:
        Dict structure for hass_storage["streakhub.streakhub"]["data"]

    Example:
        >>> data = build_storage_data(
        ...     tracker_id="test_tracker",
        ...     current_streak_start=date(2025, 1, 20),
        ...     history_streaks=[
        ...         (date(2024, 11, 1), 30),  # 30-day streak
        ...         (date(2024, 12, 10), 20), # 20-day streak
        ...     ],
        ...     last_event_date=date(2025, 1, 19),  # Event that ended the last streak
        ...     goal=100,  # 100-day goal
        ... )
        >>> hass_storage["streakhub.streakhub"] = {
        ...     "version": 1,
        ...     "data": data,
        ... }
    """
    history: list[dict[str, Any]] = []

    if history_streaks:
        for start, days in history_streaks:
            end = start + timedelta(days=days - 1)
            history.append({
                "start": start.isoformat(),
                "end": end.isoformat(),
                "days": days,
            })

    return {
        "trackers": {
            tracker_id: {
                "streak_start": current_streak_start.isoformat(),
                "history": history,
                "last_event_date": last_event_date.isoformat() if last_event_date else None,
                "goal": goal,
            }
        }
    }


def build_hass_storage_entry(
    tracker_id: str,
    current_streak_start: date,
    history_streaks: list[tuple[date, int]] | None = None,
    last_event_date: date | None = None,
    goal: int = 0,
    version: int = 1,
) -> dict[str, Any]:
    """Build a complete hass_storage entry for streakhub.

    Convenience wrapper around build_storage_data that includes the version
    and proper structure for direct use with hass_storage fixture.

    Args:
        tracker_id: Tracker ID (must match config entry unique_id)
        current_streak_start: Start date of the current streak
        history_streaks: List of (start_date, days) tuples for historical streaks
        last_event_date: Date of the last event (for undo functionality)
        goal: Streak goal in days (0 = no goal, >0 = goal in days)
        version: Storage version (default: 1)

    Returns:
        Complete hass_storage entry dict with "version" and "data" keys.

    Example:
        >>> hass_storage["streakhub"] = build_hass_storage_entry(
        ...     tracker_id="test_tracker",
        ...     current_streak_start=date(2025, 1, 20),
        ...     history_streaks=[(date(2024, 11, 1), 30)],
        ...     last_event_date=date(2025, 1, 19),
        ...     goal=100,
        ... )
    """
    return {
        "version": version,
        "data": build_storage_data(
            tracker_id=tracker_id,
            current_streak_start=current_streak_start,
            history_streaks=history_streaks,
            last_event_date=last_event_date,
            goal=goal,
        ),
    }


# Storage key constant for tests
STORAGE_KEY = "streakhub"
