"""Climate platform for Muller Intuis Connect."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
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

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Presets personnalisés
PRESET_SCHEDULE = "schedule"
PRESET_MANUAL = "manual"
PRESET_FROST_PROTECTION = "frost_protection"

# Mapping des modes HVAC vers les modes API
HVAC_MODE_TO_API = {
    HVACMode.AUTO: "schedule",      # Mode planning
    HVACMode.HEAT: "manual",        # Mode manuel avec température
    HVACMode.OFF: "off",            # VRAI arrêt complet (nouveau)
}

# Mapping des presets vers les modes API
PRESET_TO_API = {
    PRESET_SCHEDULE: "schedule",
    PRESET_MANUAL: "manual",
    PRESET_AWAY: "away",
    PRESET_FROST_PROTECTION: "hg",  # Hors-gel
}

# Mapping inverse
API_TO_HVAC_MODE = {v: k for k, v in HVAC_MODE_TO_API.items()}
API_TO_HVAC_MODE["hg"] = HVACMode.OFF  # hg affiche comme OFF dans l'interface
API_TO_HVAC_MODE["away"] = HVACMode.AUTO  # away affiche comme AUTO

API_TO_PRESET = {v: k for k, v in PRESET_TO_API.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Muller Intuis climate devices."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Attendre que les données soient chargées
    await coordinator.async_update_data()
    
    # Créer une entité climate pour chaque pièce
    entities = []
    rooms = coordinator.data.get("rooms", [])
    
    _LOGGER.debug("Found %d rooms", len(rooms))
    
    for room in rooms:
        _LOGGER.debug("Room data: %s", room)
        entities.append(MullerIntuisClimate(coordinator, room))
    
    async_add_entities(entities, True)


class MullerIntuisClimate(ClimateEntity):
    """Representation of a Muller Intuis Climate device."""
    
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
    )
    _attr_hvac_modes = [
        HVACMode.AUTO,   # Mode planning
        HVACMode.HEAT,   # Mode manuel
        HVACMode.OFF,    # Arrêt complet
    ]
    _attr_preset_modes = [
        PRESET_SCHEDULE,
        PRESET_MANUAL,
        PRESET_AWAY,
        PRESET_FROST_PROTECTION,
    ]
    
    def __init__(self, coordinator, room: dict) -> None:
        """Initialize the climate device."""
        self.coordinator = coordinator
        self._room = room
        self._room_id = room["id"]
        # Le nom peut être dans 'name' ou dans 'module_name' selon la structure API
        room_name = room.get("name") or room.get("module_name") or room.get("id")
        self._attr_name = f"Muller {room_name}"
        self._attr_unique_id = f"muller_{self._room_id}"
        
        # Min/Max températures
        self._attr_min_temp = 7.0
        self._attr_max_temp = 30.0
        self._attr_target_temperature_step = 0.5
    
    @property
    def device_info(self):
        """Return device information."""
        room_name = self._room.get("name") or self._room.get("module_name") or self._room.get("id")
        return {
            "identifiers": {(DOMAIN, self._room_id)},
            "name": room_name,
            "manufacturer": "Muller Intuitiv",
            "model": "Intuis Connect",
        }
    
    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self._room.get("therm_measured_temperature")
    
    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        return self._room.get("therm_setpoint_temperature")
    
    @property
    def hvac_mode(self) -> HVACMode:
        """Return current HVAC mode."""
        # Mode global de la maison
        home_mode = self.coordinator.data.get("therm_mode")
        
        # Convertir le mode API en mode HVAC
        if home_mode in API_TO_HVAC_MODE:
            return API_TO_HVAC_MODE[home_mode]
        
        # Par défaut, retourner AUTO
        return HVACMode.AUTO
    
    @property
    def preset_mode(self) -> str | None:
        """Return current preset mode."""
        home_mode = self.coordinator.data.get("therm_mode")
        
        if home_mode in API_TO_PRESET:
            return API_TO_PRESET[home_mode]
        
        return None
    
    @property
    def hvac_action(self) -> str | None:
        """Return current HVAC action."""
        heating_power = self._room.get("heating_power_request", 0)
        
        if self.hvac_mode == HVACMode.OFF:
            return "off"
        elif heating_power > 0:
            return "heating"
        else:
            return "idle"
    
    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        
        if temperature is None:
            return
        
        try:
            # Passer en mode manuel et définir la température
            await self.coordinator.async_set_room_temperature(
                self._room_id,
                temperature,
            )
            
            # Mettre à jour l'état local
            self._room["therm_setpoint_temperature"] = temperature
            self.async_write_ha_state()
            
        except Exception as err:
            _LOGGER.error("Error setting temperature: %s", err)
    
    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new HVAC mode."""
        if hvac_mode not in self._attr_hvac_modes:
            _LOGGER.error("Unsupported HVAC mode: %s", hvac_mode)
            return
        
        try:
            api_mode = HVAC_MODE_TO_API[hvac_mode]
            
            # Pour le mode OFF, on envoie vraiment "off" à l'API
            if hvac_mode == HVACMode.OFF:
                _LOGGER.info("Setting real OFF mode (not frost protection)")
                await self.coordinator.async_set_home_mode("off", endtime=None)
            elif hvac_mode == HVACMode.AUTO:
                # Mode AUTO = mode planning
                await self.coordinator.async_set_home_mode("schedule", endtime=None)
            elif hvac_mode == HVACMode.HEAT:
                # Mode HEAT = mode manuel, garder la température actuelle ou 19°C par défaut
                temperature = self.target_temperature or 19.0
                await self.coordinator.async_set_room_temperature(
                    self._room_id,
                    temperature,
                )
            
            # Mettre à jour les données
            await self.coordinator.async_update_data()
            self._update_room_data()
            self.async_write_ha_state()
            
        except Exception as err:
            _LOGGER.error("Error setting HVAC mode: %s", err)
    
    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        if preset_mode not in self._attr_preset_modes:
            _LOGGER.error("Unsupported preset mode: %s", preset_mode)
            return
        
        try:
            api_mode = PRESET_TO_API[preset_mode]
            
            # Définir l'endtime selon le preset
            endtime = None
            if api_mode == "away":
                # Mode absent : par défaut 3 heures
                endtime = int((datetime.now() + timedelta(hours=3)).timestamp())
            elif api_mode == "manual":
                # Mode manuel : garder la température et mettre 3 heures
                temperature = self.target_temperature or 19.0
                await self.coordinator.async_set_room_temperature(
                    self._room_id,
                    temperature,
                )
                # Pas besoin d'appeler async_set_home_mode après
                await self.coordinator.async_update_data()
                self._update_room_data()
                self.async_write_ha_state()
                return
            
            # Pour les autres modes
            await self.coordinator.async_set_home_mode(api_mode, endtime)
            
            # Mettre à jour les données
            await self.coordinator.async_update_data()
            self._update_room_data()
            self.async_write_ha_state()
            
        except Exception as err:
            _LOGGER.error("Error setting preset mode: %s", err)
    
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
