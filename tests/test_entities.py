"""Test StreakHub entity properties and attributes."""

import pytest
from freezegun import freeze_time
from homeassistant.components.sensor import SensorStateClass
from homeassistant.core import HomeAssistant


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
    hass: HomeAssistant, config_entry_with_history
) -> None:
    """Test that rank sensor shows medal icon when rank is 2 or 3."""
    # This test requires a config entry with history where current streak
    # ranks 2nd or 3rd. We need to mock storage data to have longer historical streaks.
    # For now, skip this test as it requires storage mocking
    pytest.skip("Requires storage mocking for history data")


@pytest.mark.asyncio
async def test_rank_sensor_icon_rank_0(
    hass: HomeAssistant, config_entry_with_history
) -> None:
    """Test that rank sensor shows trophy-outline icon when rank is 0 (not in top 3)."""
    # This test requires history with at least 3 longer streaks
    pytest.skip("Requires storage mocking for history data")


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
