"""Sensor platform for StreakHub integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,  # Needs Home Assistant 2025.3 (see hacs.json)
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    ENTITY_DAYS_TO_GOAL,
    ENTITY_RANK,
    ENTITY_STREAK,
    ICON_GOAL_NOT_REACHED,
    ICON_GOAL_REACHED,
    ICON_MEDAL,
    ICON_STREAK,
    ICON_TROPHY,
    UNIT_DAYS,
)
from .coordinator import StreakHubConfigEntry, StreakHubCoordinator
from .logic import (
    Top3Entry,
    calculate_days_to_goal,
    calculate_rank,
    calculate_streak,
    calculate_top_3,
)

# Entities only read from or write to the coordinator, no device I/O
PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class StreakHubSensorEntityDescription(SensorEntityDescription):
    """Describes a StreakHub sensor entity."""

    value_fn: Callable[[StreakHubCoordinator, date], Any]
    extra_state_attributes_fn: (
        Callable[[StreakHubCoordinator, date], dict[str, Any]] | None
    ) = None
    icon_fn: Callable[[StreakHubCoordinator, date], str] | None = None


def _get_streak_start(coordinator: StreakHubCoordinator) -> date:
    """Get streak start date from coordinator."""
    return date.fromisoformat(coordinator.data["streak_start"])


def _get_streak_value(coordinator: StreakHubCoordinator, today: date) -> int:
    """Calculate current streak value."""
    streak_start = _get_streak_start(coordinator)
    return calculate_streak(streak_start, today)


def _get_streak_attributes(
    coordinator: StreakHubCoordinator, today: date
) -> dict[str, Any]:
    """Get streak sensor attributes."""
    return {
        "streak_start": coordinator.data["streak_start"],
    }


def _get_top_3(coordinator: StreakHubCoordinator, today: date) -> list[Top3Entry]:
    """Calculate top 3 streaks."""
    streak_start = _get_streak_start(coordinator)
    history = coordinator.data["history"]
    return calculate_top_3(streak_start, history, today)


def _get_rank_value(coordinator: StreakHubCoordinator, today: date) -> int:
    """Calculate rank of current streak."""
    top_3 = _get_top_3(coordinator, today)
    return calculate_rank(top_3)


def _get_rank_attributes(
    coordinator: StreakHubCoordinator, today: date
) -> dict[str, Any]:
    """Get rank sensor attributes."""
    return {
        "top_3": _get_top_3(coordinator, today),
    }


def _get_rank_icon(coordinator: StreakHubCoordinator, today: date) -> str:
    """Get rank sensor icon based on current rank."""
    rank = _get_rank_value(coordinator, today)
    if rank in (1, 2, 3):
        return ICON_TROPHY
    return ICON_MEDAL


def _get_days_to_goal_value(
    coordinator: StreakHubCoordinator, today: date
) -> int | None:
    """Calculate days remaining to goal."""
    goal = coordinator.data.get("goal", 0)
    if goal == 0:
        return None
    current_streak = _get_streak_value(coordinator, today)
    return calculate_days_to_goal(current_streak, goal)


def _get_days_to_goal_icon(coordinator: StreakHubCoordinator, today: date) -> str:
    """Get days-to-goal icon based on goal status."""
    days_to_goal = _get_days_to_goal_value(coordinator, today)
    if days_to_goal is None or days_to_goal > 0:
        return ICON_GOAL_NOT_REACHED
    return ICON_GOAL_REACHED


def _get_days_to_goal_attributes(
    coordinator: StreakHubCoordinator, today: date
) -> dict[str, Any]:
    """Get days-to-goal sensor attributes."""
    goal = coordinator.data.get("goal", 0)
    attributes: dict[str, Any] = {"goal": goal}

    # Add goal_date if goal is set
    if goal > 0:
        streak_start = date.fromisoformat(coordinator.data["streak_start"])
        goal_date = streak_start + timedelta(days=goal - 1)
        attributes["goal_date"] = goal_date.isoformat()

    return attributes


SENSOR_DESCRIPTIONS: tuple[StreakHubSensorEntityDescription, ...] = (
    StreakHubSensorEntityDescription(
        key=ENTITY_STREAK,
        translation_key=ENTITY_STREAK,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UNIT_DAYS,
        icon=ICON_STREAK,
        value_fn=_get_streak_value,
        extra_state_attributes_fn=_get_streak_attributes,
    ),
    StreakHubSensorEntityDescription(
        key=ENTITY_RANK,
        translation_key=ENTITY_RANK,
        state_class=None,
        value_fn=_get_rank_value,
        extra_state_attributes_fn=_get_rank_attributes,
        icon_fn=_get_rank_icon,
    ),
    StreakHubSensorEntityDescription(
        key=ENTITY_DAYS_TO_GOAL,
        translation_key=ENTITY_DAYS_TO_GOAL,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UNIT_DAYS,
        icon_fn=_get_days_to_goal_icon,
        value_fn=_get_days_to_goal_value,
        extra_state_attributes_fn=_get_days_to_goal_attributes,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: StreakHubConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up StreakHub sensor entities.

    Args:
        hass: Home Assistant instance.
        entry: Config entry.
        async_add_entities: Callback to add entities.
    """
    coordinator = entry.runtime_data

    async_add_entities(
        StreakHubSensor(coordinator, description, entry)
        for description in SENSOR_DESCRIPTIONS
    )


class StreakHubSensor(CoordinatorEntity[StreakHubCoordinator], SensorEntity):
    """Representation of a StreakHub sensor."""

    entity_description: StreakHubSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: StreakHubCoordinator,
        description: StreakHubSensorEntityDescription,
        entry: StreakHubConfigEntry,
    ) -> None:
        """Initialize the sensor.

        Args:
            coordinator: The data coordinator.
            description: Entity description for this sensor.
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
            sw_version="1.0.0",
        )

    def _get_today(self) -> date:
        """Get today's date using Home Assistant's timezone-aware datetime."""
        return dt_util.now().date()

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator, self._get_today())

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if self.coordinator.data is None:
            return None
        if self.entity_description.extra_state_attributes_fn is None:
            return None
        return self.entity_description.extra_state_attributes_fn(
            self.coordinator, self._get_today()
        )

    @property
    def icon(self) -> str | None:
        """Return the icon for the sensor."""
        if self.entity_description.icon_fn is not None and self.coordinator.data:
            return self.entity_description.icon_fn(self.coordinator, self._get_today())
        return self.entity_description.icon
