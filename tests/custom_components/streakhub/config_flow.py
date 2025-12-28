"""Config flow for StreakHub integration."""

from __future__ import annotations

from datetime import date
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers import selector
from homeassistant.util import slugify

from .const import CONF_INITIAL_DATE, CONF_NAME, DOMAIN


class StreakHubConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for StreakHub."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step.

        Allows the user to create a new StreakHub tracker with a name
        and optional initial start date.
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            # Generate unique ID from name
            unique_id = slugify(user_input[CONF_NAME])

            # Check for duplicates
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            # Normalize initial_date to ISO string if provided
            initial_date = user_input.get(CONF_INITIAL_DATE)
            if initial_date is None:
                initial_date = date.today().isoformat()
            elif isinstance(initial_date, date):
                initial_date = initial_date.isoformat()

            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data={
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_INITIAL_DATE: initial_date,
                },
            )

        # Show the form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME): str,
                    vol.Optional(
                        CONF_INITIAL_DATE,
                        default=date.today().isoformat(),
                    ): selector.DateSelector(),
                }
            ),
            errors=errors,
        )
