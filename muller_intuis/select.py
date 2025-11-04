"""Entités select pour Muller Intuis."""
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configurer les entités select."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]

    # Créer le sélecteur de planning
    async_add_entities([MullerIntuisScheduleSelect(coordinator, api)])


class MullerIntuisScheduleSelect(CoordinatorEntity, SelectEntity):
    """Sélecteur de planning."""

    _attr_has_entity_name = True
    _attr_name = "Active Schedule"

    def __init__(self, coordinator, api):
        """Initialiser le sélecteur."""
        super().__init__(coordinator)
        self.api = api
        self._attr_unique_id = f"{DOMAIN}_schedule_selector"

    @property
    def device_info(self):
        """Informations sur le device."""
        return {
            "identifiers": {(DOMAIN, "home")},
            "name": "Muller Intuis Home",
            "manufacturer": "Muller Intuis",
            "model": "Home Controller",
        }

    @property
    def options(self):
        """Liste des options disponibles."""
        schedules = self.coordinator.data.get("schedules", {})
        return [schedule.get("name", schedule_id) for schedule_id, schedule in schedules.items()]

    @property
    def current_option(self):
        """Option actuellement sélectionnée."""
        schedules = self.coordinator.data.get("schedules", {})
        for schedule_id, schedule in schedules.items():
            if schedule.get("selected"):
                return schedule.get("name", schedule_id)
        return None

    async def async_select_option(self, option: str) -> None:
        """Changer le planning actif."""
        schedules = self.coordinator.data.get("schedules", {})
        
        # Trouver l'ID du planning correspondant au nom
        schedule_id = None
        for sid, schedule in schedules.items():
            if schedule.get("name") == option:
                schedule_id = sid
                break

        if schedule_id:
            await self.api.async_switch_schedule(schedule_id)
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Planning '%s' introuvable", option)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Gérer les mises à jour du coordinateur."""
        self.async_write_ha_state()
