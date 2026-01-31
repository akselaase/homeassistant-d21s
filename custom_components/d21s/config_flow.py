"""Config flow for the Disruptive Technologies integration."""

from __future__ import annotations

import logging
from typing import Any

import disruptive
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_API_KEY, CONF_CLIENT_SECRET, CONF_EMAIL
from homeassistant.core import HomeAssistant

from .api import D21sAPI
from .const import CONF_PROJECT, DOMAIN
from .errors import InvalidAuth

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_API_KEY): str,
        vol.Required(CONF_CLIENT_SECRET): str,
        vol.Required(CONF_PROJECT): str,
    }
)


async def validate_input(
    hass: HomeAssistant, data: dict[str, Any]
) -> disruptive.Project:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    api = D21sAPI(data[CONF_EMAIL], data[CONF_API_KEY], data[CONF_CLIENT_SECRET])
    return await hass.async_add_executor_job(api.get_project, data[CONF_PROJECT])


class ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Disruptive Technologies."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                project = await validate_input(self.hass, user_input)
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(project.id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=project.display_name, data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
