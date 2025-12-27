"""Button platform for StreakHub integration."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, ENTITY_RESET, ICON_RESET
from .coordinator import StreakHubCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up StreakHub button entities.

    Args:
        hass: Home Assistant instance.
        entry: Config entry.
        async_add_entities: Callback to add entities.
    """
    coordinator: StreakHubCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([ResetButton(coordinator, entry)])


class ResetButton(CoordinatorEntity[StreakHubCoordinator], ButtonEntity):
    """Button to reset the current streak.

    Pressing this button means "the event happened today".
    The current streak ends, and a new one begins tomorrow.
    """

    _attr_has_entity_name = True
    _attr_icon = ICON_RESET

    def __init__(
        self,
        coordinator: StreakHubCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the reset button.

        Args:
            coordinator: The data coordinator.
            entry: Config entry.
        """
        super().__init__(coordinator)
        self._entry = entry

        # Unique ID based on entry ID and entity type
        self._attr_unique_id = f"{entry.entry_id}_{ENTITY_RESET}"

        # Translation key for entity name
        self._attr_translation_key = ENTITY_RESET

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for device registry."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._entry.title,
            manufacturer="StreakHub",
            sw_version="1.0.0",
        )

    async def async_press(self) -> None:
        """Handle button press.

        Records that the event happened today:
        - Current streak ends (yesterday was the last day without event)
        - New streak starts tomorrow (first day without event)
        - Today shows streak value 0
        """
        today = dt_util.now().date()
        await self.coordinator.async_handle_event(today)
