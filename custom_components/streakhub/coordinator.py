"""DataUpdateCoordinator for StreakHub integration."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import TYPE_CHECKING

from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, STORAGE_KEY, STORAGE_VERSION
from .logic import (
    StorageData,
    TrackerData,
    create_initial_storage_data,
    create_initial_tracker_data,
    process_event,
    process_set_streak_start,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class StreakHubCoordinator(DataUpdateCoordinator[TrackerData]):
    """Coordinator for a single StreakHub tracker.

    Manages data loading, saving, and updates for one tracker.
    Multiple coordinators share the same Store instance.
    """

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        store: Store[StorageData],
        tracker_id: str,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance.
            store: Shared storage instance for all trackers.
            tracker_id: Unique identifier for this tracker (slugified name).
            entry: Config entry for this tracker.
        """
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{tracker_id}",
            update_interval=timedelta(hours=1),
        )
        self._store = store
        self._tracker_id = tracker_id
        self._storage_data: StorageData | None = None
        self.config_entry = entry

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


async def async_get_or_create_store(hass: HomeAssistant) -> Store[StorageData]:
    """Get or create the shared storage instance.

    The store is cached in hass.data to be shared across all coordinators.

    Args:
        hass: Home Assistant instance.

    Returns:
        The shared Store instance.
    """
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    if "store" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["store"] = Store[StorageData](
            hass, STORAGE_VERSION, STORAGE_KEY
        )

    return hass.data[DOMAIN]["store"]


async def async_initialize_tracker(
    hass: HomeAssistant,
    store: Store[StorageData],
    tracker_id: str,
    initial_date: date,
) -> None:
    """Initialize a new tracker in storage if it doesn't exist.

    Args:
        hass: Home Assistant instance.
        store: The shared storage instance.
        tracker_id: Unique identifier for the tracker.
        initial_date: Initial streak start date.
    """
    storage_data = await store.async_load()

    if storage_data is None:
        storage_data = create_initial_storage_data()

    if tracker_id not in storage_data["trackers"]:
        _LOGGER.info(
            "Initializing new tracker '%s' with start date %s",
            tracker_id,
            initial_date.isoformat(),
        )
        storage_data["trackers"][tracker_id] = create_initial_tracker_data(
            initial_date
        )
        await store.async_save(storage_data)
    else:
        _LOGGER.debug("Tracker '%s' already exists in storage", tracker_id)


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
