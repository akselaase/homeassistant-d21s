"""Support for DT events."""

from datetime import datetime
from typing import Any

import disruptive

from homeassistant.components.event import EventEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DEVICES, DOMAIN
from .entity_common import DTEntity

SENSORS_WITH_TOUCH = {
    disruptive.Device.TEMPERATURE,
    disruptive.Device.HUMIDITY,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the event platform."""
    devices: list[disruptive.Device] = hass.data[DOMAIN][entry.entry_id][DEVICES]
    entities = [
        DTTouchEvent(device)
        for device in devices
        if device.device_type in SENSORS_WITH_TOUCH
    ]
    async_add_entities(entities)


class DTTouchEvent(DTEntity, EventEntity):
    """Representation of a Disruptive Technologies Touch Event."""

    _attr_name = "Touch"
    _attr_event_types = ["touch"]
    _dt_event_types = {disruptive.events.TOUCH}

    def _on_event(
        self,
        event_type: str,
        timestamp: datetime,
        payload: dict[str, Any],
    ):
        self._trigger_event("touch", {"timestamp": timestamp})
