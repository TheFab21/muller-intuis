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
from homeassistant.const import (
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Muller Intuis sensor devices."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Attendre que les données soient chargées
    await coordinator.async_update_data()
    
    # Créer les capteurs pour chaque pièce
    entities = []
    rooms = coordinator.data.get("rooms", [])
    
    for room in rooms:
        # Température mesurée
        entities.append(
            MullerIntuisTemperatureSensor(coordinator, room)
        )
        
        # Puissance de chauffe
        entities.append(
            MullerIntuisHeatingPowerSensor(coordinator, room)
        )
        
        # Énergie quotidienne (si disponible)
        if "energy_day" in room:
            entities.append(
                MullerIntuisEnergySensor(coordinator, room)
            )
    
    async_add_entities(entities, True)


class MullerIntuisSensorBase(SensorEntity):
    """Base class for Muller Intuis sensors."""
    
    def __init__(self, coordinator, room: dict) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._room = room
        self._room_id = room["id"]
        room_name = room.get("name") or room.get("module_name") or room.get("id")
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._room_id)},
            "name": room_name,
            "manufacturer": "Muller Intuitiv",
            "model": "Intuis Connect",
        }
    
    async def async_update(self) -> None:
        """Update the entity."""
        await self.coordinator.async_update_data()
        self._update_room_data()
    
    def _update_room_data(self) -> None:
        """Update room data from coordinator."""
        rooms = self.coordinator.data.get("rooms", [])
        for room in rooms:
            if room["id"] == self._room_id:
                self._room = room
                break


class MullerIntuisTemperatureSensor(MullerIntuisSensorBase):
    """Temperature sensor for Muller Intuis."""
    
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    
    def __init__(self, coordinator, room: dict) -> None:
        """Initialize the temperature sensor."""
        super().__init__(coordinator, room)
        room_name = room.get("name") or room.get("module_name") or room.get("id")
        self._attr_name = f"Muller {room_name} Temperature"
        self._attr_unique_id = f"muller_{self._room_id}_temperature"
    
    @property
    def native_value(self) -> float | None:
        """Return the current temperature."""
        return self._room.get("therm_measured_temperature")


class MullerIntuisHeatingPowerSensor(MullerIntuisSensorBase):
    """Heating power sensor for Muller Intuis."""
    
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:radiator"
    
    def __init__(self, coordinator, room: dict) -> None:
        """Initialize the heating power sensor."""
        super().__init__(coordinator, room)
        room_name = room.get("name") or room.get("module_name") or room.get("id")
        self._attr_name = f"Muller {room_name} Heating Power"
        self._attr_unique_id = f"muller_{self._room_id}_heating_power"
    
    @property
    def native_value(self) -> int | None:
        """Return the heating power request."""
        return self._room.get("heating_power_request", 0)


class MullerIntuisEnergySensor(MullerIntuisSensorBase):
    """Daily energy sensor for Muller Intuis."""
    
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    
    def __init__(self, coordinator, room: dict) -> None:
        """Initialize the energy sensor."""
        super().__init__(coordinator, room)
        room_name = room.get("name") or room.get("module_name") or room.get("id")
        self._attr_name = f"Muller {room_name} Daily Energy"
        self._attr_unique_id = f"muller_{self._room_id}_daily_energy"
    
    @property
    def native_value(self) -> float | None:
        """Return the daily energy consumption."""
        energy = self._room.get("energy_day")
        if energy is not None:
            # Convertir de Wh en kWh
            return energy / 1000
        return None
