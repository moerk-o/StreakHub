"""Test StreakHub integration setup and entity creation."""

import pytest
from freezegun import freeze_time
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component


@pytest.mark.asyncio
async def test_setup_component_minimal(hass: HomeAssistant) -> None:
    """Test minimal component setup without config entry."""
    assert await async_setup_component(hass, "streakhub", {})
    await hass.async_block_till_done()

    assert "streakhub" in hass.config.components


@pytest.mark.asyncio
async def test_config_entry_setup_creates_entities(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that config entry setup creates all expected entities."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

    # Verify the entry is loaded
    assert basic_config_entry.state == ConfigEntryState.LOADED

    # Check sensor entities
    streak_sensor = hass.states.get("sensor.zucker_streak")
    assert streak_sensor is not None
    assert int(streak_sensor.state) == 10  # 10 days from Jan 1 to Jan 10

    rank_sensor = hass.states.get("sensor.zucker_rank")
    assert rank_sensor is not None
    assert int(rank_sensor.state) == 1  # First streak is always rank 1

    # Check button entity
    reset_button = hass.states.get("button.zucker_reset")
    assert reset_button is not None


@pytest.mark.asyncio
async def test_entity_ids_follow_pattern(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that entity IDs follow the expected pattern."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-05 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

    # Entity IDs should be: sensor.{name}_streak, sensor.{name}_rank, button.{name}_reset
    assert hass.states.get("sensor.zucker_streak") is not None
    assert hass.states.get("sensor.zucker_rank") is not None
    assert hass.states.get("button.zucker_reset") is not None


@pytest.mark.asyncio
async def test_config_entry_unload(hass: HomeAssistant, basic_config_entry) -> None:
    """Test that config entry can be unloaded."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-05 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

    assert basic_config_entry.state == ConfigEntryState.LOADED

    # Unload the entry
    assert await hass.config_entries.async_unload(basic_config_entry.entry_id)
    await hass.async_block_till_done()

    assert basic_config_entry.state == ConfigEntryState.NOT_LOADED

    # After unload, entities are marked as unavailable (not removed from registry)
    state = hass.states.get("sensor.zucker_streak")
    assert state is not None
    assert state.state == "unavailable"


@pytest.mark.asyncio
async def test_config_entry_remove_cleans_up_entities(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that removing a config entry completely removes entities from registry."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-05 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

    # Verify entities exist in registry
    entity_registry = er.async_get(hass)
    assert entity_registry.async_get("sensor.zucker_streak") is not None
    assert entity_registry.async_get("sensor.zucker_rank") is not None
    assert entity_registry.async_get("button.zucker_reset") is not None

    # Remove the config entry (this simulates user deleting the integration)
    await hass.config_entries.async_remove(basic_config_entry.entry_id)
    await hass.async_block_till_done()

    # After removal, entities should be completely gone from registry
    assert entity_registry.async_get("sensor.zucker_streak") is None
    assert entity_registry.async_get("sensor.zucker_rank") is None
    assert entity_registry.async_get("button.zucker_reset") is None

    # State machine should also not have them anymore
    assert hass.states.get("sensor.zucker_streak") is None
