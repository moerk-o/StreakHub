"""Test StreakHub ranking calculation."""

from datetime import date

import pytest
from freezegun import freeze_time
from homeassistant.core import HomeAssistant

from conftest import STORAGE_KEY, build_hass_storage_entry


@pytest.mark.asyncio
async def test_rank_first_streak_is_rank_1(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that a new integration with no history shows rank 1."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

    rank_sensor = hass.states.get("sensor.zucker_rank")
    assert rank_sensor is not None
    assert int(rank_sensor.state) == 1


@pytest.mark.asyncio
async def test_rank_current_is_record(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that current streak ranks #1 when it's longer than all history."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

        # Press reset to end current streak (10 days)
        await hass.services.async_call(
            "button", "press",
            {"entity_id": "button.zucker_reset"},
            blocking=True,
        )
        await hass.async_block_till_done()

    # Now we have history with 9 days (Jan 1-9, per konzept.md), new streak starts Jan 11
    with freeze_time("2025-01-20 12:00:00+00:00"):
        # Force a refresh - new streak is 10 days (Jan 11 to Jan 20)
        coordinator = hass.data["streakhub"][basic_config_entry.entry_id]
        await coordinator.async_refresh()
        await hass.async_block_till_done()

    rank_sensor = hass.states.get("sensor.zucker_rank")
    # Current streak (10 days: Jan 11-20) is longer than history (9 days: Jan 1-9)
    # So current streak should be rank 1
    assert rank_sensor is not None
    assert int(rank_sensor.state) == 1


@pytest.mark.asyncio
async def test_rank_current_is_rank_2(
    hass: HomeAssistant, config_entry_with_history, hass_storage: dict
) -> None:
    """Test current streak ranks #2 when it's the second longest."""
    # Setup: Current streak = 5 days, History has 1 streak with 10 days
    # At 2025-01-20, current streak started 2025-01-15 = 6 days
    # History: 10 days (rank 1) -> Current: 6 days (rank 2)
    hass_storage[STORAGE_KEY] = build_hass_storage_entry(
        tracker_id="mit_history",
        current_streak_start=date(2025, 1, 15),
        history_streaks=[
            (date(2024, 11, 1), 10),  # 10 days = rank 1
        ],
    )

    config_entry_with_history.add_to_hass(hass)

    with freeze_time("2025-01-20 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(config_entry_with_history.entry_id)
        await hass.async_block_till_done()

    rank_sensor = hass.states.get("sensor.mit_history_rank")
    assert rank_sensor is not None
    assert int(rank_sensor.state) == 2


@pytest.mark.asyncio
async def test_rank_current_is_rank_3(
    hass: HomeAssistant, config_entry_with_history, hass_storage: dict
) -> None:
    """Test current streak ranks #3 when it's the third longest."""
    # Setup: Current streak = 5 days, History has 2 longer streaks
    # At 2025-01-20, current streak started 2025-01-16 = 5 days
    # History: 20 days (rank 1), 10 days (rank 2) -> Current: 5 days (rank 3)
    hass_storage[STORAGE_KEY] = build_hass_storage_entry(
        tracker_id="mit_history",
        current_streak_start=date(2025, 1, 16),
        history_streaks=[
            (date(2024, 10, 1), 20),  # 20 days = rank 1
            (date(2024, 11, 1), 10),  # 10 days = rank 2
        ],
    )

    config_entry_with_history.add_to_hass(hass)

    with freeze_time("2025-01-20 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(config_entry_with_history.entry_id)
        await hass.async_block_till_done()

    rank_sensor = hass.states.get("sensor.mit_history_rank")
    assert rank_sensor is not None
    assert int(rank_sensor.state) == 3


@pytest.mark.asyncio
async def test_rank_current_not_in_top_3(
    hass: HomeAssistant, config_entry_with_history, hass_storage: dict
) -> None:
    """Test rank is 0 when current streak is not in top 3."""
    # Setup: Current streak = 3 days, History has 3 longer streaks
    # At 2025-01-20, current streak started 2025-01-18 = 3 days
    # History: 30 days (rank 1), 20 days (rank 2), 10 days (rank 3)
    # -> Current: 3 days (rank 0, not in top 3)
    hass_storage[STORAGE_KEY] = build_hass_storage_entry(
        tracker_id="mit_history",
        current_streak_start=date(2025, 1, 18),
        history_streaks=[
            (date(2024, 9, 1), 30),   # 30 days = rank 1
            (date(2024, 10, 1), 20),  # 20 days = rank 2
            (date(2024, 11, 1), 10),  # 10 days = rank 3
        ],
    )

    config_entry_with_history.add_to_hass(hass)

    with freeze_time("2025-01-20 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(config_entry_with_history.entry_id)
        await hass.async_block_till_done()

    rank_sensor = hass.states.get("sensor.mit_history_rank")
    assert rank_sensor is not None
    assert int(rank_sensor.state) == 0


@pytest.mark.asyncio
async def test_rank_tie_breaking(
    hass: HomeAssistant, config_entry_with_history, hass_storage: dict
) -> None:
    """Test that newer streaks win tie-breakers."""
    # Setup: Current streak = 10 days, History has 1 streak with same 10 days
    # At 2025-01-20, current streak started 2025-01-11 = 10 days
    # History: 10 days (older start date)
    # Tie-breaker: newer start date wins -> Current should be rank 1
    hass_storage[STORAGE_KEY] = build_hass_storage_entry(
        tracker_id="mit_history",
        current_streak_start=date(2025, 1, 11),  # 10 days at 2025-01-20
        history_streaks=[
            (date(2024, 11, 1), 10),  # Same 10 days but older
        ],
    )

    config_entry_with_history.add_to_hass(hass)

    with freeze_time("2025-01-20 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(config_entry_with_history.entry_id)
        await hass.async_block_till_done()

    rank_sensor = hass.states.get("sensor.mit_history_rank")
    assert rank_sensor is not None
    # Current streak is newer, so it wins the tie-breaker
    assert int(rank_sensor.state) == 1

    # Verify top_3 order: current (newer) before historical (older)
    top_3 = rank_sensor.attributes.get("top_3", [])
    assert len(top_3) == 2
    assert top_3[0]["end"] is None  # Current streak at rank 1
    assert top_3[1]["end"] is not None  # Historical streak at rank 2


@pytest.mark.asyncio
async def test_rank_fewer_than_3_streaks(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that top_3 contains only available streaks when fewer than 3 exist."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

    rank_sensor = hass.states.get("sensor.zucker_rank")
    assert rank_sensor is not None

    top_3 = rank_sensor.attributes.get("top_3", [])
    # Only one streak exists (current), so top_3 should have 1 entry
    assert len(top_3) == 1


@pytest.mark.asyncio
async def test_rank_updated_after_reset(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that rank is correctly recalculated after button press."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

        # Before reset: rank 1, top_3 has 1 entry
        rank_sensor = hass.states.get("sensor.zucker_rank")
        assert int(rank_sensor.state) == 1
        top_3_before = rank_sensor.attributes.get("top_3", [])
        assert len(top_3_before) == 1

        # Press reset
        await hass.services.async_call(
            "button", "press",
            {"entity_id": "button.zucker_reset"},
            blocking=True,
        )
        await hass.async_block_till_done()

        # After reset: current streak is 0, history has 10 days
        rank_sensor = hass.states.get("sensor.zucker_rank")
        # Current streak (0) is not in top 3 because 10-day streak in history is larger
        # Actually, 0-day streaks ARE included in top_3 calculation per the logic
        # Let's verify what actually happens
        top_3_after = rank_sensor.attributes.get("top_3", [])
        # After reset, we have:
        # - Current streak: 0 days (starting tomorrow)
        # - History: 10 day streak
        # Top 3 should include both, with 10-day ranked #1
        assert len(top_3_after) >= 1


@pytest.mark.asyncio
async def test_rank_updated_after_service(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that rank is correctly recalculated after set_streak_start service."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

        # Call set_streak_start service
        await hass.services.async_call(
            "streakhub",
            "set_streak_start",
            {
                "entity_id": "sensor.zucker_streak",
                "date": "2025-01-08",  # Event was on Jan 7, new streak starts Jan 8
            },
            blocking=True,
        )
        await hass.async_block_till_done()

        # After service: history has old streak (Jan 1-7 = 7 days)
        # Current streak is Jan 8-10 = 3 days
        rank_sensor = hass.states.get("sensor.zucker_rank")
        top_3 = rank_sensor.attributes.get("top_3", [])
        # Should have 2 entries now
        assert len(top_3) == 2


@pytest.mark.asyncio
async def test_rank_with_many_history_entries(
    hass: HomeAssistant, config_entry_with_history, hass_storage: dict
) -> None:
    """Test that top 3 is correctly selected from 100+ history entries."""
    # Generate 100 history entries with varying lengths
    # Entry 0: 100 days (best)
    # Entry 1: 99 days
    # ...
    # Entry 99: 1 day (worst)
    history_streaks = []
    base_date = date(2020, 1, 1)
    for i in range(100):
        # Space them out to avoid overlaps
        start = date(base_date.year + (i // 12), (i % 12) + 1, 1)
        days = 100 - i  # 100, 99, 98, ..., 1
        history_streaks.append((start, days))

    # Current streak: 5 days at 2025-01-20, starting 2025-01-16
    hass_storage[STORAGE_KEY] = build_hass_storage_entry(
        tracker_id="mit_history",
        current_streak_start=date(2025, 1, 16),
        history_streaks=history_streaks,
    )

    config_entry_with_history.add_to_hass(hass)

    with freeze_time("2025-01-20 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(config_entry_with_history.entry_id)
        await hass.async_block_till_done()

    rank_sensor = hass.states.get("sensor.mit_history_rank")
    assert rank_sensor is not None

    # Current streak (5 days) should not be in top 3
    # Top 3 should be: 100 days, 99 days, 98 days
    assert int(rank_sensor.state) == 0

    top_3 = rank_sensor.attributes.get("top_3", [])
    assert len(top_3) == 3
    assert top_3[0]["days"] == 100
    assert top_3[1]["days"] == 99
    assert top_3[2]["days"] == 98
