"""Button platform for StreakHub integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import (
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,  # Needs Home Assistant 2025.3 (see hacs.json)
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, ENTITY_RESET, ICON_RESET
from .coordinator import StreakHubConfigEntry, StreakHubCoordinator

# Entities only read from or write to the coordinator, no device I/O
PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class StreakHubButtonEntityDescription(ButtonEntityDescription):
    """Describes a StreakHub button entity."""


BUTTON_DESCRIPTIONS: tuple[StreakHubButtonEntityDescription, ...] = (
    StreakHubButtonEntityDescription(
        key=ENTITY_RESET,
        translation_key=ENTITY_RESET,
        icon=ICON_RESET,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: StreakHubConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up StreakHub button entities.

    Args:
        hass: Home Assistant instance.
        entry: Config entry.
        async_add_entities: Callback to add entities.
    """
    coordinator = entry.runtime_data

    async_add_entities(
        StreakHubButton(coordinator, description, entry)
        for description in BUTTON_DESCRIPTIONS
    )


class StreakHubButton(CoordinatorEntity[StreakHubCoordinator], ButtonEntity):
    """Button to reset the current streak.

    Pressing this button means "the event happened today".
    The current streak ends, and a new one begins tomorrow.
    """

    entity_description: StreakHubButtonEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: StreakHubCoordinator,
        description: StreakHubButtonEntityDescription,
        entry: StreakHubConfigEntry,
    ) -> None:
        """Initialize the button.

        Args:
            coordinator: The data coordinator.
            description: Entity description for this button.
            entry: Config entry.
        """
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry

        # Unique ID based on entry ID and button key
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

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
