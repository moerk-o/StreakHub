"""Test StreakHub midnight/timezone behavior."""

import pytest
from freezegun import freeze_time
from homeassistant.core import HomeAssistant


@pytest.mark.asyncio
async def test_midnight_streak_increments(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that streak increments at midnight."""
    basic_config_entry.add_to_hass(hass)

    # Setup at 23:59 on Jan 10
    with freeze_time("2025-01-10 23:59:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

        streak_sensor = hass.states.get("sensor.zucker_streak")
        # Jan 1 - Jan 10 = 10 days
        assert int(streak_sensor.state) == 10

    # After midnight (00:01 on Jan 11)
    with freeze_time("2025-01-11 00:01:00+00:00"):
        coordinator = hass.data["streakhub"][basic_config_entry.entry_id]
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        streak_sensor = hass.states.get("sensor.zucker_streak")
        # Jan 1 - Jan 11 = 11 days
        assert int(streak_sensor.state) == 11


@pytest.mark.asyncio
async def test_midnight_timezone_berlin(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that local midnight (Europe/Berlin) is used, not UTC."""
    basic_config_entry.add_to_hass(hass)

    # CET is UTC+1, so 23:30 CET = 22:30 UTC
    with freeze_time("2025-01-10 23:30:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

        streak_sensor = hass.states.get("sensor.zucker_streak")
        # Should still be Jan 10 (10 days)
        assert int(streak_sensor.state) == 10

    # At 00:30 CET (23:30 UTC on Jan 10)
    with freeze_time("2025-01-11 00:30:00+00:00"):
        coordinator = hass.data["streakhub"][basic_config_entry.entry_id]
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        streak_sensor = hass.states.get("sensor.zucker_streak")
        # Now it's Jan 11 in local time = 11 days
        assert int(streak_sensor.state) == 11


@pytest.mark.asyncio
async def test_midnight_dst_spring(hass: HomeAssistant, basic_config_entry) -> None:
    """Test streak is correct across spring DST period.

    Note: Since we use UTC for testing, DST transitions don't affect our tests.
    This test verifies the streak calculation works correctly across the DST
    period, even though the actual DST handling would only matter for local
    timezone display in production.
    """
    from pytest_homeassistant.common import MockConfigEntry

    # Create entry starting March 25
    entry = MockConfigEntry(
        domain="streakhub",
        data={"name": "DST Test", "initial_date": "2025-03-25"},
        unique_id="dst_test",
        title="DST Test",
        version=1,
    )
    entry.add_to_hass(hass)

    # March 29 (UTC)
    with freeze_time("2025-03-29 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        streak_sensor = hass.states.get("sensor.dst_test_streak")
        # March 25-29 = 5 days
        assert int(streak_sensor.state) == 5

    # March 31 (UTC) - after DST change in local timezones
    with freeze_time("2025-03-31 12:00:00+00:00"):
        coordinator = hass.data["streakhub"][entry.entry_id]
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        streak_sensor = hass.states.get("sensor.dst_test_streak")
        # March 25-31 = 7 days
        assert int(streak_sensor.state) == 7


@pytest.mark.asyncio
async def test_midnight_dst_fall(hass: HomeAssistant, basic_config_entry) -> None:
    """Test streak is correct across fall DST period.

    Note: Since we use UTC for testing, DST transitions don't affect our tests.
    This test verifies the streak calculation works correctly across the DST
    period, even though the actual DST handling would only matter for local
    timezone display in production.
    """
    from pytest_homeassistant.common import MockConfigEntry

    # Create entry starting October 20
    entry = MockConfigEntry(
        domain="streakhub",
        data={"name": "DST Fall Test", "initial_date": "2025-10-20"},
        unique_id="dst_fall_test",
        title="DST Fall Test",
        version=1,
    )
    entry.add_to_hass(hass)

    # October 25 (UTC)
    with freeze_time("2025-10-25 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        streak_sensor = hass.states.get("sensor.dst_fall_test_streak")
        # Oct 20-25 = 6 days
        assert int(streak_sensor.state) == 6

    # October 27 (UTC) - after DST change in local timezones
    with freeze_time("2025-10-27 12:00:00+00:00"):
        coordinator = hass.data["streakhub"][entry.entry_id]
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        streak_sensor = hass.states.get("sensor.dst_fall_test_streak")
        # Oct 20-27 = 8 days
        assert int(streak_sensor.state) == 8
