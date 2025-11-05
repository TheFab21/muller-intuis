"""Select platform for Muller Intuis Connect."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
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
    """Set up Muller Intuis select platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api_client = hass.data[DOMAIN][entry.entry_id]["api_client"]
    
    # Check if we have schedules
    status = coordinator.data.get("status", {})
    home = status.get("home", {})
    schedules = home.get("schedules", [])
    
    if schedules:
        entities = [MullerIntuisScheduleSelect(coordinator, api_client)]
        async_add_entities(entities)
        _LOGGER.info("Select platform setup completed with 1 entity (schedule selector)")
    else:
        _LOGGER.info("No schedules found, select platform setup completed with 0 entities")


class MullerIntuisScheduleSelect(CoordinatorEntity, SelectEntity):
    """Select entity for choosing the active schedule."""

    _attr_has_entity_name = True
    _attr_name = "Planning actif"

    def __init__(self, coordinator, api_client) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self.api_client = api_client
        self._home_id = coordinator.home_id
        self._attr_unique_id = f"{self._home_id}_active_schedule"

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._home_id)},
            "name": "Muller Intuis Connect",
            "manufacturer": "Muller Intuitiv",
            "model": "Système de chauffage",
        }

    @property
    def options(self) -> list[str]:
        """Return available schedule options."""
        status = self.coordinator.data.get("status", {})
        home = status.get("home", {})
        schedules = home.get("schedules", [])
        
        return [schedule.get("name", f"Planning {schedule.get('id')}") for schedule in schedules]

    @property
    def current_option(self) -> str | None:
        """Return the currently selected schedule."""
        status = self.coordinator.data.get("status", {})
        home = status.get("home", {})
        schedules = home.get("schedules", [])
        
        # Find selected schedule
        for schedule in schedules:
            if schedule.get("selected", False):
                return schedule.get("name", f"Planning {schedule.get('id')}")
        
        # If no schedule is selected, return first one
        if schedules:
            return schedules[0].get("name", f"Planning {schedules[0].get('id')}")
        
        return None

    async def async_select_option(self, option: str) -> None:
        """Change the selected schedule."""
        _LOGGER.info("Changing active schedule to: %s", option)
        
        # Find schedule ID by name
        status = self.coordinator.data.get("status", {})
        home = status.get("home", {})
        schedules = home.get("schedules", [])
        
        schedule_id = None
        for schedule in schedules:
            if schedule.get("name") == option:
                schedule_id = schedule.get("id")
                break
        
        if not schedule_id:
            _LOGGER.error("Schedule not found: %s", option)
            return
        
        try:
            await self.api_client.set_therm_mode(self._home_id, "schedule", schedule_id)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Error changing schedule: %s", err)
            raise
