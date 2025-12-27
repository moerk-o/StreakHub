"""Sensor platform for StreakHub integration."""

from __future__ import annotations

from datetime import date
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    ENTITY_RANK,
    ENTITY_STREAK,
    ICON_MEDAL,
    ICON_STREAK,
    ICON_TROPHY,
    ICON_TROPHY_OUTLINE,
    UNIT_DAYS,
)
from .coordinator import StreakHubCoordinator
from .logic import calculate_rank, calculate_streak, calculate_top_3


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up StreakHub sensor entities.

    Args:
        hass: Home Assistant instance.
        entry: Config entry.
        async_add_entities: Callback to add entities.
    """
    coordinator: StreakHubCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            StreakSensor(coordinator, entry),
            RankSensor(coordinator, entry),
        ]
    )


class StreakHubBaseSensor(CoordinatorEntity[StreakHubCoordinator], SensorEntity):
    """Base class for StreakHub sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: StreakHubCoordinator,
        entry: ConfigEntry,
        entity_key: str,
    ) -> None:
        """Initialize the sensor.

        Args:
            coordinator: The data coordinator.
            entry: Config entry.
            entity_key: Key for this entity type (streak, rank).
        """
        super().__init__(coordinator)
        self._entry = entry
        self._entity_key = entity_key

        # Unique ID based on entry ID and entity type
        self._attr_unique_id = f"{entry.entry_id}_{entity_key}"

        # Translation key for entity name
        self._attr_translation_key = entity_key

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
        """Get today's date using Home Assistant's timezone-aware datetime.

        Returns:
            Today's date in the configured timezone.
        """
        return dt_util.now().date()

    def _get_streak_start(self) -> date:
        """Get the streak start date from coordinator data.

        Returns:
            The streak start date.
        """
        return date.fromisoformat(self.coordinator.data["streak_start"])


class StreakSensor(StreakHubBaseSensor):
    """Sensor showing the current streak in days.

    State: Number of days since the last event (0 on event day).
    Attributes: streak_start (ISO 8601 date string).
    """

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UNIT_DAYS
    _attr_icon = ICON_STREAK

    def __init__(
        self,
        coordinator: StreakHubCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the streak sensor."""
        super().__init__(coordinator, entry, ENTITY_STREAK)

    @property
    def native_value(self) -> int:
        """Return the current streak value in days.

        Returns 0 if we are on the event day (today < streak_start).
        Otherwise returns days since streak_start (inclusive).
        """
        streak_start = self._get_streak_start()
        today = self._get_today()
        return calculate_streak(streak_start, today)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes.

        Returns:
            Dictionary with streak_start as ISO 8601 string.
        """
        return {
            "streak_start": self.coordinator.data["streak_start"],
        }


class RankSensor(StreakHubBaseSensor):
    """Sensor showing the current streak's rank in top 3.

    State: 1, 2, 3 (if in top 3) or 0 (not in top 3).
    Attributes: top_3 (list of top 3 streaks with rank, start, end, days).
    """

    _attr_state_class = None  # Not a measurement

    def __init__(
        self,
        coordinator: StreakHubCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the rank sensor."""
        super().__init__(coordinator, entry, ENTITY_RANK)

    @property
    def native_value(self) -> int:
        """Return the rank of the current streak.

        Returns 1, 2, or 3 if current streak is in top 3.
        Returns 0 if not in top 3.
        """
        top_3 = self._calculate_top_3()
        return calculate_rank(top_3)

    @property
    def icon(self) -> str:
        """Return icon based on current rank.

        Returns:
            mdi:trophy for rank 1 (record!).
            mdi:medal-outline for rank 2 or 3.
            mdi:trophy-outline for not in top 3.
        """
        rank = self.native_value
        if rank == 1:
            return ICON_TROPHY
        elif rank in (2, 3):
            return ICON_MEDAL
        return ICON_TROPHY_OUTLINE

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes.

        Returns:
            Dictionary with top_3 list containing rank, start, end, days.
        """
        return {
            "top_3": self._calculate_top_3(),
        }

    def _calculate_top_3(self) -> list[dict[str, Any]]:
        """Calculate the top 3 streaks.

        Returns:
            List of up to 3 entries with rank, start, end, days.
            Current streak has end=None.
        """
        streak_start = self._get_streak_start()
        today = self._get_today()
        history = self.coordinator.data["history"]

        return calculate_top_3(streak_start, history, today)
