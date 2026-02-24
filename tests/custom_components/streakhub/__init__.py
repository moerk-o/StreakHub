"""The StreakHub integration."""

from __future__ import annotations

import logging
from datetime import date
from typing import TYPE_CHECKING

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.util import slugify
from homeassistant.util import dt as dt_util

from .const import CONF_GOAL, CONF_INITIAL_DATE, CONF_NAME, DOMAIN, PLATFORMS
from .coordinator import (
    StreakHubCoordinator,
    async_get_or_create_store,
    async_initialize_tracker,
    async_remove_tracker,
)
from .logic import validate_set_streak_start

if TYPE_CHECKING:
    pass

_LOGGER = logging.getLogger(__name__)

PLATFORMS_LIST: list[Platform] = [
    Platform.SENSOR,
    Platform.BUTTON,
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
]

# Service constants
SERVICE_SET_STREAK_START = "set_streak_start"
SERVICE_UNDO_LAST_EVENT = "undo_last_event"
ATTR_DATE = "date"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up StreakHub from a config entry.

    Args:
        hass: Home Assistant instance.
        entry: Config entry to set up.

    Returns:
        True if setup was successful.
    """
    hass.data.setdefault(DOMAIN, {})

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

    # Create coordinator
    coordinator = StreakHubCoordinator(hass, store, tracker_id, entry)

    # Load initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS_LIST)

    # Register services (only once, on first entry)
    await async_setup_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.

    Args:
        hass: Home Assistant instance.
        entry: Config entry to unload.

    Returns:
        True if unload was successful.
    """
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS_LIST
    )

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle removal of a config entry.

    Removes the tracker data from storage when the config entry is deleted.

    Args:
        hass: Home Assistant instance.
        entry: Config entry being removed.
    """
    store = await async_get_or_create_store(hass)
    tracker_id = slugify(entry.data[CONF_NAME])
    await async_remove_tracker(store, tracker_id)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up StreakHub services.

    Services are registered only once, shared across all config entries.

    Args:
        hass: Home Assistant instance.
    """
    # Check if services are already registered
    if hass.services.has_service(DOMAIN, SERVICE_SET_STREAK_START):
        return

    async def handle_set_streak_start(call: ServiceCall) -> None:
        """Handle the set_streak_start service call.

        Args:
            call: Service call data.

        Raises:
            ServiceValidationError: If validation fails.
        """
        entity_ids = call.data.get("entity_id", [])
        if isinstance(entity_ids, str):
            entity_ids = [entity_ids]

        new_start_input = call.data[ATTR_DATE]

        # Convert to date if string
        if isinstance(new_start_input, str):
            new_start = date.fromisoformat(new_start_input)
        elif isinstance(new_start_input, date):
            new_start = new_start_input
        else:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_date_format",
            )

        today = dt_util.now().date()

        # Get entity registry to find config entries
        ent_reg = er.async_get(hass)

        for entity_id in entity_ids:
            # Look up entity
            entity_entry = ent_reg.async_get(entity_id)
            if entity_entry is None:
                _LOGGER.warning("Entity %s not found", entity_id)
                continue

            if entity_entry.platform != DOMAIN:
                _LOGGER.warning(
                    "Entity %s is not a StreakHub entity", entity_id
                )
                continue

            # Get coordinator from config entry
            config_entry_id = entity_entry.config_entry_id
            if config_entry_id is None or config_entry_id not in hass.data[DOMAIN]:
                _LOGGER.warning(
                    "Config entry for entity %s not found", entity_id
                )
                continue

            coordinator: StreakHubCoordinator = hass.data[DOMAIN][config_entry_id]

            # Validate
            current_start = date.fromisoformat(
                coordinator.data["streak_start"]
            )
            validation_error = validate_set_streak_start(
                current_start, new_start, today
            )

            if validation_error == "date_in_future":
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="date_in_future",
                )
            elif validation_error == "date_before_streak_start":
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

    # Register the set_streak_start service
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
        entity_ids = call.data.get("entity_id", [])
        if isinstance(entity_ids, str):
            entity_ids = [entity_ids]

        # Get entity registry to find config entries
        ent_reg = er.async_get(hass)

        for entity_id in entity_ids:
            # Look up entity
            entity_entry = ent_reg.async_get(entity_id)
            if entity_entry is None:
                _LOGGER.warning("Entity %s not found", entity_id)
                continue

            if entity_entry.platform != DOMAIN:
                _LOGGER.warning(
                    "Entity %s is not a StreakHub entity", entity_id
                )
                continue

            # Get coordinator from config entry
            config_entry_id = entity_entry.config_entry_id
            if config_entry_id is None or config_entry_id not in hass.data[DOMAIN]:
                _LOGGER.warning(
                    "Config entry for entity %s not found", entity_id
                )
                continue

            coordinator: StreakHubCoordinator = hass.data[DOMAIN][config_entry_id]

            # Execute undo
            success = await coordinator.async_undo_last_event()

            if not success:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="undo_not_possible",
                )

            _LOGGER.info("Undid last event for %s", entity_id)

    # Register the undo_last_event service
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
