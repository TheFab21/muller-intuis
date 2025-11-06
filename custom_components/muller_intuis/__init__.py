"""The Muller Intuis Connect integration."""
from __future__ import annotations

import logging
import asyncio
from datetime import datetime, timedelta
import aiohttp
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    API_BASE_URL,
    OAUTH_TOKEN_URL,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CLIMATE, Platform.SENSOR, Platform.SELECT]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Muller Intuis Connect from a config entry."""
    
    client_id = entry.data[CONF_CLIENT_ID]
    client_secret = entry.data[CONF_CLIENT_SECRET]
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    
    # Créer le coordinateur
    coordinator = MullerIntuisCoordinator(
        hass, client_id, client_secret, username, password
    )
    
    # Récupérer le token et les données
    try:
        await coordinator.async_get_token()
        await coordinator.async_update_data()
    except ConfigEntryAuthFailed:
        return False
    except Exception as err:
        _LOGGER.error("Error setting up Muller Intuis: %s", err)
        raise ConfigEntryNotReady from err
    
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok


class MullerIntuisCoordinator:
    """Coordinator pour gérer les appels API Muller Intuis."""
    
    def __init__(
        self,
        hass: HomeAssistant,
        client_id: str,
        client_secret: str,
        username: str,
        password: str,
    ) -> None:
        """Initialize the coordinator."""
        self.hass = hass
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self.access_token: str | None = None
        self.refresh_token: str | None = None
        self.token_expires_at: datetime | None = None
        self.home_id: str | None = None
        self.data: dict[str, Any] = {}
        self.schedules: list[dict] = []
        self.active_schedule_id: str | None = None
        
    async def async_get_token(self) -> None:
        """Get OAuth token from Muller API."""
        session = async_get_clientsession(self.hass)
        
        data = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": self.username,
            "password": self.password,
            "scope": "read_muller write_muller",
            "user_prefix": "muller",
        }
        
        try:
            async with session.post(OAUTH_TOKEN_URL, data=data) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self.access_token = token_data["access_token"]
                    self.refresh_token = token_data.get("refresh_token")
                    expires_in = token_data.get("expires_in", 3600)
                    self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                    _LOGGER.debug("Token obtained successfully")
                else:
                    error_text = await response.text()
                    _LOGGER.error("Failed to get token: %s - %s", response.status, error_text)
                    raise ConfigEntryAuthFailed(f"Authentication failed: {response.status}")
        except aiohttp.ClientError as err:
            _LOGGER.error("Connection error during authentication: %s", err)
            raise ConfigEntryNotReady from err
    
    async def async_ensure_token_valid(self) -> None:
        """Ensure the token is still valid, refresh if needed."""
        if not self.token_expires_at or datetime.now() >= self.token_expires_at - timedelta(minutes=5):
            _LOGGER.debug("Token expired or about to expire, refreshing...")
            await self.async_get_token()
    
    async def async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        await self.async_ensure_token_valid()
        
        session = async_get_clientsession(self.hass)
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        
        try:
            # Get home data
            async with session.post(
                f"{API_BASE_URL}/homesdata",
                headers=headers,
                json={"app_identifier": "app_muller"}
            ) as response:
                if response.status == 200:
                    homes_data = await response.json()
                    if homes_data.get("body", {}).get("homes"):
                        home = homes_data["body"]["homes"][0]
                        self.home_id = home["id"]
                        self.schedules = home.get("schedules", [])
                        
                        # Trouver le planning actif
                        for schedule in self.schedules:
                            if schedule.get("selected"):
                                self.active_schedule_id = schedule["id"]
                                break
                    else:
                        _LOGGER.error("No homes found")
                        raise ConfigEntryNotReady("No homes found")
                else:
                    error_text = await response.text()
                    _LOGGER.error("Failed to get homes data: %s - %s", response.status, error_text)
                    raise ConfigEntryNotReady(f"Failed to get homes data: {response.status}")
            
            # Get home status
            async with session.post(
                f"{API_BASE_URL}/homestatus",
                headers=headers,
                json={
                    "app_identifier": "app_muller",
                    "home_id": self.home_id
                }
            ) as response:
                if response.status == 200:
                    status_data = await response.json()
                    self.data = status_data.get("body", {}).get("home", {})
                    _LOGGER.debug("Data updated successfully")
                    return self.data
                else:
                    error_text = await response.text()
                    _LOGGER.error("Failed to get home status: %s - %s", response.status, error_text)
                    raise ConfigEntryNotReady(f"Failed to get home status: {response.status}")
                    
        except aiohttp.ClientError as err:
            _LOGGER.error("Connection error during data update: %s", err)
            raise ConfigEntryNotReady from err
    
    async def async_set_home_mode(
        self,
        mode: str,
        endtime: int | None = None,
    ) -> None:
        """
        Set the home thermostat mode.
        
        Args:
            mode: Le mode à définir (schedule, away, hg, off)
            endtime: Timestamp Unix en secondes pour la fin du mode (optionnel)
        """
        await self.async_ensure_token_valid()
        
        session = async_get_clientsession(self.hass)
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        
        # Validation et correction de l'endtime
        validated_endtime = self._validate_endtime(endtime, mode)
        
        payload = {
            "app_identifier": "app_muller",
            "home_id": self.home_id,
            "mode": mode,
        }
        
        # N'ajouter endtime que s'il est valide
        if validated_endtime is not None:
            payload["endtime"] = validated_endtime
        
        _LOGGER.debug("Setting home mode: %s with payload: %s", mode, payload)
        
        try:
            async with session.post(
                f"{API_BASE_URL}/setthermmode",
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    _LOGGER.info("Home mode set successfully to %s", mode)
                    await self.async_update_data()
                else:
                    error_text = await response.text()
                    _LOGGER.error("API error: %s - %s", response.status, error_text)
                    raise Exception(f"API error: {response.status} - {error_text}")
        except aiohttp.ClientError as err:
            _LOGGER.error("Connection error: %s", err)
            raise
    
    def _validate_endtime(self, endtime: int | None, mode: str) -> int | None:
        """
        Valide et corrige l'endtime selon les règles de l'API.
        
        Args:
            endtime: Timestamp Unix en secondes
            mode: Le mode demandé
            
        Returns:
            Timestamp Unix valide ou None
        """
        if endtime is None:
            # Pour les modes hg, schedule et off, pas besoin d'endtime
            if mode in ["hg", "schedule", "off"]:
                return None
            # Pour away et manual, mettre une durée par défaut
            elif mode in ["away", "manual"]:
                return int((datetime.now() + timedelta(hours=3)).timestamp())
            return None
        
        now = int(datetime.now().timestamp())
        min_time = now + 5 * 60  # Au moins 5 minutes dans le futur
        max_time = now + 365 * 24 * 60 * 60  # Maximum 1 an
        
        # Vérifier si endtime est dans la plage valide
        if endtime < min_time:
            _LOGGER.warning(
                "endtime %s is in the past or too soon (min: %s). Using default 3 hours.",
                endtime, min_time
            )
            return int((datetime.now() + timedelta(hours=3)).timestamp())
        elif endtime > max_time:
            _LOGGER.warning(
                "endtime %s is too far in the future (max: %s). Using default 3 hours.",
                endtime, max_time
            )
            return int((datetime.now() + timedelta(hours=3)).timestamp())
        
        return endtime
    
    async def async_set_room_temperature(
        self,
        room_id: str,
        temperature: float,
        endtime: int | None = None,
    ) -> None:
        """Set room target temperature in manual mode."""
        await self.async_ensure_token_valid()
        
        session = async_get_clientsession(self.hass)
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        
        # Si pas d'endtime, mettre 3 heures par défaut pour le mode manuel
        if endtime is None:
            endtime = int((datetime.now() + timedelta(hours=3)).timestamp())
        else:
            endtime = self._validate_endtime(endtime, "manual")
        
        payload = {
            "app_identifier": "app_muller",
            "home_id": self.home_id,
            "room_id": room_id,
            "mode": "manual",
            "temp": temperature,
        }
        
        if endtime is not None:
            payload["endtime"] = endtime
        
        _LOGGER.debug("Setting room temperature: %s°C for room %s", temperature, room_id)
        
        try:
            async with session.post(
                f"{API_BASE_URL}/setroomthermpoint",
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    _LOGGER.info("Room temperature set successfully")
                    await self.async_update_data()
                else:
                    error_text = await response.text()
                    _LOGGER.error("API error: %s - %s", response.status, error_text)
                    raise Exception(f"API error: {response.status} - {error_text}")
        except aiohttp.ClientError as err:
            _LOGGER.error("Connection error: %s", err)
            raise
    
    async def async_switch_schedule(self, schedule_id: str) -> None:
        """Switch active schedule."""
        await self.async_ensure_token_valid()
        
        session = async_get_clientsession(self.hass)
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "app_identifier": "app_muller",
            "home_id": self.home_id,
            "schedule_id": schedule_id,
        }
        
        _LOGGER.debug("Switching to schedule: %s", schedule_id)
        
        try:
            async with session.post(
                f"{API_BASE_URL}/switchhomeschedule",
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    _LOGGER.info("Schedule switched successfully")
                    self.active_schedule_id = schedule_id
                    await self.async_update_data()
                else:
                    error_text = await response.text()
                    _LOGGER.error("API error: %s - %s", response.status, error_text)
                    raise Exception(f"API error: {response.status} - {error_text}")
        except aiohttp.ClientError as err:
            _LOGGER.error("Connection error: %s", err)
            raise
