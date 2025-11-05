"""Climate platform for Muller Intuis Connect."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MODE_MANUAL,
    MODE_HOME,
    MODE_OFF,
    MODE_HG,
    DEFAULT_MANUAL_DURATION,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Muller Intuis climate platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api_client = hass.data[DOMAIN][entry.entry_id]["api_client"]
    
    entities = []
    
    # Get rooms from coordinator data
    status = coordinator.data.get("status", {})
    rooms_status = status.get("rooms", [])
    rooms_info = status.get("rooms_info", [])
    
    # Create a map of room_id -> room_info
    rooms_map = {room["id"]: room for room in rooms_info}
    
    _LOGGER.info("Creating %d climate entities", len(rooms_status))
    
    for room_status in rooms_status:
        room_id = room_status.get("id")
        room_info = rooms_map.get(room_id, {})
        
        # Merge info and status
        room_data = {**room_info, **room_status}
        entities.append(MullerIntuisClimate(coordinator, api_client, room_data))
    
    async_add_entities(entities)
    _LOGGER.info("Climate platform setup completed with %d entities", len(entities))


class MullerIntuisClimate(CoordinatorEntity, ClimateEntity):
    """Representation of a Muller Intuis climate device."""

    _attr_has_entity_name = True
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_hvac_modes = [HVACMode.AUTO, HVACMode.HEAT, HVACMode.OFF]
    _attr_min_temp = 7
    _attr_max_temp = 30
    _attr_target_temperature_step = 0.5

    def __init__(self, coordinator, api_client, room_data: dict[str, Any]) -> None:
        """Initialize the climate device."""
        super().__init__(coordinator)
        self.api_client = api_client
        self._room_id = room_data["id"]
        self._attr_name = room_data.get("name", "Unknown Room")
        self._attr_unique_id = f"{self._room_id}_climate"
        self._home_id = coordinator.home_id
        
        _LOGGER.debug("Created climate entity for room: %s (ID: %s)", self._attr_name, self._room_id)

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._room_id)},
            "name": self._attr_name,
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

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        room = self._get_room_data()
        if room:
            return room.get("therm_measured_temperature")
        return None

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        room = self._get_room_data()
        if room:
            return room.get("therm_setpoint_temperature")
        return None

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current operation mode."""
        room = self._get_room_data()
        if not room:
            return HVACMode.AUTO
        
        setpoint_mode = room.get("therm_setpoint_mode")
        
        # Map room modes to HVAC modes
        if setpoint_mode == MODE_MANUAL:
            return HVACMode.HEAT
        elif setpoint_mode == MODE_OFF:
            return HVACMode.OFF
        elif setpoint_mode == MODE_HG:
            return HVACMode.OFF
        else:  # home, schedule, etc.
            return HVACMode.AUTO

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        
        _LOGGER.info("Setting temperature to %s°C for %s (mode: manual, duration: %dm)", 
                    temperature, self._attr_name, DEFAULT_MANUAL_DURATION)
        
        try:
            # Set manual mode with temperature and default duration
            await self.api_client.set_room_state(
                self._home_id,
                self._room_id,
                MODE_MANUAL,
                temperature,
                DEFAULT_MANUAL_DURATION
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Error setting temperature: %s", err)
            raise

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        _LOGGER.info("Setting HVAC mode to %s for %s", hvac_mode, self._attr_name)
        
        try:
            if hvac_mode == HVACMode.AUTO:
                # Follow home schedule
                await self.api_client.set_room_state(
                    self._home_id,
                    self._room_id,
                    MODE_HOME
                )
            elif hvac_mode == HVACMode.HEAT:
                # Manual mode with current/default temperature
                room = self._get_room_data()
                temp = room.get("therm_setpoint_temperature", 19) if room else 19
                await self.api_client.set_room_state(
                    self._home_id,
                    self._room_id,
                    MODE_MANUAL,
                    temp,
                    DEFAULT_MANUAL_DURATION
                )
            elif hvac_mode == HVACMode.OFF:
                # Turn off this room
                await self.api_client.set_room_state(
                    self._home_id,
                    self._room_id,
                    MODE_OFF
                )
            
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Error setting HVAC mode: %s", err)
            raise

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        room = self._get_room_data()
        if not room:
            return {}
        
        attrs = {
            "room_id": self._room_id,
            "setpoint_mode": room.get("therm_setpoint_mode"),
        }
        
        # Add end time if in manual mode
        if room.get("therm_setpoint_end_time"):
            attrs["manual_mode_end_time"] = room["therm_setpoint_end_time"]
        
        # Add heating status
        if "heating_power_request" in room:
            attrs["heating_power_request"] = room["heating_power_request"]
        
        # Add reachable status
        if "reachable" in room:
            attrs["reachable"] = room["reachable"]
        
        # Add open window detection
        if "open_window" in room:
            attrs["open_window"] = room["open_window"]
        
        # Add anticipating
        if "anticipating" in room:
            attrs["anticipating"] = room["anticipating"]
        
        return attrs
