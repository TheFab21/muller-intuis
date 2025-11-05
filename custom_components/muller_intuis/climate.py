"""Climate platform for Muller Intuis Connect."""
from __future__ import annotations

import logging
import time
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
    PRESET_AWAY,
    PRESET_HOME,
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
    MODE_SCHEDULE,
    MODE_AWAY,
    MODE_HOME_HG,
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
    
    status = coordinator.data.get("status", {})
    rooms_status = status.get("rooms", [])
    rooms_info = status.get("rooms_info", [])
    
    rooms_map = {room["id"]: room for room in rooms_info}
    
    # Add home climate entity (controls entire house)
    entities.append(MullerIntuisHomeClimate(coordinator, api_client))
    _LOGGER.info("Added home climate entity: %s", coordinator.home_name)
    
    # Add room climate entities (one per room)
    for room_status in rooms_status:
        room_id = room_status.get("id")
        room_info = rooms_map.get(room_id, {})
        room_data = {**room_info, **room_status}
        entities.append(MullerIntuisRoomClimate(coordinator, api_client, room_data))
    
    async_add_entities(entities)
    _LOGGER.info("Climate platform setup: 1 home + %d rooms = %d entities", len(rooms_status), len(entities))


class MullerIntuisHomeClimate(CoordinatorEntity, ClimateEntity):
    """Climate entity for the entire home."""

    _attr_has_entity_name = False
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = 0
    _attr_hvac_modes = [HVACMode.AUTO, HVACMode.OFF]
    _attr_preset_modes = [PRESET_HOME, PRESET_AWAY, "frost_protection"]

    def __init__(self, coordinator, api_client) -> None:
        """Initialize the home climate device."""
        super().__init__(coordinator)
        self.api_client = api_client
        self._home_id = coordinator.home_id
        self._home_name = coordinator.home_name
        self._attr_unique_id = f"{self._home_id}_home_climate"
        self._attr_name = self._home_name
        
        _LOGGER.info("Creating home climate: %s (ID: %s)", self._home_name, self._home_id)

    @property
    def device_info(self):
        """Return device info for home."""
        return {
            "identifiers": {(DOMAIN, f"{self._home_id}_home")},
            "name": f"Système de chauffage",
            "manufacturer": "Muller Intuitiv",
            "model": "Contrôle central",
        }

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current operation mode."""
        status = self.coordinator.data.get("status", {})
        therm_mode = status.get("therm_mode")
        
        if therm_mode in [MODE_SCHEDULE, MODE_AWAY]:
            return HVACMode.AUTO
        elif therm_mode == MODE_HOME_HG:
            return HVACMode.OFF
        return HVACMode.AUTO

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode."""
        status = self.coordinator.data.get("status", {})
        therm_mode = status.get("therm_mode")
        
        if therm_mode == MODE_SCHEDULE:
            return PRESET_HOME
        elif therm_mode == MODE_AWAY:
            return PRESET_AWAY
        elif therm_mode == MODE_HOME_HG:
            return "frost_protection"
        
        return PRESET_HOME

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        _LOGGER.info("Setting home HVAC mode to %s", hvac_mode)
        
        try:
            if hvac_mode == HVACMode.AUTO:
                await self.api_client.set_therm_mode(self._home_id, MODE_SCHEDULE)
            elif hvac_mode == HVACMode.OFF:
                await self.api_client.set_therm_mode(self._home_id, MODE_HOME_HG)
            
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Error setting home HVAC mode: %s", err)
            raise

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        _LOGGER.info("Setting home preset mode to %s", preset_mode)
        
        try:
            if preset_mode == PRESET_HOME:
                await self.api_client.set_therm_mode(self._home_id, MODE_SCHEDULE)
            elif preset_mode == PRESET_AWAY:
                await self.api_client.set_therm_mode(self._home_id, MODE_AWAY, end_time=0)
            elif preset_mode == "frost_protection":
                await self.api_client.set_therm_mode(self._home_id, MODE_HOME_HG, end_time=0)
            
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Error setting home preset mode: %s", err)
            raise

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        status = self.coordinator.data.get("status", {})
        
        attrs = {
            "home_id": self._home_id,
            "therm_mode": status.get("therm_mode"),
        }
        
        schedules = status.get("schedules", [])
        for schedule in schedules:
            if schedule.get("type") == "therm" and schedule.get("selected"):
                attrs["active_schedule"] = schedule.get("name")
                break
        
        return attrs


class MullerIntuisRoomClimate(CoordinatorEntity, ClimateEntity):
    """Climate entity for a single room/heater."""

    _attr_has_entity_name = False
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_hvac_modes = [HVACMode.AUTO, HVACMode.HEAT, HVACMode.OFF]
    _attr_min_temp = 7
    _attr_max_temp = 30
    _attr_target_temperature_step = 0.5

    def __init__(self, coordinator, api_client, room_data: dict[str, Any]) -> None:
        """Initialize the room climate device."""
        super().__init__(coordinator)
        self.api_client = api_client
        self._room_id = room_data["id"]
        self._room_name = room_data.get("name", "Unknown Room")
        self._attr_unique_id = f"{self._room_id}_climate"
        self._attr_name = self._room_name
        self._home_id = coordinator.home_id

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._room_id)},
            "name": self._room_name,
            "manufacturer": "Muller Intuitiv",
            "model": "Radiateur connecté",
            "via_device": (DOMAIN, f"{self._home_id}_home"),
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
        
        if setpoint_mode == MODE_MANUAL:
            return HVACMode.HEAT
        elif setpoint_mode in [MODE_OFF, MODE_HG]:
            return HVACMode.OFF
        else:
            return HVACMode.AUTO

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        
        _LOGGER.info("Setting temperature to %s°C for %s (manual, %dm)", 
                    temperature, self._room_name, DEFAULT_MANUAL_DURATION)
        
        try:
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
        _LOGGER.info("Setting HVAC mode to %s for %s", hvac_mode, self._room_name)
        
        try:
            if hvac_mode == HVACMode.AUTO:
                await self.api_client.set_room_state(self._home_id, self._room_id, MODE_HOME)
            elif hvac_mode == HVACMode.HEAT:
                room = self._get_room_data()
                temp = room.get("therm_setpoint_temperature", 19) if room else 19
                await self.api_client.set_room_state(
                    self._home_id, self._room_id, MODE_MANUAL, temp, DEFAULT_MANUAL_DURATION
                )
            elif hvac_mode == HVACMode.OFF:
                await self.api_client.set_room_state(self._home_id, self._room_id, MODE_OFF)
            
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
        
        if room.get("therm_setpoint_end_time"):
            attrs["manual_mode_end_time"] = room["therm_setpoint_end_time"]
        
        if "heating_power_request" in room:
            attrs["heating_power_request"] = room["heating_power_request"]
        
        if "reachable" in room:
            attrs["reachable"] = room["reachable"]
        
        if "open_window" in room:
            attrs["open_window"] = room["open_window"]
        
        if "anticipating" in room:
            attrs["anticipating"] = room["anticipating"]
        
        return attrs
