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
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DEVICES, DOMAIN
from .entity_common import DTEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    devices: list[disruptive.Device] = hass.data[DOMAIN][entry.entry_id][DEVICES]
    entities = []
    common_sensors = [DTBatterySensor, DTRSSISensor, DTTransmissionModeSensor]
    for device in devices:
        if device.device_type == disruptive.Device.TEMPERATURE:
            entities.extend(sensor_cls(device) for sensor_cls in common_sensors)
            entities.append(DTTempSensor(device))
        elif device.device_type == disruptive.Device.HUMIDITY:
            entities.extend(sensor_cls(device) for sensor_cls in common_sensors)
            entities.append(DTTempSensor(device))
            entities.append(DTHumiditySensor(device))

    async_add_entities(entities)


class DTSensor(DTEntity, SensorEntity):
    """Representation of a Disruptive Technologies Sensor."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _dt_event_attr: str

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Extra state attributes."""
        return {"timestamp": self._attr_timestamp}

    def _on_offline(self, timestamp: datetime):
        self._attr_native_value = None
        return super()._on_offline(timestamp)

    def _on_event(
        self,
        event_type: str,
        timestamp: datetime,
        payload: dict[str, Any],
    ):
        self._attr_native_value = getattr(payload, self._dt_event_attr)


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


class DTBatterySensor(DTSensor):
    """Representation of a Disruptive Technologies Battery Sensor."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_name = "Battery"
    _dt_event_types = {disruptive.events.BATTERY_STATUS}
    _dt_event_attr = "percentage"


class DTRSSISensor(DTSensor):
    """Representation of a Disruptive Technologies RSSI Sensor."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_native_unit_of_measurement = "dBm"
    _attr_name = "Signal Strength"
    _dt_event_types = {disruptive.events.NETWORK_STATUS}
    _dt_event_attr = "rssi"


class DTTransmissionModeSensor(DTSensor):
    """Representation of a Disruptive Technologies Transmission Mode Sensor."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_native_unit_of_measurement = None
    _attr_state_class = None
    _attr_name = "Transmission Mode"
    _dt_event_types = {disruptive.events.NETWORK_STATUS}
    _dt_event_attr = "transmission_mode"
