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
    
    # Add home climate entity FIRST
    home_entity = MullerIntuisHomeClimate(coordinator, api_client)
    entities.append(home_entity)
    
    # Add room climate entities
    for room_status in rooms_status:
        room_id = room_status.get("id")
        room_info = rooms_map.get(room_id, {})
        room_data = {**room_info, **room_status}
        room_entity = MullerIntuisRoomClimate(coordinator, api_client, room_data)
        entities.append(room_entity)
    
    async_add_entities(entities)
    _LOGGER.info("Climate setup: 1 home + %d rooms = %d entities", len(rooms_status), len(entities))


class MullerIntuisHomeClimate(CoordinatorEntity, ClimateEntity):
    """Climate entity for the entire home."""

    _attr_has_entity_name = False
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.AUTO, HVACMode.HEAT, HVACMode.OFF]
    _attr_preset_modes = [PRESET_HOME, PRESET_AWAY, "frost_protection"]
    _attr_supported_features = ClimateEntityFeature.PRESET_MODE

    def __init__(self, coordinator, api_client) -> None:
        """Initialize the home climate device."""
        super().__init__(coordinator)
        self.api_client = api_client
        self._home_id = coordinator.home_id
        self._home_name = coordinator.home_name
        self._attr_unique_id = f"{self._home_id}_home_climate"
        self._attr_name = self._home_name

    @property
    def supported_features(self) -> ClimateEntityFeature:
        """Return the list of supported features."""
        return ClimateEntityFeature(0)

    @property
    def device_info(self):
        """Return device info for home."""
        return {
            "identifiers": {(DOMAIN, f"{self._home_id}_home")},
            "name": "Système de chauffage",
            "manufacturer": "Muller Intuitiv",
            "model": "Contrôle central",
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current operation mode."""
        status = self.coordinator.data.get("status", {})
        therm_mode = status.get("therm_mode")
        
        # Vérifier si toutes les pièces sont OFF
        rooms = status.get("rooms", [])
        if rooms:
            all_off = all(room.get("therm_setpoint_mode") == "off" for room in rooms)
            if all_off:
                return HVACMode.OFF
        
        # Map API modes to HVAC modes
        if therm_mode == MODE_SCHEDULE:
            return HVACMode.AUTO  # Schedule = Auto
        elif therm_mode == MODE_AWAY:
            return HVACMode.HEAT  # Away = Heat (temporary mode)
        elif therm_mode == MODE_HOME_HG:
            return HVACMode.OFF  # Frost protection = Off (devrait être preset)
        
        return HVACMode.AUTO

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode."""
        status = self.coordinator.data.get("status", {})
        therm_mode = status.get("therm_mode")
        
        if therm_mode == MODE_SCHEDULE:
            return PRESET_HOME  # "schedule"
        elif therm_mode == MODE_AWAY:
            return PRESET_AWAY  # "away"
        elif therm_mode == MODE_HOME_HG:
            return "frost_protection"  # "hg"
        
        return PRESET_HOME

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        _LOGGER.info("Setting home HVAC mode to %s", hvac_mode)
        
        try:
            status = self.coordinator.data.get("status", {})
            rooms = status.get("rooms", [])
            
            if hvac_mode == HVACMode.AUTO:
                # Auto = Schedule mode + remettre les pièces en mode home
                await self.api_client.set_therm_mode(self._home_id, MODE_SCHEDULE)
                await self.api_client.set_all_rooms_mode(self._home_id, rooms, "home")
                
            elif hvac_mode == HVACMode.HEAT:
                # Heat = Away mode + remettre les pièces en mode home
                await self.api_client.set_therm_mode(self._home_id, MODE_AWAY)
                await self.api_client.set_all_rooms_mode(self._home_id, rooms, "home")
                
            elif hvac_mode == HVACMode.OFF:
                # Off = Éteindre toutes les pièces
                _LOGGER.info("Turning OFF all rooms")
                await self.api_client.set_all_rooms_off(self._home_id, rooms)
            
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Error setting home HVAC mode: %s", err)
            raise

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        _LOGGER.info("Setting home preset mode to %s", preset_mode)
        
        try:
            status = self.coordinator.data.get("status", {})
            rooms = status.get("rooms", [])
            
            if preset_mode == PRESET_HOME:
                # "schedule"
                await self.api_client.set_therm_mode(self._home_id, MODE_SCHEDULE)
                await self.api_client.set_all_rooms_mode(self._home_id, rooms, "home")
            elif preset_mode == PRESET_AWAY:
                # "away" (sans endtime = permanent)
                await self.api_client.set_therm_mode(self._home_id, MODE_AWAY)
                await self.api_client.set_all_rooms_mode(self._home_id, rooms, "home")
            elif preset_mode == "frost_protection":
                # "hg" (hors-gel) + mettre toutes les pièces en hg
                await self.api_client.set_therm_mode(self._home_id, MODE_HOME_HG)
                await self.api_client.set_all_rooms_mode(self._home_id, rooms, "hg")
            
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
    def supported_features(self) -> ClimateEntityFeature:
        """Return the list of supported features."""
        return ClimateEntityFeature.TARGET_TEMPERATURE

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.last_update_success:
            return False
        room = self._get_room_data()
        if room:
            return room.get("reachable", True)
        return False

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
        
        _LOGGER.info("Setting temperature to %s°C for %s", temperature, self._room_name)
        
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
