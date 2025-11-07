"""Client API pour Muller Intuis Connect (basé sur Netatmo)."""
import logging
import time
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers import storage

from .const import (
    API_BASE_URL,
    AUTH_URL,
    CREATE_NEW_SCHEDULE_URL,
    DEFAULT_MANUAL_DURATION,
    DELETE_SCHEDULE_URL,
    GET_MEASURE_URL,
    GET_ROOM_MEASURE_URL,
    HOME_STATUS_URL,
    RENAME_SCHEDULE_URL,
    SET_THERM_MODE_URL,
    SET_THERMPOINT_URL,
    SWITCH_SCHEDULE_URL,
    SYNC_SCHEDULE_URL,
)

_LOGGER = logging.getLogger(__name__)


class MullerIntuisAPI:
    """Classe pour communiquer avec l'API Muller Intuis."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        session: aiohttp.ClientSession,
        hass: HomeAssistant,
        home_id: str = None,
    ):
        """Initialiser l'API."""
        self.client_id = client_id
        self.client_secret = client_secret
        self.session = session
        self.hass = hass
        self.home_id = home_id
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = 0
        self.store = storage.Store(hass, version=1, key="muller_intuis_tokens")

    async def async_load_tokens(self):
        """Charger les tokens depuis le stockage."""
        data = await self.store.async_load()
        if data:
            self.access_token = data.get("access_token")
            self.refresh_token = data.get("refresh_token")
            self.token_expires_at = data.get("expires_at", 0)

    async def async_save_tokens(self):
        """Sauvegarder les tokens."""
        await self.store.async_save(
            {
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "expires_at": self.token_expires_at,
            }
        )

    async def async_get_access_token(self):
        """Obtenir un access token."""
        # Essayer de charger les tokens existants
        await self.async_load_tokens()

        # Si on a déjà un token valide, le retourner
        if self.access_token and time.time() < self.token_expires_at - 300:
            return self.access_token

        # Sinon, rafraîchir ou obtenir un nouveau token
        if self.refresh_token:
            return await self.async_refresh_token()

        # Premier appel : pas de refresh_token
        _LOGGER.error(
            "Pas de refresh_token disponible. Utilisez le flow de configuration."
        )
        return None

    async def async_refresh_token(self):
        """Rafraîchir l'access token."""
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        async with self.session.post(AUTH_URL, data=data) as response:
            if response.status == 200:
                result = await response.json()
                self.access_token = result["access_token"]
                self.refresh_token = result.get("refresh_token", self.refresh_token)
                expires_in = result.get("expires_in", 10800)
                self.token_expires_at = time.time() + expires_in
                await self.async_save_tokens()
                return self.access_token
            else:
                error_text = await response.text()
                _LOGGER.error("Erreur de rafraîchissement du token: %s", error_text)
                return None

    async def async_refresh_token_if_needed(self):
        """Rafraîchir le token si nécessaire."""
        if time.time() >= self.token_expires_at - 300:
            await self.async_refresh_token()

    async def async_request(
        self, method: str, url: str, params: dict = None, data: dict = None
    ) -> dict:
        """Faire une requête à l'API."""
        await self.async_refresh_token_if_needed()

        headers = {"Authorization": f"Bearer {self.access_token}"}

        async with self.session.request(
            method, url, headers=headers, params=params, json=data
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                _LOGGER.error(
                    "Erreur API %s %s: %s", method, url, error_text
                )
                return None

    async def async_get_homestatus(self) -> dict:
        """Récupérer le statut de la maison."""
        params = {"home_id": self.home_id} if self.home_id else {}
        return await self.async_request("POST", HOME_STATUS_URL, data=params)

    async def async_set_thermpoint(
    self, room_id: str, mode: str, temp: float = None, endtime: int = None
):
    """Définir le point de consigne d'une pièce."""
    
    # Validation endtime : minimum 5 min dans le futur
    if endtime is not None:
        now = int(time.time())
        min_time = now + 300  # 5 minutes
        
        if endtime < min_time:
            _LOGGER.warning(
                "endtime %s is in the past or too soon, adjusting to +3h",
                endtime
            )
            endtime = now + (DEFAULT_MANUAL_DURATION * 60)
    
    data = {
        "home_id": self.home_id,
        "room_id": room_id,
        "mode": mode,
    }
    if temp is not None:
        data["temp"] = temp
    if endtime is not None:
        data["endtime"] = endtime

    return await self.async_request("POST", SET_THERMPOINT_URL, data=data)

    async def async_set_therm_mode(
    self, mode: str, endtime: int = None, schedule_id: str = None
):
    """Définir le mode de chauffage de la maison."""
    
    # Validation endtime : minimum 5 min dans le futur  
    if endtime is not None:
        now = int(time.time())
        min_time = now + 300  # 5 minutes
        
        if endtime < min_time:
            _LOGGER.warning(
                "endtime %s is in the past or too soon, adjusting to +3h",
                endtime
            )
            endtime = now + (DEFAULT_MANUAL_DURATION * 60)
    
    data = {
        "home_id": self.home_id,
        "mode": mode,
    }
    if endtime is not None:
        data["endtime"] = endtime
    if schedule_id is not None:
        data["schedule_id"] = schedule_id

    return await self.async_request("POST", SET_THERM_MODE_URL, data=data)

    async def async_switch_schedule(self, schedule_id: str):
        """Changer le planning actif."""
        data = {"home_id": self.home_id, "schedule_id": schedule_id}
        return await self.async_request("POST", SWITCH_SCHEDULE_URL, data=data)

    async def async_sync_schedule(
        self, schedule_id: str, timetable: list, zones: list, name: str = None
    ):
        """Synchroniser/mettre à jour un planning."""
        data = {
            "home_id": self.home_id,
            "schedule_id": schedule_id,
            "timetable": timetable,
            "zones": zones,
        }
        if name:
            data["name"] = name

        return await self.async_request("POST", SYNC_SCHEDULE_URL, data=data)

    async def async_create_schedule(self, name: str, timetable: list, zones: list):
        """Créer un nouveau planning."""
        data = {
            "home_id": self.home_id,
            "name": name,
            "timetable": timetable,
            "zones": zones,
        }
        return await self.async_request("POST", CREATE_NEW_SCHEDULE_URL, data=data)

    async def async_delete_schedule(self, schedule_id: str):
        """Supprimer un planning."""
        data = {"home_id": self.home_id, "schedule_id": schedule_id}
        return await self.async_request("POST", DELETE_SCHEDULE_URL, data=data)

    async def async_rename_schedule(self, schedule_id: str, name: str):
        """Renommer un planning."""
        data = {"home_id": self.home_id, "schedule_id": schedule_id, "name": name}
        return await self.async_request("POST", RENAME_SCHEDULE_URL, data=data)

    async def async_get_room_measure(
        self,
        room_id: str,
        scale: str,
        type_measure: str,
        date_begin: int = None,
        date_end: int = None,
    ):
        """Récupérer les mesures d'une pièce."""
        data = {
            "home_id": self.home_id,
            "room_id": room_id,
            "scale": scale,
            "type": type_measure,
        }
        if date_begin:
            data["date_begin"] = date_begin
        if date_end:
            data["date_end"] = date_end

        return await self.async_request("POST", GET_ROOM_MEASURE_URL, data=data)

    async def async_get_schedules(self) -> dict:
        """Récupérer tous les plannings depuis le homestatus."""
        home_status = await self.async_get_homestatus()
        if not home_status:
            return {}

        schedules = {}
        home_data = home_status.get("body", {}).get("home", {})
        schedule_list = home_data.get("schedules", [])

        for schedule in schedule_list:
            schedule_id = schedule.get("id")
            if schedule_id:
                schedules[schedule_id] = schedule

        return schedules
