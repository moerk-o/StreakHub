"""Test StreakHub reset button functionality."""

import pytest
from freezegun import freeze_time
from homeassistant.core import HomeAssistant


@pytest.mark.asyncio
async def test_button_press_sets_streak_zero(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that pressing the button sets streak to 0 on event day."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

        # Before press: streak should be 10
        streak_sensor = hass.states.get("sensor.zucker_streak")
        assert int(streak_sensor.state) == 10

        # Press reset button
        await hass.services.async_call(
            "button", "press",
            {"entity_id": "button.zucker_reset"},
            blocking=True,
        )
        await hass.async_block_till_done()

        # After press: streak should be 0
        streak_sensor = hass.states.get("sensor.zucker_streak")
        assert int(streak_sensor.state) == 0


@pytest.mark.asyncio
async def test_button_press_new_streak_tomorrow(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that after button press, streak_start is set to event_day + 1."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

        # Press reset button on Jan 10
        await hass.services.async_call(
            "button", "press",
            {"entity_id": "button.zucker_reset"},
            blocking=True,
        )
        await hass.async_block_till_done()

        # streak_start should be Jan 11 (tomorrow)
        streak_sensor = hass.states.get("sensor.zucker_streak")
        assert streak_sensor.attributes.get("streak_start") == "2025-01-11"


@pytest.mark.asyncio
async def test_button_press_writes_history(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that button press writes old streak to history when > 0 days."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

        # Before press: no history
        rank_sensor = hass.states.get("sensor.zucker_rank")
        top_3_before = rank_sensor.attributes.get("top_3", [])
        # Only current streak in top_3
        assert len(top_3_before) == 1

        # Press reset button
        await hass.services.async_call(
            "button", "press",
            {"entity_id": "button.zucker_reset"},
            blocking=True,
        )
        await hass.async_block_till_done()

        # After press: history should have the 9-day streak
        # Per konzept.md: Button press on Jan 10 saves streak Jan 1-9 = 9 days
        rank_sensor = hass.states.get("sensor.zucker_rank")
        top_3_after = rank_sensor.attributes.get("top_3", [])
        # Now we have current (0) + history (9) = 2 entries
        # But 0-day streaks may or may not be included based on implementation
        assert len(top_3_after) >= 1

        # Find the 9-day streak in top_3
        days_in_top_3 = [entry.get("days") if isinstance(entry, dict) else entry[0]
                        for entry in top_3_after]
        assert 9 in days_in_top_3


@pytest.mark.asyncio
async def test_button_press_zero_day_streak_not_saved(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that double-click doesn't save 0-day streaks to history."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

        # First press: saves 10-day streak
        await hass.services.async_call(
            "button", "press",
            {"entity_id": "button.zucker_reset"},
            blocking=True,
        )
        await hass.async_block_till_done()

        # Second press: should not save 0-day streak
        await hass.services.async_call(
            "button", "press",
            {"entity_id": "button.zucker_reset"},
            blocking=True,
        )
        await hass.async_block_till_done()

        # Check coordinator data for history length
        coordinator = basic_config_entry.runtime_data
        history = coordinator.data.get("history", [])
        # Should only have 1 entry (the 9-day streak per konzept.md), not 2
        # Button press on Jan 10 saves streak Jan 1-9 = 9 days
        assert len(history) == 1
        assert history[0]["days"] == 9


@pytest.mark.asyncio
async def test_button_press_on_streak_start_day(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test button press on streak start day doesn't save 0-day streak."""
    basic_config_entry.add_to_hass(hass)

    # On the first day (streak_start = 2025-01-01), streak is 1 day
    with freeze_time("2025-01-01 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

        # Press on start day - streak is 1 day
        await hass.services.async_call(
            "button", "press",
            {"entity_id": "button.zucker_reset"},
            blocking=True,
        )
        await hass.async_block_till_done()

        # Check history - 0-day streak should NOT be saved
        # Per konzept.md: event_day = 1.1., old_streak_end = 31.12.
        # old_streak_days = (31.12. - 1.1.).days + 1 = 0 Tage → nicht gespeichert
        coordinator = basic_config_entry.runtime_data
        history = coordinator.data.get("history", [])
        assert len(history) == 0


@pytest.mark.asyncio
async def test_button_press_updates_top_3(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that top_3 attribute is updated after button press."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

        rank_sensor = hass.states.get("sensor.zucker_rank")
        top_3_before = rank_sensor.attributes.get("top_3", [])

        await hass.services.async_call(
            "button", "press",
            {"entity_id": "button.zucker_reset"},
            blocking=True,
        )
        await hass.async_block_till_done()

        rank_sensor = hass.states.get("sensor.zucker_rank")
        top_3_after = rank_sensor.attributes.get("top_3", [])

        # top_3 should be different after button press
        assert top_3_before != top_3_after


@pytest.mark.asyncio
async def test_button_press_consecutive_days(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test pressing button on consecutive days saves only first streak."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

        # Day 1 press: 10-day streak saved
        await hass.services.async_call(
            "button", "press",
            {"entity_id": "button.zucker_reset"},
            blocking=True,
        )
        await hass.async_block_till_done()

    # Move to next day
    with freeze_time("2025-01-11 12:00:00+00:00"):
        # Force coordinator refresh
        coordinator = basic_config_entry.runtime_data
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        # Day 2 press: 0-day streak (started today) should not be saved
        await hass.services.async_call(
            "button", "press",
            {"entity_id": "button.zucker_reset"},
            blocking=True,
        )
        await hass.async_block_till_done()

        # Check history
        history = coordinator.data.get("history", [])
        # Per konzept.md:
        # - First press on Jan 10: old_streak = Jan 1-9 = 9 days (saved)
        # - Second press on Jan 11: streak_start = Jan 11, event_day = Jan 11
        #   old_streak_end = Jan 10,
        #   old_streak_days = (10.1. - 11.1.).days + 1 = 0 (not saved)
        assert len(history) == 1
        assert history[0]["days"] == 9
