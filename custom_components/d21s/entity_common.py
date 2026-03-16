from datetime import datetime
import logging
from typing import Any

import disruptive

from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo, Entity

from .const import DOMAIN, SENSOR_EVENT

LOGGER = logging.getLogger(__name__)


class DTEntity(Entity):
    """Base entity for Disruptive Technologies devices."""

    _attr_has_entity_name = True
    _attr_available = True
    _attr_timestamp: datetime | None = None

    _dt_event_types: set[str]

    def __init__(self, device: disruptive.Device) -> None:
        """Initialize the entity."""
        self._device_id = device.device_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.device_id)},
            name=device.display_name,
            default_name=device.device_id,
            model_id=device.product_number,
            serial_number=device.device_id,
        )

        entity_name = self._attr_name.lower().replace(" ", "-")
        self._attr_unique_id = f"{device.device_id}-{entity_name}"

    @property
    def should_poll(self) -> bool:
        """No polling for these devices."""
        return False

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SENSOR_EVENT, self._handle_event)
        )
        await super().async_added_to_hass()

    @callback
    def _handle_event(
        self,
        device_id: str,
        event_type: str,
        timestamp: datetime,
        payload: dict[str, Any],
    ):
        if device_id != self._device_id:
            return

        # Handle connection status
        if event_type == disruptive.events.CONNECTION_STATUS:
            connection_status = getattr(payload, "connection", None)
            if connection_status == "OFFLINE":
                self._on_offline(timestamp)
            else:
                self._on_online(timestamp)
            return

        if self._attr_timestamp is not None and timestamp < self._attr_timestamp:
            LOGGER.warning(
                "Received out-of-order event for device %s: %s at %s (current timestamp: %s)",
                self._device_id,
                event_type,
                timestamp,
                self._attr_timestamp,
            )
            return

        if event_type in self._dt_event_types:
            self._attr_available = True
            self._attr_timestamp = timestamp
            self._on_event(event_type, timestamp, payload)
            self.async_write_ha_state()

    def _on_offline(self, timestamp: datetime) -> None:
        """Handle device going offline."""
        self._attr_available = False
        self.async_write_ha_state()

    def _on_online(self, timestamp: datetime) -> None:
        """Handle device coming online."""
        self._attr_available = True
        self.async_write_ha_state()

    def _on_event(
        self,
        event_type: str,
        timestamp: datetime,
        payload: dict[str, Any],
    ):
        """Handle an event."""
