"""Select platform for Muller Intuis Connect."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Muller Intuis select entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Attendre que les données soient chargées
    await coordinator.async_update_data()
    
    # Créer l'entité de sélection des plannings
    async_add_entities([MullerIntuisScheduleSelect(coordinator)], True)


class MullerIntuisScheduleSelect(SelectEntity):
    """Select entity for active schedule."""
    
    _attr_icon = "mdi:calendar-clock"
    
    def __init__(self, coordinator) -> None:
        """Initialize the select entity."""
        self.coordinator = coordinator
        self._attr_name = "Muller Intuis Active Schedule"
        self._attr_unique_id = f"muller_{coordinator.home_id}_active_schedule"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.home_id)},
            "name": "Muller Intuis Home",
            "manufacturer": "Muller Intuitiv",
            "model": "Intuis Connect Home",
        }
    
    @property
    def options(self) -> list[str]:
        """Return list of available schedules."""
        return [schedule["name"] for schedule in self.coordinator.schedules]
    
    @property
    def current_option(self) -> str | None:
        """Return currently selected schedule."""
        for schedule in self.coordinator.schedules:
            if schedule.get("selected"):
                return schedule["name"]
        return None
    
    async def async_select_option(self, option: str) -> None:
        """Change the selected schedule."""
        # Trouver l'ID du planning correspondant au nom
        schedule_id = None
        for schedule in self.coordinator.schedules:
            if schedule["name"] == option:
                schedule_id = schedule["id"]
                break
        
        if schedule_id is None:
            _LOGGER.error("Schedule not found: %s", option)
            return
        
        try:
            await self.coordinator.async_switch_schedule(schedule_id)
            self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Error selecting schedule: %s", err)
    
    async def async_update(self) -> None:
        """Update the entity."""
        await self.coordinator.async_update_data()
