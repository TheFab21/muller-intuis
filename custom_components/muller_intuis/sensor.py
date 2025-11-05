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
from homeassistant.const import UnitOfTemperature, UnitOfPower, UnitOfEnergy
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
    
    # Get rooms from coordinator data
    status = coordinator.data.get("status", {})
    home = status.get("home", {})
    rooms = home.get("rooms", [])
    
    _LOGGER.info("Creating sensor entities for %d rooms", len(rooms))
    
    for room in rooms:
        # Temperature sensor
        entities.append(MullerIntuisTemperatureSensor(coordinator, room))
        # Heating power sensor
        entities.append(MullerIntuisHeatingPowerSensor(coordinator, room))
        # Window open sensor
        entities.append(MullerIntuisWindowOpenSensor(coordinator, room))
        # Anticipating sensor
        entities.append(MullerIntuisAnticipat ingSensor(coordinator, room))
        # Reachable sensor
        entities.append(MullerIntuisReachableSensor(coordinator, room))
        
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
        home = status.get("home", {})
        rooms = home.get("rooms", [])
        
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

    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.WATT

    def __init__(self, coordinator, room_data: dict[str, Any]) -> None:
        """Initialize the heating power sensor."""
        super().__init__(coordinator, room_data, "heating_power")
        self._attr_name = "Puissance de chauffe"

    @property
    def native_value(self) -> int | None:
        """Return the heating power value."""
        room = self._get_room_data()
        if room:
            # heating_power_request is a percentage, need to convert to watts
            # Assuming average radiator power of 1500W
            power_request = room.get("heating_power_request", 0)
            if power_request is not None:
                return int((power_request / 100) * 1500)
        return None


class MullerIntuisWindowOpenSensor(MullerIntuisSensorBase):
    """Window open sensor for Muller Intuis."""

    _attr_device_class = None

    def __init__(self, coordinator, room_data: dict[str, Any]) -> None:
        """Initialize the window open sensor."""
        super().__init__(coordinator, room_data, "window_open")
        self._attr_name = "Fenêtre ouverte"

    @property
    def native_value(self) -> str | None:
        """Return the window open status."""
        room = self._get_room_data()
        if room:
            open_window = room.get("open_window")
            if open_window is True:
                return "Ouverte"
            elif open_window is False:
                return "Fermée"
        return "Inconnue"

    @property
    def icon(self) -> str:
        """Return icon."""
        room = self._get_room_data()
        if room and room.get("open_window"):
            return "mdi:window-open-variant"
        return "mdi:window-closed-variant"


class MullerIntuisAnticipat ingSensor(MullerIntuisSensorBase):
    """Anticipating sensor for Muller Intuis."""

    _attr_device_class = None

    def __init__(self, coordinator, room_data: dict[str, Any]) -> None:
        """Initialize the anticipating sensor."""
        super().__init__(coordinator, room_data, "anticipating")
        self._attr_name = "Anticipation"

    @property
    def native_value(self) -> str | None:
        """Return the anticipating status."""
        room = self._get_room_data()
        if room:
            anticipating = room.get("anticipating")
            if anticipating is True:
                return "Actif"
            elif anticipating is False:
                return "Inactif"
        return "Inconnu"

    @property
    def icon(self) -> str:
        """Return icon."""
        return "mdi:clock-fast"


class MullerIntuisReachableSensor(MullerIntuisSensorBase):
    """Reachable sensor for Muller Intuis."""

    _attr_device_class = None

    def __init__(self, coordinator, room_data: dict[str, Any]) -> None:
        """Initialize the reachable sensor."""
        super().__init__(coordinator, room_data, "reachable")
        self._attr_name = "Connecté"

    @property
    def native_value(self) -> str | None:
        """Return the reachable status."""
        room = self._get_room_data()
        if room:
            reachable = room.get("reachable")
            if reachable is True:
                return "En ligne"
            elif reachable is False:
                return "Hors ligne"
        return "Inconnu"

    @property
    def icon(self) -> str:
        """Return icon."""
        room = self._get_room_data()
        if room and room.get("reachable"):
            return "mdi:wifi"
        return "mdi:wifi-off"
