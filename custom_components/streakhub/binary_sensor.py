"""Binary sensor platform for StreakHub integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,  # Needs Home Assistant 2025.3 (see hacs.json)
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, ENTITY_HAS_GOAL, ICON_HAS_GOAL
from .coordinator import StreakHubConfigEntry, StreakHubCoordinator

# Entities only read from or write to the coordinator, no device I/O
PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class StreakHubBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a StreakHub binary sensor entity."""

    is_on_fn: Callable[[StreakHubCoordinator], bool]


def _get_has_goal_state(coordinator: StreakHubCoordinator) -> bool:
    """Check if tracker has a goal set."""
    goal = coordinator.data.get("goal", 0)
    return goal > 0


BINARY_SENSOR_DESCRIPTIONS: tuple[StreakHubBinarySensorEntityDescription, ...] = (
    StreakHubBinarySensorEntityDescription(
        key=ENTITY_HAS_GOAL,
        translation_key=ENTITY_HAS_GOAL,
        icon=ICON_HAS_GOAL,
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=_get_has_goal_state,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: StreakHubConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up StreakHub binary sensor entities.

    Args:
        hass: Home Assistant instance.
        entry: Config entry.
        async_add_entities: Callback to add entities.
    """
    coordinator = entry.runtime_data

    async_add_entities(
        StreakHubBinarySensor(coordinator, description, entry)
        for description in BINARY_SENSOR_DESCRIPTIONS
    )


class StreakHubBinarySensor(
    CoordinatorEntity[StreakHubCoordinator], BinarySensorEntity
):
    """Representation of a StreakHub binary sensor."""

    entity_description: StreakHubBinarySensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: StreakHubCoordinator,
        description: StreakHubBinarySensorEntityDescription,
        entry: StreakHubConfigEntry,
    ) -> None:
        """Initialize the binary sensor.

        Args:
            coordinator: The data coordinator.
            description: Entity description for this binary sensor.
            entry: Config entry.
        """
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry

        # Unique ID based on entry ID and sensor key
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for device registry."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._entry.title,
            manufacturer="StreakHub",
            sw_version=self.coordinator.sw_version,
        )

    @property
    def is_on(self) -> bool:
        """Return True if the binary sensor is on."""
        if self.coordinator.data is None:
            return False
        return self.entity_description.is_on_fn(self.coordinator)
