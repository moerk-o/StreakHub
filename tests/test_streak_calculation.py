"""Test StreakHub streak calculation with freezegun time manipulation."""

import pytest
from freezegun import freeze_time
from homeassistant.core import HomeAssistant


@pytest.mark.asyncio
async def test_streak_day_1(hass: HomeAssistant, basic_config_entry) -> None:
    """Test that on the start day, streak is 1."""
    basic_config_entry.add_to_hass(hass)

    # basic_config_entry has initial_date = "2025-01-01"
    with freeze_time("2025-01-01 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

    streak_sensor = hass.states.get("sensor.zucker_streak")
    assert streak_sensor is not None
    assert int(streak_sensor.state) == 1


@pytest.mark.asyncio
async def test_streak_day_5(hass: HomeAssistant, basic_config_entry) -> None:
    """Test that after 5 days, streak is 5."""
    basic_config_entry.add_to_hass(hass)

    # Start: 2025-01-01, today: 2025-01-05
    with freeze_time("2025-01-05 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

    streak_sensor = hass.states.get("sensor.zucker_streak")
    assert streak_sensor is not None
    assert int(streak_sensor.state) == 5


@pytest.mark.asyncio
async def test_streak_event_day_is_zero(hass: HomeAssistant, basic_config_entry) -> None:
    """Test that on the event day (after reset), streak is 0."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

        # Press the reset button (event happened today)
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.zucker_reset"},
            blocking=True,
        )
        await hass.async_block_till_done()

    # After event, streak should be 0
    streak_sensor = hass.states.get("sensor.zucker_streak")
    assert streak_sensor is not None
    assert int(streak_sensor.state) == 0


@pytest.mark.asyncio
async def test_streak_across_year_boundary(
    hass: HomeAssistant, config_entry_year_boundary
) -> None:
    """Test streak calculation across year boundary (Dec 30 -> Jan 2 = 4 days)."""
    config_entry_year_boundary.add_to_hass(hass)

    # initial_date = "2024-12-30", test on "2025-01-02"
    with freeze_time("2025-01-02 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(config_entry_year_boundary.entry_id)
        await hass.async_block_till_done()

    streak_sensor = hass.states.get("sensor.jahreswechsel_streak")
    assert streak_sensor is not None
    # Dec 30, 31, Jan 1, 2 = 4 days
    assert int(streak_sensor.state) == 4


@pytest.mark.asyncio
async def test_streak_across_leap_year(
    hass: HomeAssistant, config_entry_leap_year
) -> None:
    """Test streak calculation across Feb 28/29 in leap year."""
    config_entry_leap_year.add_to_hass(hass)

    # initial_date = "2024-02-29" (leap year)
    with freeze_time("2024-03-01 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(config_entry_leap_year.entry_id)
        await hass.async_block_till_done()

    streak_sensor = hass.states.get("sensor.schaltjahr_test_streak")
    assert streak_sensor is not None
    # Feb 29, March 1 = 2 days
    assert int(streak_sensor.state) == 2


@pytest.mark.asyncio
async def test_streak_very_long(hass: HomeAssistant, config_entry_long_streak) -> None:
    """Test that very long streaks (1000+ days) are calculated correctly."""
    config_entry_long_streak.add_to_hass(hass)

    # initial_date = "2020-01-01", test on "2025-01-01" (5 years later)
    with freeze_time("2025-01-01 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(config_entry_long_streak.entry_id)
        await hass.async_block_till_done()

    streak_sensor = hass.states.get("sensor.langer_streak_streak")
    assert streak_sensor is not None
    # 2020: 366 days (leap year)
    # 2021: 365 days
    # 2022: 365 days
    # 2023: 365 days
    # 2024: 366 days (leap year)
    # 2025-01-01: +1 day (inclusive)
    # Total: 366 + 365 + 365 + 365 + 366 + 1 = 1828 days
    assert int(streak_sensor.state) == 1828
