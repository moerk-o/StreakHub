"""Test StreakHub entity properties and attributes."""

from datetime import date

import pytest
from freezegun import freeze_time
from homeassistant.components.sensor import SensorStateClass
from homeassistant.core import HomeAssistant

from conftest import STORAGE_KEY, build_hass_storage_entry


@pytest.mark.asyncio
async def test_streak_sensor_state_class(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that streak sensor has SensorStateClass.MEASUREMENT."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

    streak_sensor = hass.states.get("sensor.zucker_streak")
    assert streak_sensor is not None
    assert streak_sensor.attributes.get("state_class") == SensorStateClass.MEASUREMENT


@pytest.mark.asyncio
async def test_streak_sensor_unit(hass: HomeAssistant, basic_config_entry) -> None:
    """Test that streak sensor has unit 'd' (days)."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

    streak_sensor = hass.states.get("sensor.zucker_streak")
    assert streak_sensor is not None
    assert streak_sensor.attributes.get("unit_of_measurement") == "d"


@pytest.mark.asyncio
async def test_streak_sensor_icon(hass: HomeAssistant, basic_config_entry) -> None:
    """Test that streak sensor has icon mdi:counter."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

    streak_sensor = hass.states.get("sensor.zucker_streak")
    assert streak_sensor is not None
    assert streak_sensor.attributes.get("icon") == "mdi:counter"


@pytest.mark.asyncio
async def test_streak_sensor_attributes(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that streak sensor has streak_start attribute in ISO 8601 format."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

    streak_sensor = hass.states.get("sensor.zucker_streak")
    assert streak_sensor is not None

    streak_start = streak_sensor.attributes.get("streak_start")
    assert streak_start is not None
    assert streak_start == "2025-01-01"


@pytest.mark.asyncio
async def test_rank_sensor_state_class(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that rank sensor has no state class (not a measurement)."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

    rank_sensor = hass.states.get("sensor.zucker_rank")
    assert rank_sensor is not None
    assert rank_sensor.attributes.get("state_class") is None


@pytest.mark.asyncio
async def test_rank_sensor_icon_rank_1(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that rank sensor shows trophy icon when rank is 1."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

    rank_sensor = hass.states.get("sensor.zucker_rank")
    assert rank_sensor is not None
    # First streak is always rank 1
    assert int(rank_sensor.state) == 1
    assert rank_sensor.attributes.get("icon") == "mdi:trophy"


@pytest.mark.asyncio
async def test_rank_sensor_icon_rank_2_3(
    hass: HomeAssistant, config_entry_with_history, hass_storage: dict
) -> None:
    """Test that rank sensor shows trophy icon when rank is 2 or 3."""
    # Setup: Current streak = 5 days, History has 1 longer streak (10 days)
    # At 2025-01-20, current streak started 2025-01-16 = 5 days -> rank 2
    hass_storage[STORAGE_KEY] = build_hass_storage_entry(
        tracker_id="mit_history",
        current_streak_start=date(2025, 1, 16),
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
    assert rank_sensor.attributes.get("icon") == "mdi:trophy"


@pytest.mark.asyncio
async def test_rank_sensor_icon_rank_0(
    hass: HomeAssistant, config_entry_with_history, hass_storage: dict
) -> None:
    """Test that rank sensor shows medal icon when rank is 0 (not in top 3)."""
    # Setup: Current streak = 3 days, History has 3 longer streaks
    # At 2025-01-20, current streak started 2025-01-18 = 3 days -> rank 0
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
    assert rank_sensor.attributes.get("icon") == "mdi:medal-outline"


@pytest.mark.asyncio
async def test_rank_sensor_attributes(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that rank sensor has top_3 attribute as a list."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

    rank_sensor = hass.states.get("sensor.zucker_rank")
    assert rank_sensor is not None

    top_3 = rank_sensor.attributes.get("top_3")
    assert top_3 is not None
    assert isinstance(top_3, list)
    # With no history, top_3 should contain only the current streak
    assert len(top_3) >= 1


@pytest.mark.asyncio
async def test_reset_button_icon(hass: HomeAssistant, basic_config_entry) -> None:
    """Test that reset button has icon mdi:restart."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

    reset_button = hass.states.get("button.zucker_reset")
    assert reset_button is not None
    assert reset_button.attributes.get("icon") == "mdi:restart"
