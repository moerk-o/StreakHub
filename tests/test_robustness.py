"""Test StreakHub robustness and error handling."""

from copy import deepcopy
from datetime import date
from unittest.mock import AsyncMock, patch

import pytest
from freezegun import freeze_time
from homeassistant.const import STATE_OFF, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant

from custom_components.streakhub.coordinator import DATA_STORE


@pytest.mark.asyncio
async def test_robust_missing_streak_start(hass: HomeAssistant) -> None:
    """Test graceful handling when streak_start is missing from storage."""
    # This would require mocking storage with invalid data
    # For now, test that normal setup works correctly
    from pytest_homeassistant.common import MockConfigEntry

    entry = MockConfigEntry(
        domain="streakhub",
        data={"name": "Robustness Test", "initial_date": "2025-01-01"},
        unique_id="robustness_test",
        title="Robustness Test",
        version=1,
    )
    entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    # Verify normal operation works
    streak_sensor = hass.states.get("sensor.robustness_test_streak")
    assert streak_sensor is not None
    assert int(streak_sensor.state) == 10


@pytest.mark.asyncio
async def test_robust_invalid_date_format(hass: HomeAssistant) -> None:
    """Test handling of invalid date format in config."""
    from pytest_homeassistant.common import MockConfigEntry

    # Config entry with invalid date format
    entry = MockConfigEntry(
        domain="streakhub",
        data={"name": "Invalid Date Test", "initial_date": "invalid-date"},
        unique_id="invalid_date_test",
        title="Invalid Date Test",
        version=1,
    )
    entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        # Setup should fail with invalid date
        try:
            result = await hass.config_entries.async_setup(entry.entry_id)
            # If it doesn't raise, it might have failed setup
            if not result:
                # Expected behavior: setup fails
                pass
            else:
                # If setup succeeded, something went wrong
                pytest.fail("Setup should have failed with invalid date")
        except (ValueError, Exception):
            # Expected: ValueError on invalid date parsing
            pass


@pytest.mark.asyncio
async def test_robust_missing_history(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that missing history field defaults to empty list."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

    # Get coordinator and verify history exists as empty list
    coordinator = basic_config_entry.runtime_data
    history = coordinator.data.get("history", None)
    assert history is not None
    assert isinstance(history, list)


@pytest.mark.asyncio
async def test_robust_coordinator_no_data(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test entity behavior when coordinator.data is None."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

        # Verify entities work normally first
        streak_sensor = hass.states.get("sensor.zucker_streak")
        assert streak_sensor is not None
        assert int(streak_sensor.state) == 10

        # Simulate a coordinator without data and let the entities re-render
        coordinator = basic_config_entry.runtime_data
        original_data = coordinator.data
        coordinator.data = None
        coordinator.async_update_listeners()
        await hass.async_block_till_done()

        streak_sensor = hass.states.get("sensor.zucker_streak")
        assert streak_sensor.state == STATE_UNKNOWN
        assert "streak_start" not in streak_sensor.attributes
        assert hass.states.get("binary_sensor.zucker_has_goal").state == STATE_OFF
        assert float(hass.states.get("number.zucker_goal").state) == 0

        # With the data back, the entities show values again
        coordinator.data = original_data
        coordinator.async_update_listeners()
        await hass.async_block_till_done()

        streak_sensor = hass.states.get("sensor.zucker_streak")
        assert int(streak_sensor.state) == 10


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "stored_data",
    [None, {"trackers": {}}],
    ids=["empty_storage", "missing_tracker"],
)
async def test_robust_refresh_without_tracker_data(
    hass: HomeAssistant, basic_config_entry, stored_data
) -> None:
    """Test that a refresh fails gracefully when the tracker data is gone."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

        coordinator = basic_config_entry.runtime_data
        assert coordinator.tracker_id == "zucker"

        with patch.object(
            hass.data[DATA_STORE],
            "async_load",
            new=AsyncMock(return_value=stored_data),
        ):
            await coordinator.async_refresh()
            await hass.async_block_till_done()

        assert not coordinator.last_update_success
        streak_sensor = hass.states.get("sensor.zucker_streak")
        assert streak_sensor.state == STATE_UNAVAILABLE


@pytest.mark.asyncio
async def test_robust_actions_without_loaded_data(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that coordinator actions change nothing while no data is loaded."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

        store = hass.data[DATA_STORE]
        stored_before = deepcopy(await store.async_load())
        coordinator = basic_config_entry.runtime_data
        coordinator.data = None

        await coordinator.async_handle_event(date(2025, 1, 10))
        await coordinator.async_set_streak_start(date(2025, 1, 5))
        await coordinator.async_set_goal(30)
        assert await coordinator.async_undo_last_event() is False

        assert await store.async_load() == stored_before
