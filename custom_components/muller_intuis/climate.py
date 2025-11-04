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

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Muller Intuis climate platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    
    # Pour l'instant, on ne crée pas d'entités
    # Cela sera implémenté dans une version future
    _LOGGER.info("Climate platform setup completed (no entities created yet)")
    
    # TODO: Créer les entités climate pour chaque radiateur/pièce
    # entities = []
    # for room in coordinator.data.get("rooms", []):
    #     entities.append(MullerIntuisClimate(coordinator, room))
    # async_add_entities(entities)


class MullerIntuisClimate(CoordinatorEntity, ClimateEntity):
    """Representation of a Muller Intuis climate device."""

    _attr_has_entity_name = True
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
    )
    _attr_hvac_modes = [HVACMode.AUTO, HVACMode.HEAT, HVACMode.OFF]

    def __init__(self, coordinator, room_data: dict[str, Any]) -> None:
        """Initialize the climate device."""
        super().__init__(coordinator)
        self._room_id = room_data["id"]
        self._attr_name = room_data["name"]
        self._attr_unique_id = f"{self._room_id}_climate"

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        # TODO: Implémenter la lecture de la température
        return None

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        # TODO: Implémenter la lecture de la consigne
        return None

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current operation mode."""
        # TODO: Implémenter la lecture du mode
        return HVACMode.AUTO

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        
        # TODO: Implémenter le changement de température
        _LOGGER.info("Setting temperature to %s for room %s", temperature, self._room_id)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        # TODO: Implémenter le changement de mode
        _LOGGER.info("Setting HVAC mode to %s for room %s", hvac_mode, self._room_id)
