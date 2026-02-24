"""Number platform for StreakHub integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, ENTITY_GOAL, ICON_GOAL, UNIT_DAYS
from .coordinator import StreakHubCoordinator


@dataclass(frozen=True, kw_only=True)
class StreakHubNumberEntityDescription(NumberEntityDescription):
    """Describes a StreakHub number entity."""


NUMBER_DESCRIPTIONS: tuple[StreakHubNumberEntityDescription, ...] = (
    StreakHubNumberEntityDescription(
        key=ENTITY_GOAL,
        translation_key=ENTITY_GOAL,
        icon=ICON_GOAL,
        native_min_value=0,
        native_step=1,
        native_unit_of_measurement=UNIT_DAYS,
        mode=NumberMode.BOX,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up StreakHub number entities.

    Args:
        hass: Home Assistant instance.
        entry: Config entry.
        async_add_entities: Callback to add entities.
    """
    coordinator: StreakHubCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        StreakHubNumber(coordinator, description, entry)
        for description in NUMBER_DESCRIPTIONS
    )


class StreakHubNumber(CoordinatorEntity[StreakHubCoordinator], NumberEntity):
    """Number entity for streak goal.

    Allows users to set and modify the streak goal (target days).
    When changed, all related entities (days_to_goal, has_goal) update automatically.
    """

    entity_description: StreakHubNumberEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: StreakHubCoordinator,
        description: StreakHubNumberEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the number entity.

        Args:
            coordinator: The data coordinator.
            description: Entity description for this number.
            entry: Config entry.
        """
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry

        # Unique ID based on entry ID and number key
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

    @property
    def native_value(self) -> int:
        """Return the current goal value from storage."""
        if self.coordinator.data is None:
            return 0
        return self.coordinator.data.get("goal", 0)

    async def async_set_native_value(self, value: float) -> None:
        """Set new goal value.

        Args:
            value: New goal value (will be converted to int).
        """
        new_goal = int(value)
        await self.coordinator.async_set_goal(new_goal)
