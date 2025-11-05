"""Climate platform for Muller Intuis Connect."""
from __future__ import annotations

import logging
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

from .const import DOMAIN, MODE_SCHEDULE, MODE_AWAY, MODE_HG

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
    home = status.get("home", {})
    rooms = home.get("rooms", [])
    
    _LOGGER.info("Creating %d climate entities", len(rooms))
    
    for room in rooms:
        entities.append(MullerIntuisClimate(coordinator, api_client, room))
    
    async_add_entities(entities)
    _LOGGER.info("Climate platform setup completed with %d entities", len(entities))


class MullerIntuisClimate(CoordinatorEntity, ClimateEntity):
    """Representation of a Muller Intuis climate device."""

    _attr_has_entity_name = True
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
    )
    _attr_hvac_modes = [HVACMode.AUTO, HVACMode.HEAT, HVACMode.OFF]
    _attr_preset_modes = [PRESET_HOME, PRESET_AWAY, "frost_protection"]

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
        home = status.get("home", {})
        rooms = home.get("rooms", [])
        
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
        
        # Get home mode
        status = self.coordinator.data.get("status", {})
        home = status.get("home", {})
        therm_mode = home.get("therm_mode")
        
        if therm_mode == MODE_SCHEDULE:
            return HVACMode.AUTO
        elif therm_mode == MODE_AWAY:
            return HVACMode.AUTO  # Away is still auto mode
        elif therm_mode == MODE_HG:
            return HVACMode.OFF
        else:
            # Check room setpoint mode
            setpoint_mode = room.get("therm_setpoint_mode")
            if setpoint_mode == "manual":
                return HVACMode.HEAT
            return HVACMode.AUTO

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode."""
        status = self.coordinator.data.get("status", {})
        home = status.get("home", {})
        therm_mode = home.get("therm_mode")
        
        if therm_mode == MODE_SCHEDULE:
            return PRESET_HOME
        elif therm_mode == MODE_AWAY:
            return PRESET_AWAY
        elif therm_mode == MODE_HG:
            return "frost_protection"
        
        # Check if manual mode
        room = self._get_room_data()
        if room and room.get("therm_setpoint_mode") == "manual":
            return "manual"
        
        return PRESET_HOME

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        
        _LOGGER.info("Setting temperature to %s for room %s", temperature, self._attr_name)
        
        try:
            await self.api_client.set_room_thermpoint(
                self._home_id,
                self._room_id,
                "manual",
                temperature
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Error setting temperature: %s", err)
            raise

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        _LOGGER.info("Setting HVAC mode to %s for room %s", hvac_mode, self._attr_name)
        
        try:
            if hvac_mode == HVACMode.AUTO:
                # Set to schedule mode
                await self.api_client.set_therm_mode(self._home_id, MODE_SCHEDULE)
            elif hvac_mode == HVACMode.HEAT:
                # Set to manual mode with current setpoint
                room = self._get_room_data()
                temp = room.get("therm_setpoint_temperature", 19) if room else 19
                await self.api_client.set_room_thermpoint(
                    self._home_id,
                    self._room_id,
                    "manual",
                    temp
                )
            elif hvac_mode == HVACMode.OFF:
                # Set to frost protection
                await self.api_client.set_therm_mode(self._home_id, MODE_HG)
            
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Error setting HVAC mode: %s", err)
            raise

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        _LOGGER.info("Setting preset mode to %s for room %s", preset_mode, self._attr_name)
        
        try:
            if preset_mode == PRESET_HOME:
                await self.api_client.set_therm_mode(self._home_id, MODE_SCHEDULE)
            elif preset_mode == PRESET_AWAY:
                await self.api_client.set_therm_mode(self._home_id, MODE_AWAY)
            elif preset_mode == "frost_protection":
                await self.api_client.set_therm_mode(self._home_id, MODE_HG)
            
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Error setting preset mode: %s", err)
            raise
