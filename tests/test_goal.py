"""Test goal-tracking features (Number entity, Days-to-Goal sensor, Has-Goal binary sensor)."""

from datetime import date

import pytest
from freezegun import freeze_time
from homeassistant.core import HomeAssistant

from conftest import STORAGE_KEY, build_hass_storage_entry


@pytest.mark.asyncio
async def test_goal_number_entity_exists(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that goal number entity is created."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

    goal_number = hass.states.get("number.zucker_goal")
    assert goal_number is not None
    assert goal_number.state == "0"  # Default goal


@pytest.mark.asyncio
async def test_goal_number_set_value(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that goal number entity value can be set."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

    # Set goal to 100
    await hass.services.async_call(
        "number",
        "set_value",
        {
            "entity_id": "number.zucker_goal",
            "value": 100,
        },
        blocking=True,
    )

    goal_number = hass.states.get("number.zucker_goal")
    assert goal_number is not None
    assert int(float(goal_number.state)) == 100


@pytest.mark.asyncio
async def test_days_to_goal_positive(hass: HomeAssistant, hass_storage: dict) -> None:
    """Test that days_to_goal shows positive values correctly."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    # Goal of 100 days, streak started on 2025-01-01, test on 2025-01-15
    # Streak = 15 days, days_to_goal = 100 - 15 = 85
    hass_storage[STORAGE_KEY] = build_hass_storage_entry(
        tracker_id="test_goal",
        current_streak_start=date(2025, 1, 1),
        goal=100,
    )

    config_entry = MockConfigEntry(
        domain="streakhub",
        data={
            "name": "Test Goal",
            "initial_date": "2025-01-01",
            "goal": 100,
        },
        unique_id="test_goal",
        title="Test Goal",
        version=1,
    )
    config_entry.add_to_hass(hass)

    with freeze_time("2025-01-15 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        days_to_goal_sensor = hass.states.get("sensor.test_goal_days_to_goal")
        assert days_to_goal_sensor is not None
        assert int(days_to_goal_sensor.state) == 85


@pytest.mark.asyncio
async def test_days_to_goal_zero(hass: HomeAssistant, hass_storage: dict) -> None:
    """Test that days_to_goal is 0 when goal is reached."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    # Goal of 100 days, streak started on 2025-01-01, test on 2025-04-10
    # Streak = 100 days (01-01 to 04-10), days_to_goal = 100 - 100 = 0
    hass_storage[STORAGE_KEY] = build_hass_storage_entry(
        tracker_id="test_goal",
        current_streak_start=date(2025, 1, 1),
        goal=100,
    )

    config_entry = MockConfigEntry(
        domain="streakhub",
        data={
            "name": "Test Goal",
            "initial_date": "2025-01-01",
            "goal": 100,
        },
        unique_id="test_goal",
        title="Test Goal",
        version=1,
    )
    config_entry.add_to_hass(hass)

    with freeze_time("2025-04-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        days_to_goal_sensor = hass.states.get("sensor.test_goal_days_to_goal")
        assert days_to_goal_sensor is not None
        assert int(days_to_goal_sensor.state) == 0


@pytest.mark.asyncio
async def test_days_to_goal_negative(hass: HomeAssistant, hass_storage: dict) -> None:
    """Test that days_to_goal shows negative values when goal is exceeded."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    # Goal of 100 days, streak started on 2025-01-01, test on 2025-04-20
    # Streak = 110 days (01-01 to 04-20), days_to_goal = 100 - 110 = -10
    hass_storage[STORAGE_KEY] = build_hass_storage_entry(
        tracker_id="test_goal",
        current_streak_start=date(2025, 1, 1),
        goal=100,
    )

    config_entry = MockConfigEntry(
        domain="streakhub",
        data={
            "name": "Test Goal",
            "initial_date": "2025-01-01",
            "goal": 100,
        },
        unique_id="test_goal",
        title="Test Goal",
        version=1,
    )
    config_entry.add_to_hass(hass)

    with freeze_time("2025-04-20 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        days_to_goal_sensor = hass.states.get("sensor.test_goal_days_to_goal")
        assert days_to_goal_sensor is not None
        assert int(days_to_goal_sensor.state) == -10


@pytest.mark.asyncio
async def test_days_to_goal_icon_changes(
    hass: HomeAssistant, hass_storage: dict
) -> None:
    """Test that days_to_goal icon changes when goal is reached."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    hass_storage[STORAGE_KEY] = build_hass_storage_entry(
        tracker_id="test_goal",
        current_streak_start=date(2025, 1, 1),
        goal=100,
    )

    config_entry = MockConfigEntry(
        domain="streakhub",
        data={
            "name": "Test Goal",
            "initial_date": "2025-01-01",
            "goal": 100,
        },
        unique_id="test_goal",
        title="Test Goal",
        version=1,
    )
    config_entry.add_to_hass(hass)

    # Before goal: icon should be outline
    with freeze_time("2025-01-15 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        days_to_goal_sensor = hass.states.get("sensor.test_goal_days_to_goal")
        assert days_to_goal_sensor is not None
        assert days_to_goal_sensor.attributes.get("icon") == "mdi:check-decagram-outline"

    # Reload at goal reached: icon should be solid
    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    with freeze_time("2025-04-11 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        days_to_goal_sensor = hass.states.get("sensor.test_goal_days_to_goal")
        assert days_to_goal_sensor is not None
        assert days_to_goal_sensor.attributes.get("icon") == "mdi:check-decagram"


@pytest.mark.asyncio
async def test_has_goal_binary_sensor_off(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that has_goal binary sensor is off when goal is 0."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

    has_goal_sensor = hass.states.get("binary_sensor.zucker_has_goal")
    assert has_goal_sensor is not None
    assert has_goal_sensor.state == "off"


@pytest.mark.asyncio
async def test_has_goal_binary_sensor_on(
    hass: HomeAssistant, hass_storage: dict
) -> None:
    """Test that has_goal binary sensor is on when goal > 0."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    hass_storage[STORAGE_KEY] = build_hass_storage_entry(
        tracker_id="test_goal",
        current_streak_start=date(2025, 1, 1),
        goal=100,
    )

    config_entry = MockConfigEntry(
        domain="streakhub",
        data={
            "name": "Test Goal",
            "initial_date": "2025-01-01",
            "goal": 100,
        },
        unique_id="test_goal",
        title="Test Goal",
        version=1,
    )
    config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    has_goal_sensor = hass.states.get("binary_sensor.test_goal_has_goal")
    assert has_goal_sensor is not None
    assert has_goal_sensor.state == "on"
