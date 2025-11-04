"""Intégration Muller Intuis Connect pour Home Assistant."""
import logging
from datetime import timedelta

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    SERVICE_CREATE_SCHEDULE,
    SERVICE_DELETE_SCHEDULE,
    SERVICE_RENAME_SCHEDULE,
    SERVICE_SET_HOME_MODE,
    SERVICE_SET_ROOM_THERMPOINT,
    SERVICE_SET_SCHEDULE,
    SERVICE_SYNC_SCHEDULE,
)
from .api import MullerIntuisAPI

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.CLIMATE, Platform.SENSOR, Platform.SELECT]

SCAN_INTERVAL = timedelta(minutes=5)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Configuration via YAML non supportée."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configuration de l'intégration via config entry."""
    hass.data.setdefault(DOMAIN, {})

    client_id = entry.data[CONF_CLIENT_ID]
    client_secret = entry.data[CONF_CLIENT_SECRET]
    home_id = entry.data.get("home_id")

    session = async_get_clientsession(hass)
    api = MullerIntuisAPI(client_id, client_secret, session, hass, home_id)

    # Authentification initiale
    try:
        await api.async_get_access_token()
        home_data = await api.async_get_homestatus()
    except Exception as err:
        _LOGGER.error("Erreur lors de l'authentification : %s", err)
        return False

    # Créer le coordinateur de données
    coordinator = MullerIntuisDataUpdateCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "api": api,
    }

    # Configurer les plateformes
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Enregistrer les services
    await async_register_services(hass, api)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Décharger l'intégration."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class MullerIntuisDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinateur pour mettre à jour les données Muller Intuis."""

    def __init__(self, hass: HomeAssistant, api: MullerIntuisAPI) -> None:
        """Initialiser le coordinateur."""
        self.api = api
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        """Récupérer les données de l'API."""
        try:
            # Rafraîchir le token si nécessaire
            await self.api.async_refresh_token_if_needed()

            # Récupérer les données de la maison
            home_status = await self.api.async_get_homestatus()
            
            # Récupérer les plannings
            schedules = await self.api.async_get_schedules()

            return {
                "home_status": home_status,
                "schedules": schedules,
                "rooms": home_status.get("body", {}).get("home", {}).get("rooms", []),
            }
        except Exception as err:
            raise UpdateFailed(f"Erreur lors de la mise à jour des données: {err}")


async def async_register_services(hass: HomeAssistant, api: MullerIntuisAPI) -> None:
    """Enregistrer les services personnalisés."""

    async def handle_set_schedule(call: ServiceCall) -> None:
        """Gérer le service set_schedule."""
        schedule_id = call.data["schedule_id"]
        await api.async_switch_schedule(schedule_id)

    async def handle_sync_schedule(call: ServiceCall) -> None:
        """Gérer le service sync_schedule."""
        schedule_id = call.data["schedule_id"]
        timetable = call.data["timetable"]
        zones = call.data["zones"]
        name = call.data.get("name")
        await api.async_sync_schedule(schedule_id, timetable, zones, name)

    async def handle_create_schedule(call: ServiceCall) -> None:
        """Gérer le service create_schedule."""
        name = call.data["name"]
        timetable = call.data["timetable"]
        zones = call.data["zones"]
        await api.async_create_schedule(name, timetable, zones)

    async def handle_delete_schedule(call: ServiceCall) -> None:
        """Gérer le service delete_schedule."""
        schedule_id = call.data["schedule_id"]
        await api.async_delete_schedule(schedule_id)

    async def handle_rename_schedule(call: ServiceCall) -> None:
        """Gérer le service rename_schedule."""
        schedule_id = call.data["schedule_id"]
        name = call.data["name"]
        await api.async_rename_schedule(schedule_id, name)

    async def handle_set_room_thermpoint(call: ServiceCall) -> None:
        """Gérer le service set_room_thermpoint."""
        room_id = call.data["room_id"]
        mode = call.data["mode"]
        temp = call.data.get("temp")
        endtime = call.data.get("endtime")
        await api.async_set_thermpoint(room_id, mode, temp, endtime)

    async def handle_set_home_mode(call: ServiceCall) -> None:
        """Gérer le service set_home_mode."""
        mode = call.data["mode"]
        schedule_id = call.data.get("schedule_id")
        endtime = call.data.get("endtime")
        await api.async_set_therm_mode(mode, endtime, schedule_id)

    # Schémas de validation
    set_schedule_schema = vol.Schema({vol.Required("schedule_id"): cv.string})
    
    sync_schedule_schema = vol.Schema({
        vol.Required("schedule_id"): cv.string,
        vol.Required("timetable"): list,
        vol.Required("zones"): list,
        vol.Optional("name"): cv.string,
    })
    
    create_schedule_schema = vol.Schema({
        vol.Required("name"): cv.string,
        vol.Required("timetable"): list,
        vol.Required("zones"): list,
    })
    
    delete_schedule_schema = vol.Schema({vol.Required("schedule_id"): cv.string})
    
    rename_schedule_schema = vol.Schema({
        vol.Required("schedule_id"): cv.string,
        vol.Required("name"): cv.string,
    })
    
    set_room_thermpoint_schema = vol.Schema({
        vol.Required("room_id"): cv.string,
        vol.Required("mode"): cv.string,
        vol.Optional("temp"): vol.Coerce(float),
        vol.Optional("endtime"): vol.Coerce(int),
    })
    
    set_home_mode_schema = vol.Schema({
        vol.Required("mode"): cv.string,
        vol.Optional("schedule_id"): cv.string,
        vol.Optional("endtime"): vol.Coerce(int),
    })

    # Enregistrement des services
    hass.services.async_register(
        DOMAIN, SERVICE_SET_SCHEDULE, handle_set_schedule, schema=set_schedule_schema
    )
    
    hass.services.async_register(
        DOMAIN, SERVICE_SYNC_SCHEDULE, handle_sync_schedule, schema=sync_schedule_schema
    )
    
    hass.services.async_register(
        DOMAIN, SERVICE_CREATE_SCHEDULE, handle_create_schedule, schema=create_schedule_schema
    )
    
    hass.services.async_register(
        DOMAIN, SERVICE_DELETE_SCHEDULE, handle_delete_schedule, schema=delete_schedule_schema
    )
    
    hass.services.async_register(
        DOMAIN, SERVICE_RENAME_SCHEDULE, handle_rename_schedule, schema=rename_schedule_schema
    )
    
    hass.services.async_register(
        DOMAIN, SERVICE_SET_ROOM_THERMPOINT, handle_set_room_thermpoint, schema=set_room_thermpoint_schema
    )
    
    hass.services.async_register(
        DOMAIN, SERVICE_SET_HOME_MODE, handle_set_home_mode, schema=set_home_mode_schema
    )
