"""Sensor platform for Muller Intuis Connect."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Muller Intuis sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    
    entities = []
    
    # Get rooms
    status = coordinator.data.get("status", {})
    rooms_status = status.get("rooms", [])
    rooms_info = status.get("rooms_info", [])
    
    rooms_map = {room["id"]: room for room in rooms_info}
    
    for room_status in rooms_status:
        room_id = room_status.get("id")
        room_info = rooms_map.get(room_id, {})
        room_data = {**room_info, **room_status}
        
        # Temperature sensor
        entities.append(MullerIntuisTemperatureSensor(coordinator, room_data))
        # Heating power sensor
        entities.append(MullerIntuisHeatingPowerSensor(coordinator, room_data))
        
    async_add_entities(entities)
    _LOGGER.info("Sensor platform setup completed with %d entities", len(entities))


class MullerIntuisSensorBase(CoordinatorEntity, SensorEntity):
    """Base class for Muller Intuis sensors."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, room_data: dict[str, Any], sensor_type: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._room_id = room_data["id"]
        self._room_name = room_data.get("name", "Unknown Room")
        self._sensor_type = sensor_type
        self._attr_unique_id = f"{self._room_id}_{sensor_type}"

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._room_id)},
            "name": self._room_name,
            "manufacturer": "Muller Intuitiv",
            "model": "Radiateur connecté",
        }

    def _get_room_data(self) -> dict[str, Any] | None:
        """Get current room data from coordinator."""
        status = self.coordinator.data.get("status", {})
        rooms = status.get("rooms", [])
        
        for room in rooms:
            if room.get("id") == self._room_id:
                return room
        return None


class MullerIntuisTemperatureSensor(MullerIntuisSensorBase):
    """Temperature sensor for Muller Intuis."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, room_data: dict[str, Any]) -> None:
        """Initialize the temperature sensor."""
        super().__init__(coordinator, room_data, "temperature")
        self._attr_name = "Température"

    @property
    def native_value(self) -> float | None:
        """Return the temperature value."""
        room = self._get_room_data()
        if room:
            return room.get("therm_measured_temperature")
        return None


class MullerIntuisHeatingPowerSensor(MullerIntuisSensorBase):
    """Heating power sensor for Muller Intuis."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:radiator"

    def __init__(self, coordinator, room_data: dict[str, Any]) -> None:
        """Initialize the heating power sensor."""
        super().__init__(coordinator, room_data, "heating_power")
        self._attr_name = "Puissance de chauffe"

    @property
    def native_value(self) -> int | None:
        """Return the heating power value (percentage)."""
        room = self._get_room_data()
        if room:
            return room.get("heating_power_request", 0)
        return None
