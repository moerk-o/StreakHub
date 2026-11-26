"""The StreakHub integration."""

from __future__ import annotations

import logging
from datetime import date

import voluptuous as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.typing import ConfigType
from homeassistant.util import dt as dt_util
from homeassistant.util import slugify

from .const import CONF_GOAL, CONF_INITIAL_DATE, CONF_NAME, DOMAIN, PLATFORMS
from .coordinator import (
    StreakHubConfigEntry,
    StreakHubCoordinator,
    async_get_or_create_store,
    async_initialize_tracker,
    async_remove_tracker,
)
from .logic import validate_set_streak_start

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

# Service constants
SERVICE_SET_STREAK_START = "set_streak_start"
SERVICE_UNDO_LAST_EVENT = "undo_last_event"
ATTR_DATE = "date"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the StreakHub integration.

    Registers the services once, shared by all config entries.

    Args:
        hass: Home Assistant instance.
        config: Configuration (unused, StreakHub is set up via the UI only).

    Returns:
        True.
    """
    async_setup_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: StreakHubConfigEntry) -> bool:
    """Set up StreakHub from a config entry.

    Args:
        hass: Home Assistant instance.
        entry: Config entry to set up.

    Returns:
        True if setup was successful.
    """
    # Get or create shared store
    store = await async_get_or_create_store(hass)

    # Get tracker ID and initial date from config
    tracker_id = slugify(entry.data[CONF_NAME])
    initial_date_str = entry.data.get(CONF_INITIAL_DATE)
    goal = entry.data.get(CONF_GOAL, 0)

    if initial_date_str:
        initial_date = date.fromisoformat(initial_date_str)
    else:
        initial_date = dt_util.now().date()

    # Initialize tracker in storage if new
    await async_initialize_tracker(hass, store, tracker_id, initial_date, goal)

    # Create coordinator and load initial data
    coordinator = StreakHubCoordinator(hass, store, tracker_id, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: StreakHubConfigEntry) -> bool:
    """Unload a config entry.

    Args:
        hass: Home Assistant instance.
        entry: Config entry to unload.

    Returns:
        True if unload was successful.
    """
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: StreakHubConfigEntry) -> None:
    """Handle removal of a config entry.

    Removes the tracker data from storage when the config entry is deleted.

    Args:
        hass: Home Assistant instance.
        entry: Config entry being removed.
    """
    store = await async_get_or_create_store(hass)
    tracker_id = slugify(entry.data[CONF_NAME])
    await async_remove_tracker(store, tracker_id)


@callback
def _async_get_coordinators(
    hass: HomeAssistant, entity_ids: list[str]
) -> list[tuple[str, StreakHubCoordinator]]:
    """Resolve StreakHub entities to the coordinators of their trackers.

    Entities that are unknown, belong to another integration or whose
    tracker is not loaded are skipped with a warning.

    Args:
        hass: Home Assistant instance.
        entity_ids: Entity IDs from the service call.

    Returns:
        Pairs of entity ID and coordinator, in the order of entity_ids.
    """
    ent_reg = er.async_get(hass)
    coordinators: list[tuple[str, StreakHubCoordinator]] = []

    for entity_id in entity_ids:
        entity_entry = ent_reg.async_get(entity_id)
        if entity_entry is None:
            _LOGGER.warning("Entity %s not found", entity_id)
            continue

        if entity_entry.platform != DOMAIN:
            _LOGGER.warning("Entity %s is not a StreakHub entity", entity_id)
            continue

        config_entry_id = entity_entry.config_entry_id
        entry: StreakHubConfigEntry | None = (
            hass.config_entries.async_get_entry(config_entry_id)
            if config_entry_id
            else None
        )
        if entry is None or entry.state is not ConfigEntryState.LOADED:
            _LOGGER.warning("Config entry for entity %s not found", entity_id)
            continue

        coordinators.append((entity_id, entry.runtime_data))

    return coordinators


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Set up StreakHub services.

    Args:
        hass: Home Assistant instance.
    """

    async def handle_set_streak_start(call: ServiceCall) -> None:
        """Handle the set_streak_start service call.

        Args:
            call: Service call data.

        Raises:
            ServiceValidationError: If validation fails.
        """
        new_start: date = call.data[ATTR_DATE]
        today = dt_util.now().date()

        for entity_id, coordinator in _async_get_coordinators(
            hass, call.data["entity_id"]
        ):
            # Validate
            current_start = date.fromisoformat(coordinator.data["streak_start"])
            validation_error = validate_set_streak_start(
                current_start, new_start, today
            )

            if validation_error == "date_in_future":
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="date_in_future",
                )
            if validation_error == "date_before_streak_start":
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="date_before_streak_start",
                    translation_placeholders={
                        "streak_start": current_start.isoformat()
                    },
                )

            # Execute
            await coordinator.async_set_streak_start(new_start)
            _LOGGER.info(
                "Set streak start for %s to %s",
                entity_id,
                new_start.isoformat(),
            )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_STREAK_START,
        handle_set_streak_start,
        schema=vol.Schema(
            {
                vol.Required("entity_id"): cv.entity_ids,
                vol.Required(ATTR_DATE): cv.date,
            }
        ),
    )

    async def handle_undo_last_event(call: ServiceCall) -> None:
        """Handle the undo_last_event service call.

        Args:
            call: Service call data.

        Raises:
            ServiceValidationError: If undo is not possible.
        """
        for entity_id, coordinator in _async_get_coordinators(
            hass, call.data["entity_id"]
        ):
            if not await coordinator.async_undo_last_event():
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="undo_not_possible",
                )

            _LOGGER.info("Undid last event for %s", entity_id)

    hass.services.async_register(
        DOMAIN,
        SERVICE_UNDO_LAST_EVENT,
        handle_undo_last_event,
        schema=vol.Schema(
            {
                vol.Required("entity_id"): cv.entity_ids,
            }
        ),
    )

    _LOGGER.debug("Registered StreakHub services")
