"""The Disruptive Technologies integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_CLIENT_SECRET, CONF_EMAIL, Platform
from homeassistant.core import HomeAssistant

from .api import D21sAPI
from .const import CONF_PROJECT, DEVICES, DOMAIN
from .streamer import Streamer

_PLATFORMS: list[Platform] = [Platform.EVENT, Platform.SENSOR]

type D21sConfigEntry = ConfigEntry[D21sAPI]


async def async_setup_entry(hass: HomeAssistant, entry: D21sConfigEntry) -> bool:
    """Set up Disruptive Technologies from a config entry."""

    api = D21sAPI(
        email=entry.data[CONF_EMAIL],
        key_id=entry.data[CONF_API_KEY],
        secret=entry.data[CONF_CLIENT_SECRET],
    )
    project = await hass.async_add_executor_job(
        api.get_project, entry.data[CONF_PROJECT]
    )

    devices = await hass.async_add_executor_job(api.get_devices, project.project_id)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {DEVICES: devices}

    streamer = Streamer(hass, api)
    entry.async_create_background_task(
        hass, streamer.stream_forever(project.project_id), "event-stream"
    )

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: D21sConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
