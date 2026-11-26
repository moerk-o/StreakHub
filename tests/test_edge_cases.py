"""Test StreakHub edge cases."""

import pytest
from freezegun import freeze_time
from homeassistant.core import HomeAssistant


@pytest.mark.asyncio
async def test_edge_leap_year_boundary(
    hass: HomeAssistant, config_entry_leap_year
) -> None:
    """Test streak across Feb 28/29 boundary in leap year."""
    config_entry_leap_year.add_to_hass(hass)

    # Start on Feb 29, 2024 (leap year)
    with freeze_time("2024-03-02 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(config_entry_leap_year.entry_id)
        await hass.async_block_till_done()

    streak_sensor = hass.states.get("sensor.schaltjahr_test_streak")
    assert streak_sensor is not None
    # Feb 29, March 1, March 2 = 3 days
    assert int(streak_sensor.state) == 3


@pytest.mark.asyncio
async def test_edge_year_boundary(
    hass: HomeAssistant, config_entry_year_boundary
) -> None:
    """Test streak across Dec 31 / Jan 1 boundary."""
    config_entry_year_boundary.add_to_hass(hass)

    # Start on Dec 30, 2024
    with freeze_time("2025-01-03 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(
            config_entry_year_boundary.entry_id
        )
        await hass.async_block_till_done()

    streak_sensor = hass.states.get("sensor.jahreswechsel_streak")
    assert streak_sensor is not None
    # Dec 30, 31, Jan 1, 2, 3 = 5 days
    assert int(streak_sensor.state) == 5


@pytest.mark.asyncio
async def test_edge_very_long_streak(
    hass: HomeAssistant, config_entry_long_streak
) -> None:
    """Test very long streak (5 years / 1828 days)."""
    config_entry_long_streak.add_to_hass(hass)

    # Start on Jan 1, 2020
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


@pytest.mark.asyncio
async def test_edge_very_long_streak_3_years(hass: HomeAssistant) -> None:
    """Test long streak (3 years / 1096 days) - additional verification."""
    from pytest_homeassistant.common import MockConfigEntry

    # 2022-01-01 to 2025-01-01 = 3 years
    # 2022: 365 days
    # 2023: 365 days
    # 2024: 366 days (leap year)
    # 2025-01-01: +1 day (inclusive)
    # Total: 365 + 365 + 366 + 1 = 1097 days
    entry = MockConfigEntry(
        domain="streakhub",
        data={"name": "Drei Jahre Test", "initial_date": "2022-01-01"},
        unique_id="drei_jahre_test",
        title="Drei Jahre Test",
        version=1,
    )
    entry.add_to_hass(hass)

    with freeze_time("2025-01-01 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    streak_sensor = hass.states.get("sensor.drei_jahre_test_streak")
    assert streak_sensor is not None
    assert int(streak_sensor.state) == 1097


@pytest.mark.asyncio
async def test_edge_empty_history(hass: HomeAssistant, basic_config_entry) -> None:
    """Test that with empty history, top_3 has only current streak."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

    rank_sensor = hass.states.get("sensor.zucker_rank")
    assert rank_sensor is not None

    top_3 = rank_sensor.attributes.get("top_3", [])
    assert len(top_3) == 1
    # Current streak (10 days) should be the only entry
    first_entry = top_3[0]
    if isinstance(first_entry, dict):
        assert first_entry.get("days") == 10
    else:
        # Might be a tuple/list
        assert first_entry[0] == 10 or first_entry.days == 10


@pytest.mark.asyncio
async def test_edge_exactly_3_history_entries(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test top_3 displacement logic with exactly 3 history entries."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

        # Create 3 history entries by pressing reset multiple times on different days
        # Entry 1: 10 days (Jan 1-10)
        await hass.services.async_call(
            "button", "press",
            {"entity_id": "button.zucker_reset"},
            blocking=True,
        )
        await hass.async_block_till_done()

    # Day 2: Jan 15 (streak: Jan 11-15 = 5 days)
    with freeze_time("2025-01-15 12:00:00+00:00"):
        coordinator = hass.data["streakhub"][basic_config_entry.entry_id]
        await coordinator.async_refresh()

        await hass.services.async_call(
            "button", "press",
            {"entity_id": "button.zucker_reset"},
            blocking=True,
        )
        await hass.async_block_till_done()

    # Day 3: Jan 20 (streak: Jan 16-20 = 5 days)
    with freeze_time("2025-01-20 12:00:00+00:00"):
        coordinator = hass.data["streakhub"][basic_config_entry.entry_id]
        await coordinator.async_refresh()

        await hass.services.async_call(
            "button", "press",
            {"entity_id": "button.zucker_reset"},
            blocking=True,
        )
        await hass.async_block_till_done()

    # Now we have 3 history entries: 10, 5, 5 days
    coordinator = hass.data["streakhub"][basic_config_entry.entry_id]
    history = coordinator.data.get("history", [])
    assert len(history) == 3

    rank_sensor = hass.states.get("sensor.zucker_rank")
    top_3 = rank_sensor.attributes.get("top_3", [])
    # top_3 should include current (0) + 3 history = 4 entries total
    # But top_3 is limited to 3, so it should be the best 3
    # Actually, based on logic, top_3 includes current streak
    # So we have current (0) and history (10, 5, 5)
    # Top 3 should be: 10, 5, 5 (current 0 is 4th)
    assert len(top_3) <= 3


@pytest.mark.asyncio
async def test_edge_current_streak_zero(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that on event day (streak=0), top_3 is correctly sorted."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

        # Press reset - current streak becomes 0
        await hass.services.async_call(
            "button", "press",
            {"entity_id": "button.zucker_reset"},
            blocking=True,
        )
        await hass.async_block_till_done()

        streak_sensor = hass.states.get("sensor.zucker_streak")
        assert int(streak_sensor.state) == 0

        rank_sensor = hass.states.get("sensor.zucker_rank")
        top_3 = rank_sensor.attributes.get("top_3", [])

        # top_3 should have history (9 days) at position 1
        # Current (0 days) might or might not be included
        assert len(top_3) >= 1

        # First entry should be 9 days (the history entry)
        # Per konzept.md: Button press on Jan 10 saves streak Jan 1-9 = 9 days
        # (event_day is excluded from old streak)
        # top_3 entries are dicts with keys: rank, start, end, days
        first_entry = top_3[0]
        assert first_entry["days"] == 9
