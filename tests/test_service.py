"""Test StreakHub set_streak_start service."""

import pytest
from freezegun import freeze_time
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError


@pytest.mark.asyncio
async def test_service_valid_date(hass: HomeAssistant, basic_config_entry) -> None:
    """Test that service accepts valid date and updates streak start."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

        # Call service to set new streak start
        await hass.services.async_call(
            "streakhub",
            "set_streak_start",
            {
                "entity_id": "sensor.zucker_streak",
                "date": "2025-01-08",
            },
            blocking=True,
        )
        await hass.async_block_till_done()

        # Verify streak_start changed
        streak_sensor = hass.states.get("sensor.zucker_streak")
        assert streak_sensor.attributes.get("streak_start") == "2025-01-08"
        # New streak: Jan 8-10 = 3 days
        assert int(streak_sensor.state) == 3


@pytest.mark.asyncio
async def test_service_history_correct(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that service correctly saves old streak to history."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

        # Initial: streak start = Jan 1, current streak = 10 days
        await hass.services.async_call(
            "streakhub",
            "set_streak_start",
            {
                "entity_id": "sensor.zucker_streak",
                "date": "2025-01-08",  # Event was Jan 7
            },
            blocking=True,
        )
        await hass.async_block_till_done()

        # Check history
        coordinator = hass.data["streakhub"][basic_config_entry.entry_id]
        history = coordinator.data.get("history", [])
        assert len(history) == 1
        # Per konzept.md: set_streak_start(2025-01-08) means event was Jan 7
        # event_day = Jan 7, old_streak_end = Jan 6
        # Old streak: Jan 1 to Jan 6 = 6 days
        assert history[0]["start"] == "2025-01-01"
        assert history[0]["end"] == "2025-01-06"
        assert history[0]["days"] == 6


@pytest.mark.asyncio
async def test_service_date_tomorrow(hass: HomeAssistant, basic_config_entry) -> None:
    """Test that tomorrow's date is allowed (event happened today)."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

        # Tomorrow = Jan 11
        await hass.services.async_call(
            "streakhub",
            "set_streak_start",
            {
                "entity_id": "sensor.zucker_streak",
                "date": "2025-01-11",  # Event was today (Jan 10)
            },
            blocking=True,
        )
        await hass.async_block_till_done()

        streak_sensor = hass.states.get("sensor.zucker_streak")
        assert streak_sensor.attributes.get("streak_start") == "2025-01-11"


@pytest.mark.asyncio
async def test_service_date_today(hass: HomeAssistant, basic_config_entry) -> None:
    """Test that today's date is allowed (event was yesterday)."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

        # Today = Jan 10
        await hass.services.async_call(
            "streakhub",
            "set_streak_start",
            {
                "entity_id": "sensor.zucker_streak",
                "date": "2025-01-10",  # Event was yesterday (Jan 9)
            },
            blocking=True,
        )
        await hass.async_block_till_done()

        streak_sensor = hass.states.get("sensor.zucker_streak")
        assert streak_sensor.attributes.get("streak_start") == "2025-01-10"


@pytest.mark.asyncio
async def test_service_date_in_past(hass: HomeAssistant, basic_config_entry) -> None:
    """Test that past date is allowed (forgotten event)."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

        # Past date = Jan 5
        await hass.services.async_call(
            "streakhub",
            "set_streak_start",
            {
                "entity_id": "sensor.zucker_streak",
                "date": "2025-01-05",
            },
            blocking=True,
        )
        await hass.async_block_till_done()

        streak_sensor = hass.states.get("sensor.zucker_streak")
        assert streak_sensor.attributes.get("streak_start") == "2025-01-05"


@pytest.mark.asyncio
async def test_service_date_day_after_tomorrow(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that date after tomorrow is rejected."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

        # Day after tomorrow = Jan 12
        with pytest.raises(ServiceValidationError):
            await hass.services.async_call(
                "streakhub",
                "set_streak_start",
                {
                    "entity_id": "sensor.zucker_streak",
                    "date": "2025-01-12",
                },
                blocking=True,
            )


@pytest.mark.asyncio
async def test_service_date_far_future(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that far future date is rejected."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

        # Far future = 2026
        with pytest.raises(ServiceValidationError):
            await hass.services.async_call(
                "streakhub",
                "set_streak_start",
                {
                    "entity_id": "sensor.zucker_streak",
                    "date": "2026-01-01",
                },
                blocking=True,
            )


@pytest.mark.asyncio
async def test_service_date_before_streak_start(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that date before current streak start is rejected."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

        # Before streak start (Jan 1) = Dec 31
        with pytest.raises(ServiceValidationError):
            await hass.services.async_call(
                "streakhub",
                "set_streak_start",
                {
                    "entity_id": "sensor.zucker_streak",
                    "date": "2024-12-31",
                },
                blocking=True,
            )


@pytest.mark.asyncio
async def test_service_date_equals_streak_start(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that date equal to current streak start is rejected."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

        # Same as streak start (Jan 1)
        with pytest.raises(ServiceValidationError):
            await hass.services.async_call(
                "streakhub",
                "set_streak_start",
                {
                    "entity_id": "sensor.zucker_streak",
                    "date": "2025-01-01",
                },
                blocking=True,
            )


@pytest.mark.asyncio
async def test_service_on_streak_sensor(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that service works on streak sensor."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

        # Should succeed
        await hass.services.async_call(
            "streakhub",
            "set_streak_start",
            {
                "entity_id": "sensor.zucker_streak",
                "date": "2025-01-08",
            },
            blocking=True,
        )
        await hass.async_block_till_done()

        # Verify it worked
        streak_sensor = hass.states.get("sensor.zucker_streak")
        assert streak_sensor.attributes.get("streak_start") == "2025-01-08"


@pytest.mark.asyncio
async def test_service_on_rank_sensor(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that service on rank sensor works (same config entry)."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

        # Service should also work on rank sensor since they share coordinator
        await hass.services.async_call(
            "streakhub",
            "set_streak_start",
            {
                "entity_id": "sensor.zucker_rank",
                "date": "2025-01-08",
            },
            blocking=True,
        )
        await hass.async_block_till_done()

        # Verify it worked (check streak sensor which shares data)
        streak_sensor = hass.states.get("sensor.zucker_streak")
        assert streak_sensor.attributes.get("streak_start") == "2025-01-08"


@pytest.mark.asyncio
async def test_service_on_reset_button(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that service on reset button works (same config entry)."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

        # Service should also work on button since they share coordinator
        await hass.services.async_call(
            "streakhub",
            "set_streak_start",
            {
                "entity_id": "button.zucker_reset",
                "date": "2025-01-08",
            },
            blocking=True,
        )
        await hass.async_block_till_done()

        # Verify it worked
        streak_sensor = hass.states.get("sensor.zucker_streak")
        assert streak_sensor.attributes.get("streak_start") == "2025-01-08"


@pytest.mark.asyncio
async def test_service_on_foreign_entity(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that service fails on non-StreakHub entity."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

        # Try to call on a non-existent foreign entity
        # The service should simply log a warning and not crash
        await hass.services.async_call(
            "streakhub",
            "set_streak_start",
            {
                "entity_id": "sensor.some_other_sensor",
                "date": "2025-01-08",
            },
            blocking=True,
        )
        # Should complete without error (just logs warning)


@pytest.mark.asyncio
async def test_service_zero_day_old_streak(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that 0-day old streak is not saved to history."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-01 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

        # On start day (Jan 1), streak is 1 day
        # If we set new start to Jan 2, old streak is Jan 1 only = 1 day (should be saved)
        await hass.services.async_call(
            "streakhub",
            "set_streak_start",
            {
                "entity_id": "sensor.zucker_streak",
                "date": "2025-01-02",
            },
            blocking=True,
        )
        await hass.async_block_till_done()

        # Per konzept.md: set_streak_start(2025-01-02) on Jan 1
        # event_day = new_start - 1 = Jan 1
        # old_streak_end = event_day - 1 = Dec 31
        # old_streak_days = (Dec 31 - Jan 1).days + 1 = 0 Tage → nicht gespeichert
        coordinator = hass.data["streakhub"][basic_config_entry.entry_id]
        history = coordinator.data.get("history", [])
        assert len(history) == 0
