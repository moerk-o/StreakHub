"""Test StreakHub storage and persistence."""

import pytest
from freezegun import freeze_time
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant


@pytest.mark.asyncio
async def test_storage_empty_creates_tracker(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that a new installation creates tracker in storage."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

    # Verify coordinator has data
    coordinator = hass.data["streakhub"][basic_config_entry.entry_id]
    assert coordinator.data is not None
    assert "streak_start" in coordinator.data
    assert "history" in coordinator.data


@pytest.mark.asyncio
async def test_storage_persists_after_reload(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that data persists after config entry reload."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

        # Press reset to modify data
        await hass.services.async_call(
            "button", "press",
            {"entity_id": "button.zucker_reset"},
            blocking=True,
        )
        await hass.async_block_till_done()

        # Get data before unload
        coordinator = hass.data["streakhub"][basic_config_entry.entry_id]
        history_before = coordinator.data.get("history", [])
        assert len(history_before) == 1

        # Unload
        await hass.config_entries.async_unload(basic_config_entry.entry_id)
        await hass.async_block_till_done()

        # Reload
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

        # Data should still be there
        coordinator = hass.data["streakhub"][basic_config_entry.entry_id]
        history_after = coordinator.data.get("history", [])
        assert len(history_after) == 1
        # Per konzept.md: Button press on Jan 10 saves streak Jan 1-9 = 9 days
        assert history_after[0]["days"] == 9


@pytest.mark.asyncio
async def test_storage_multiple_trackers(hass: HomeAssistant) -> None:
    """Test that multiple trackers are stored independently."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry1 = MockConfigEntry(
        domain="streakhub",
        data={"name": "Tracker A", "initial_date": "2025-01-01"},
        unique_id="tracker_a",
        title="Tracker A",
        version=1,
    )
    entry2 = MockConfigEntry(
        domain="streakhub",
        data={"name": "Tracker B", "initial_date": "2025-01-05"},
        unique_id="tracker_b",
        title="Tracker B",
        version=1,
    )

    entry1.add_to_hass(hass)
    entry2.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        # Only call async_setup once - Home Assistant automatically loads
        # all config entries of a domain when the integration is first set up
        assert await hass.config_entries.async_setup(entry1.entry_id)
        await hass.async_block_till_done()

    # Verify both trackers exist with different data
    sensor_a = hass.states.get("sensor.tracker_a_streak")
    sensor_b = hass.states.get("sensor.tracker_b_streak")

    assert sensor_a is not None
    assert sensor_b is not None

    # Tracker A: Jan 1 - Jan 10 = 10 days
    assert int(sensor_a.state) == 10
    # Tracker B: Jan 5 - Jan 10 = 6 days
    assert int(sensor_b.state) == 6

    # Modify only tracker A
    with freeze_time("2025-01-10 12:00:00+00:00"):
        await hass.services.async_call(
            "button", "press",
            {"entity_id": "button.tracker_a_reset"},
            blocking=True,
        )
        await hass.async_block_till_done()

    # Tracker A should be reset, B unchanged
    sensor_a = hass.states.get("sensor.tracker_a_streak")
    sensor_b = hass.states.get("sensor.tracker_b_streak")

    assert int(sensor_a.state) == 0
    assert int(sensor_b.state) == 6


@pytest.mark.asyncio
async def test_storage_entry_removal(
    hass: HomeAssistant, basic_config_entry
) -> None:
    """Test that tracker data is removed from storage when entry is deleted."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

    # Get the store
    store = hass.data["streakhub"]["store"]
    storage_data = await store.async_load()
    assert "zucker" in storage_data["trackers"]

    # Remove the config entry
    await hass.config_entries.async_remove(basic_config_entry.entry_id)
    await hass.async_block_till_done()

    # Tracker should be removed from storage
    storage_data = await store.async_load()
    assert "zucker" not in storage_data["trackers"]


@pytest.mark.asyncio
async def test_storage_version(hass: HomeAssistant, basic_config_entry) -> None:
    """Test that storage version is set correctly."""
    basic_config_entry.add_to_hass(hass)

    with freeze_time("2025-01-10 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

    # Get the store and verify version
    store = hass.data["streakhub"]["store"]
    # Store version is set in const.py as STORAGE_VERSION = 1
    assert store.version == 1
