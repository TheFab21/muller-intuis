"""Select platform for Muller Intuis Connect."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
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
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator = entry_data["coordinator"]
    api_client = entry_data["api_client"]

    schedules = coordinator.data.get("schedules", {})
    if not schedules:
        _LOGGER.debug("No schedules available for Muller Intuis select entity")
        return

    entity = MullerIntuisScheduleSelect(coordinator, api_client)
    async_add_entities([entity])
    _LOGGER.info("Added Muller Intuis schedule select entity")


class MullerIntuisScheduleSelect(CoordinatorEntity, SelectEntity):
    """Representation of the Muller Intuis schedule selector."""

    def __init__(self, coordinator, api_client) -> None:
        """Initialise the select entity."""
        super().__init__(coordinator)
        self._api = api_client
        home_id = self._get_home_id()
        home_name = coordinator.data.get("home_name")
        self._attr_name = f"{home_name} Schedule" if home_name else "Muller Intuis Schedule"
        if home_id:
            self._attr_unique_id = f"{home_id}_schedule_select"
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, home_id)},
                name=home_name or "Muller Intuis Home",
                manufacturer="Muller",
            )
        else:
            self._attr_unique_id = "muller_intuis_schedule_select"

    @property
    def options(self) -> list[str]:
        """Return the available schedule names."""
        schedules = self._get_schedules()
        return [schedule.get("name", schedule_id) for schedule_id, schedule in schedules.items()]

    @property
    def current_option(self) -> str | None:
        """Return the currently selected schedule."""
        selected_id = self.coordinator.data.get("selected_schedule_id")
        if not selected_id:
            return None
        schedule = self._get_schedules().get(selected_id)
        if not schedule:
            return None
        return schedule.get("name", selected_id)

    async def async_select_option(self, option: str) -> None:
        """Select a different schedule."""
        schedules = self._get_schedules()
        target_id: str | None = None
        for schedule_id, schedule in schedules.items():
            if schedule.get("name", schedule_id) == option:
                target_id = schedule_id
                break

        if target_id is None:
            raise ValueError(f"Unknown schedule option: {option}")

        home_id = self._get_home_id()
        if not home_id:
            _LOGGER.error("Cannot change schedule without home ID")
            return

        _LOGGER.debug("Switching Muller Intuis schedule to %s (%s)", option, target_id)
        await self._api.set_therm_mode(home_id, "schedule", schedule_id=target_id)
        await self.coordinator.async_request_refresh()

    @property
    def available(self) -> bool:
        """Return entity availability."""
        return bool(self._get_schedules())

    def _get_home_id(self) -> str | None:
        """Return the home ID from the coordinator."""
        home_id = self.coordinator.data.get("home_id")
        if home_id:
            return str(home_id)
        return getattr(self.coordinator, "home_id", None)

    def _get_schedules(self) -> dict[str, dict[str, Any]]:
        """Return schedules from the coordinator."""
        schedules = self.coordinator.data.get("schedules")
        if isinstance(schedules, dict):
            return schedules
        return {}
