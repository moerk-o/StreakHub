"""DataUpdateCoordinator for StreakHub integration."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util.hass_dict import HassKey

from .const import DOMAIN, STORAGE_KEY, STORAGE_VERSION
from .logic import (
    StorageData,
    TrackerData,
    create_initial_storage_data,
    create_initial_tracker_data,
    process_event,
    process_set_streak_start,
    undo_last_event,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# Shared storage instance for all trackers
DATA_STORE: HassKey[Store[StorageData]] = HassKey(f"{DOMAIN}_store")

type StreakHubConfigEntry = ConfigEntry[StreakHubCoordinator]


class StreakHubCoordinator(DataUpdateCoordinator[TrackerData]):
    """Coordinator for a single StreakHub tracker.

    Manages data loading, saving, and updates for one tracker.
    Multiple coordinators share the same Store instance.
    """

    config_entry: StreakHubConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        store: Store[StorageData],
        tracker_id: str,
        entry: StreakHubConfigEntry,
        sw_version: str,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance.
            store: Shared storage instance for all trackers.
            tracker_id: Unique identifier for this tracker (slugified name).
            entry: Config entry for this tracker.
            sw_version: Integration version, shown on the tracker device.
        """
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_{tracker_id}",
            update_interval=timedelta(hours=1),
        )
        self._store = store
        self._tracker_id = tracker_id
        self._storage_data: StorageData | None = None
        self.sw_version = sw_version

    @property
    def tracker_id(self) -> str:
        """Return the tracker ID."""
        return self._tracker_id

    async def _async_update_data(self) -> TrackerData:
        """Load tracker data from storage.

        Returns:
            TrackerData for this tracker.

        Raises:
            KeyError: If tracker not found in storage (should not happen).
        """
        self._storage_data = await self._store.async_load()

        if self._storage_data is None:
            _LOGGER.debug("Storage empty, creating initial data")
            self._storage_data = create_initial_storage_data()

        if self._tracker_id not in self._storage_data["trackers"]:
            _LOGGER.error(
                "Tracker '%s' not found in storage, this should not happen",
                self._tracker_id,
            )
            raise KeyError(f"Tracker '{self._tracker_id}' not found in storage")

        return self._storage_data["trackers"][self._tracker_id]

    async def async_handle_event(self, event_day: date) -> None:
        """Process a button press / event.

        Updates the tracker data, saves to storage, and refreshes entities.

        Args:
            event_day: The day the event occurred (typically today).
        """
        if self._storage_data is None or self.data is None:
            _LOGGER.error("Cannot handle event: storage data not loaded")
            return

        _LOGGER.debug(
            "Handling event for tracker '%s' on %s",
            self._tracker_id,
            event_day.isoformat(),
        )

        # Process the event (pure function, no mutation)
        new_tracker_data, history_entry = process_event(self.data, event_day)

        if history_entry is not None:
            _LOGGER.info(
                "Tracker '%s': Streak ended with %d days (%s to %s)",
                self._tracker_id,
                history_entry["days"],
                history_entry["start"],
                history_entry["end"],
            )
        else:
            _LOGGER.debug(
                "Tracker '%s': 0-day streak not saved to history",
                self._tracker_id,
            )

        # Update storage
        self._storage_data["trackers"][self._tracker_id] = new_tracker_data
        await self._store.async_save(self._storage_data)

        # Refresh all entities
        await self.async_refresh()

    async def async_set_streak_start(self, new_start: date) -> None:
        """Set a new streak start date.

        Used for correcting missed button presses. The new_start is the first
        day WITHOUT the event, meaning the event happened on new_start - 1.

        Args:
            new_start: The new streak start date.

        Note:
            Validation should be done by the service handler before calling.
        """
        if self._storage_data is None or self.data is None:
            _LOGGER.error("Cannot set streak start: storage data not loaded")
            return

        _LOGGER.debug(
            "Setting streak start for tracker '%s' to %s",
            self._tracker_id,
            new_start.isoformat(),
        )

        # Process the change (pure function, no mutation)
        new_tracker_data, history_entry = process_set_streak_start(
            self.data, new_start
        )

        if history_entry is not None:
            _LOGGER.info(
                "Tracker '%s': Corrected streak, old streak had %d days (%s to %s)",
                self._tracker_id,
                history_entry["days"],
                history_entry["start"],
                history_entry["end"],
            )

        # Update storage
        self._storage_data["trackers"][self._tracker_id] = new_tracker_data
        await self._store.async_save(self._storage_data)

        # Refresh all entities
        await self.async_refresh()

    async def async_undo_last_event(self) -> bool:
        """Undo the last event (button press or set_streak_start).

        Restores the previous streak by removing the last history entry
        and resetting streak_start to the removed entry's start date.

        Returns:
            True if undo was successful, False if not possible.
        """
        if self._storage_data is None or self.data is None:
            _LOGGER.error("Cannot undo: storage data not loaded")
            return False

        # Try to undo (pure function)
        new_tracker_data = undo_last_event(self.data)

        if new_tracker_data is None:
            _LOGGER.warning(
                "Tracker '%s': Undo not possible (no recent event or empty history)",
                self._tracker_id,
            )
            return False

        _LOGGER.info(
            "Tracker '%s': Undid last event, restored streak starting %s",
            self._tracker_id,
            new_tracker_data["streak_start"],
        )

        # Update storage
        self._storage_data["trackers"][self._tracker_id] = new_tracker_data
        await self._store.async_save(self._storage_data)

        # Refresh all entities
        await self.async_refresh()
        return True

    async def async_set_goal(self, new_goal: int) -> None:
        """Set a new streak goal.

        Updates the goal value in storage and refreshes all entities.
        This triggers updates to days_to_goal sensor and has_goal binary sensor.

        Args:
            new_goal: New goal value in days (0 = no goal).
        """
        if self._storage_data is None or self.data is None:
            _LOGGER.error("Cannot set goal: storage data not loaded")
            return

        _LOGGER.info(
            "Tracker '%s': Setting goal to %d days (previous: %d)",
            self._tracker_id,
            new_goal,
            self.data.get("goal", 0),
        )

        # Update goal in storage
        self._storage_data["trackers"][self._tracker_id]["goal"] = new_goal
        await self._store.async_save(self._storage_data)

        # Refresh all entities
        await self.async_refresh()


async def async_get_or_create_store(hass: HomeAssistant) -> Store[StorageData]:
    """Get or create the shared storage instance.

    The store is kept in hass.data to be shared across all coordinators.

    Args:
        hass: Home Assistant instance.

    Returns:
        The shared Store instance.
    """
    if DATA_STORE not in hass.data:
        hass.data[DATA_STORE] = Store[StorageData](
            hass, STORAGE_VERSION, STORAGE_KEY
        )

    return hass.data[DATA_STORE]


async def async_initialize_tracker(
    hass: HomeAssistant,
    store: Store[StorageData],
    tracker_id: str,
    initial_date: date,
    goal: int = 0,
) -> None:
    """Initialize a new tracker in storage if it doesn't exist.

    Args:
        hass: Home Assistant instance.
        store: The shared storage instance.
        tracker_id: Unique identifier for the tracker.
        initial_date: Initial streak start date.
        goal: Target days for the streak (0 = no goal).
    """
    storage_data = await store.async_load()

    if storage_data is None:
        storage_data = create_initial_storage_data()

    if tracker_id not in storage_data["trackers"]:
        _LOGGER.info(
            "Initializing new tracker '%s' with start date %s and goal %d",
            tracker_id,
            initial_date.isoformat(),
            goal,
        )
        storage_data["trackers"][tracker_id] = create_initial_tracker_data(
            initial_date, goal
        )
        await store.async_save(storage_data)
    else:
        _LOGGER.debug("Tracker '%s' already exists in storage", tracker_id)
        # Migration: Add goal field if missing (for trackers created before v1.2.0)
        tracker_data = storage_data["trackers"][tracker_id]
        if "goal" not in tracker_data:
            _LOGGER.info("Migrating tracker '%s': adding goal field", tracker_id)
            tracker_data["goal"] = 0
            await store.async_save(storage_data)


async def async_remove_tracker(
    store: Store[StorageData],
    tracker_id: str,
) -> None:
    """Remove a tracker from storage.

    Args:
        store: The shared storage instance.
        tracker_id: Unique identifier for the tracker to remove.
    """
    storage_data = await store.async_load()

    if storage_data is None:
        return

    if tracker_id in storage_data["trackers"]:
        _LOGGER.info("Removing tracker '%s' from storage", tracker_id)
        del storage_data["trackers"][tracker_id]
        await store.async_save(storage_data)
