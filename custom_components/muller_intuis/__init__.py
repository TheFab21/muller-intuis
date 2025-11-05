"""The Muller Intuis Connect integration."""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import timedelta
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_PASSWORD,
    CONF_USERNAME,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    API_AUTH_URL,
    API_HOMESDATA_URL,
    API_HOMESTATUS_URL,
    API_SETSTATE_URL,
    API_SETTHERMMODE_URL,
    API_SWITCHHOMESCHEDULE_URL,
    DOMAIN,
    OAUTH_GRANT_TYPE,
    OAUTH_SCOPE,
    OAUTH_USER_PREFIX,
    SCAN_INTERVAL_SECONDS,
    TOKEN_REFRESH_MARGIN_SECONDS,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CLIMATE, Platform.SENSOR, Platform.SELECT]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Muller Intuis Connect from a config entry."""
    _LOGGER.info("Setting up Muller Intuis Connect integration")
    hass.data.setdefault(DOMAIN, {})

    try:
        api_client = MullerIntuisApiClient(
            hass,
            entry.data[CONF_CLIENT_ID],
            entry.data[CONF_CLIENT_SECRET],
            entry.data[CONF_USERNAME],
            entry.data[CONF_PASSWORD],
            entry.data.get("access_token"),
            entry.data.get("refresh_token_value"),
        )

        coordinator = MullerIntuisDataUpdateCoordinator(hass, api_client)
        await coordinator.async_config_entry_first_refresh()

        hass.data[DOMAIN][entry.entry_id] = {
            "coordinator": coordinator,
            "api_client": api_client,
        }

        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        _LOGGER.info("Muller Intuis Connect setup completed successfully")

        return True
    
    except Exception as err:
        _LOGGER.exception("Error setting up Muller Intuis Connect: %s", err)
        raise


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class MullerIntuisApiClient:
    """API client for Muller Intuitiv."""

    def __init__(
        self,
        hass: HomeAssistant,
        client_id: str,
        client_secret: str,
        username: str,
        password: str,
        access_token: str | None = None,
        refresh_token_value: str | None = None,
    ) -> None:
        """Initialize the API client."""
        self.hass = hass
        self.session = async_get_clientsession(hass)
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self._access_token = access_token
        self._refresh_token_value = refresh_token_value
        self._token_expires_at = 0

    async def _refresh_token(self) -> None:
        """Refresh the access token."""
        auth_data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": self.username,
            "password": self.password,
            "grant_type": OAUTH_GRANT_TYPE,
            "user_prefix": OAUTH_USER_PREFIX,
            "scope": OAUTH_SCOPE,
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with self.session.post(
                API_AUTH_URL,
                data=auth_data,
                headers=headers,
                timeout=timeout,
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    _LOGGER.error("Token refresh failed: %s - %s", response.status, error_text)
                    raise ConfigEntryAuthFailed("Token refresh failed")

                data = await response.json()

                if "access_token" not in data:
                    raise ConfigEntryAuthFailed("No access_token in response")

                self._access_token = data["access_token"]
                self._refresh_token_value = data.get("refresh_token", self._refresh_token_value)
                
                expires_in = data.get("expires_in", 10800)
                self._token_expires_at = time.time() + expires_in

                _LOGGER.info("Token refreshed successfully")

        except aiohttp.ClientError as err:
            _LOGGER.error("Connection error during token refresh: %s", err)
            raise UpdateFailed(f"Connection error: {err}") from err

    async def _ensure_token_valid(self) -> None:
        """Ensure the access token is valid."""
        if (
            not self._access_token
            or time.time() >= (self._token_expires_at - TOKEN_REFRESH_MARGIN_SECONDS)
        ):
            await self._refresh_token()

    async def _api_request(
        self, url: str, method: str = "POST", data: dict | None = None
    ) -> dict[str, Any]:
        """Make an API request."""
        await self._ensure_token_valid()

        headers = {
            "Authorization": f"Bearer {self._access_token}",
        }
        
        if method == "POST_JSON":
            headers["Content-Type"] = "application/json"
            method = "POST"
            request_data = data
        else:
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            request_data = data

        try:
            timeout = aiohttp.ClientTimeout(total=30)
            if method == "GET":
                async with self.session.get(url, headers=headers, params=data, timeout=timeout) as response:
                    return await self._handle_response(response)
            else:
                if headers["Content-Type"] == "application/json":
                    async with self.session.post(url, headers=headers, json=request_data, timeout=timeout) as response:
                        return await self._handle_response(response)
                else:
                    async with self.session.post(url, headers=headers, data=request_data, timeout=timeout) as response:
                        return await self._handle_response(response)

        except aiohttp.ClientError as err:
            _LOGGER.error("API request error: %s", err)
            raise UpdateFailed(f"API request failed: {err}") from err

    async def _handle_response(self, response: aiohttp.ClientResponse) -> dict[str, Any]:
        """Handle API response."""
        if response.status == 401:
            self._access_token = None
            raise ConfigEntryAuthFailed("Authentication failed")

        if response.status != 200:
            error_text = await response.text()
            _LOGGER.error("API error: %s - %s", response.status, error_text)
            raise UpdateFailed(f"API error: {response.status}")

        data = await response.json()
        
        if data.get("status") != "ok":
            error = data.get("error", {})
            error_msg = error.get("message", "Unknown error")
            _LOGGER.error("API returned error: %s", error_msg)
            raise UpdateFailed(f"API error: {error_msg}")

        return data

    async def get_homes_data(self) -> dict[str, Any]:
        """Get homes data (static info: rooms, modules, schedules)."""
        return await self._api_request(API_HOMESDATA_URL, method="GET")

    async def get_home_status(self, home_id: str) -> dict[str, Any]:
        """Get home status (real-time: temperatures, states)."""
        return await self._api_request(
            API_HOMESTATUS_URL,
            method="GET",
            data={"home_id": home_id},
        )

    async def set_room_state(
        self, home_id: str, room_id: str, mode: str, temp: float | None = None, duration: int | None = None
    ) -> dict[str, Any]:
        """Set room state (temperature setpoint and mode)."""
        _LOGGER.debug("Setting room state: home=%s, room=%s, mode=%s, temp=%s, duration=%s", 
                     home_id, room_id, mode, temp, duration)
        
        room_data = {
            "id": room_id,
            "therm_setpoint_mode": mode,
        }
        
        if temp is not None:
            room_data["therm_setpoint_temperature"] = temp
            
        if duration is not None:
            if duration == 0:
                # Indefinite: set to 0 or past timestamp
                room_data["therm_setpoint_end_time"] = 0
            else:
                # Specific duration: current timestamp + duration in seconds
                end_time = int(time.time()) + (duration * 60)
                room_data["therm_setpoint_end_time"] = end_time
        
        payload = {
            "home": {
                "id": home_id,
                "rooms": [room_data]
            }
        }

        return await self._api_request(API_SETSTATE_URL, data=payload, method="POST_JSON")

    async def set_therm_mode(
        self, home_id: str, mode: str, end_time: int | None = None
    ) -> dict[str, Any]:
        """Set home thermostat mode."""
        _LOGGER.debug("Setting home therm mode: home=%s, mode=%s, endtime=%s", home_id, mode, end_time)
        
        data = {
            "home_id": home_id,
            "mode": mode,
        }
        
        if end_time is not None:
            data["endtime"] = end_time

        return await self._api_request(API_SETTHERMMODE_URL, data=data)

    async def switch_home_schedule(
        self, home_id: str, schedule_id: str
    ) -> dict[str, Any]:
        """Switch the active home schedule."""
        _LOGGER.debug("Switching home schedule: home=%s, schedule=%s", home_id, schedule_id)
        
        payload = {
            "app_identifier": "app_muller",
            "home_id": home_id,
            "schedule_id": schedule_id,
            "schedule_type": "therm"
        }

        return await self._api_request(API_SWITCHHOMESCHEDULE_URL, data=payload, method="POST_JSON")


class MullerIntuisDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Muller Intuis data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_client: MullerIntuisApiClient,
    ) -> None:
        """Initialize."""
        self.api_client = api_client
        self.home_id: str | None = None
        self.home_name: str | None = None
        self.homes_data: dict[str, Any] = {}

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            # Get homes data on first run
            if not self.home_id:
                homes_response = await self.api_client.get_homes_data()
                homes = homes_response.get("body", {}).get("homes", [])
                
                if not homes:
                    raise UpdateFailed("No homes found in account")
                
                self.home_id = homes[0]["id"]
                self.home_name = homes[0].get("name", "Domicile")
                self.homes_data = homes[0]
                _LOGGER.info("Using home: %s (ID: %s)", self.home_name, self.home_id)

            # Get home status (real-time data)
            status_data = await self.api_client.get_home_status(self.home_id)
            status = status_data.get("body", {}).get("home", {})
            
            # Add static data
            status["rooms_info"] = self.homes_data.get("rooms", [])
            status["schedules"] = self.homes_data.get("schedules", [])
            status["home_name"] = self.home_name
            
            return {
                "home_id": self.home_id,
                "home_name": self.home_name,
                "status": status,
                "homes_data": self.homes_data,
            }

        except ConfigEntryAuthFailed as err:
            raise err
        except Exception as err:
            _LOGGER.exception("Error communicating with API: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err
