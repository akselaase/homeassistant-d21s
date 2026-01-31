"""Support for DT sensors."""

from datetime import datetime
from typing import Any

import disruptive

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DEVICES, DOMAIN, SENSOR_EVENT


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    devices: list[disruptive.Device] = hass.data[DOMAIN][entry.entry_id][DEVICES]
    entities = []
    for device in devices:
        if device.device_type == disruptive.Device.TEMPERATURE:
            entities.append(DTTempSensor(device))
        elif device.device_type == disruptive.Device.HUMIDITY:
            entities.append(DTTempSensor(device))
            entities.append(DTHumiditySensor(device))

    async_add_entities(entities)


def _device_info(device: disruptive.Device) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, device.device_id)},
        name=device.display_name,
        model_id=device.product_number,
    )


class DTSensor(SensorEntity):
    """Representation of a Disruptive Technologies Sensor."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_has_entity_name = True

    _dt_event_types: set[str]
    _dt_event_attr: str

    _attr_timestamp: datetime | None = None

    def __init__(self, device: disruptive.Device) -> None:
        """Initialize DT sensor."""
        self._device_id = device.device_id
        self._attr_unique_id = f"{device.device_id}-{self._attr_device_class}"
        self._attr_device_info = _device_info(device)

    @property
    def should_poll(self) -> bool:
        """No polling for these devices."""
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Extra state attributes."""
        return {"timestamp": self._attr_timestamp}

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
        payload: dict[str],
    ):
        if device_id != self._device_id:
            return

        if event_type not in self._dt_event_types:
            return

        if self._attr_timestamp is not None and timestamp < self._attr_timestamp:
            return

        self._attr_native_value = getattr(payload, self._dt_event_attr)
        self._attr_timestamp = timestamp

        self.async_write_ha_state()


class DTTempSensor(DTSensor):
    """Representation of a Disruptive Technologies Temperature Sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_name = "Temperature"
    _dt_event_types = {disruptive.events.TEMPERATURE, disruptive.events.HUMIDITY}
    _dt_event_attr = "celsius"


class DTHumiditySensor(DTSensor):
    """Representation of a Disruptive Technologies Humidity Sensor."""

    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_name = "Humidity"
    _dt_event_types = {disruptive.events.HUMIDITY}
    _dt_event_attr = "relative_humidity"
