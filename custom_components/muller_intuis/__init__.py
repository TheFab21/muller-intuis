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
    API_HOMES_URL,
    API_HOMESTATUS_URL,
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
        # Créer le client API
        _LOGGER.debug("Creating API client with credentials")
        api_client = MullerIntuisApiClient(
            hass,
            entry.data[CONF_CLIENT_ID],
            entry.data[CONF_CLIENT_SECRET],
            entry.data[CONF_USERNAME],
            entry.data[CONF_PASSWORD],
            entry.data.get("access_token"),
            entry.data.get("refresh_token"),
        )

        # Créer le coordinator
        _LOGGER.debug("Creating data update coordinator")
        coordinator = MullerIntuisDataUpdateCoordinator(hass, api_client)

        # Fetch initial data
        _LOGGER.debug("Fetching initial data")
        await coordinator.async_config_entry_first_refresh()
        _LOGGER.info("Initial data fetch successful")

        hass.data[DOMAIN][entry.entry_id] = {
            "coordinator": coordinator,
            "api_client": api_client,
        }

        # Setup platforms
        _LOGGER.debug("Setting up platforms")
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        _LOGGER.info("Muller Intuis Connect setup completed successfully")

        return True
    
    except Exception as err:
        _LOGGER.exception("Error setting up Muller Intuis Connect: %s", err)
        _LOGGER.error("Exception type: %s", type(err).__name__)
        _LOGGER.error("Exception args: %s", err.args)
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
        refresh_token: str | None = None,
    ) -> None:
        """Initialize the API client."""
        self.hass = hass
        self.session = async_get_clientsession(hass)
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self._access_token = access_token
        self._refresh_token_value = refresh_token  # Renamed to avoid conflict with method
        self._token_expires_at = 0

    async def _refresh_token(self) -> None:
        """Refresh the access token."""
        _LOGGER.debug("Starting token refresh")
        auth_data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": self.username,
            "password": self.password,
            "grant_type": OAUTH_GRANT_TYPE,
            "user_prefix": OAUTH_USER_PREFIX,
            "scope": OAUTH_SCOPE,
        }
        
        _LOGGER.debug("Auth data prepared (credentials hidden)")

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        try:
            _LOGGER.debug("Sending POST request to %s", API_AUTH_URL)
            timeout = aiohttp.ClientTimeout(total=30)
            async with self.session.post(
                API_AUTH_URL,
                data=auth_data,
                headers=headers,
                timeout=timeout,
            ) as response:
                _LOGGER.debug("Received response with status: %s", response.status)
                if response.status != 200:
                    error_text = await response.text()
                    _LOGGER.error(
                        "Token refresh failed: %s - %s", response.status, error_text
                    )
                    raise ConfigEntryAuthFailed("Token refresh failed")

                data = await response.json()
                _LOGGER.debug("Response parsed as JSON")

                if "access_token" not in data:
                    _LOGGER.error("No access_token in response")
                    raise ConfigEntryAuthFailed("No access_token in response")

                self._access_token = data["access_token"]
                self._refresh_token_value = data.get("refresh_token", self._refresh_token_value)
                
                # Calculate expiration time
                expires_in = data.get("expires_in", 10800)
                self._token_expires_at = time.time() + expires_in

                _LOGGER.info("Token refreshed successfully, expires in %s seconds", expires_in)

        except aiohttp.ClientError as err:
            _LOGGER.error("Connection error during token refresh: %s", err)
            _LOGGER.error("Error type: %s", type(err).__name__)
            raise UpdateFailed(f"Connection error: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error during token refresh: %s", err)
            _LOGGER.error("Error type: %s", type(err).__name__)
            _LOGGER.error("Error args: %s", err.args)
            raise

    async def _ensure_token_valid(self) -> None:
        """Ensure the access token is valid."""
        
        # Refresh if token is not set or about to expire
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
            "Content-Type": "application/x-www-form-urlencoded",
        }

        try:
            timeout = aiohttp.ClientTimeout(total=30)
            if method == "GET":
                async with self.session.get(url, headers=headers, params=data, timeout=timeout) as response:
                    return await self._handle_response(response)
            else:
                async with self.session.post(url, headers=headers, data=data, timeout=timeout) as response:
                    return await self._handle_response(response)

        except aiohttp.ClientError as err:
            _LOGGER.error("API request error: %s", err)
            raise UpdateFailed(f"API request failed: {err}") from err

    async def _handle_response(self, response: aiohttp.ClientResponse) -> dict[str, Any]:
        """Handle API response."""
        if response.status == 401:
            # Token expired, refresh and retry will happen on next call
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
        """Get homes data."""
        return await self._api_request(API_HOMES_URL, method="GET")

    async def get_home_status(self, home_id: str) -> dict[str, Any]:
        """Get home status."""
        return await self._api_request(
            API_HOMESTATUS_URL,
            method="GET",
            data={"home_id": home_id},
        )

    async def set_room_thermpoint(
        self, home_id: str, room_id: str, mode: str, temp: float | None = None
    ) -> dict[str, Any]:
        """Set room temperature setpoint."""
        from .const import API_SETROOMTHERMPOINT_URL
        
        data = {
            "home_id": home_id,
            "room_id": room_id,
            "mode": mode,
        }
        
        if temp is not None:
            data["temp"] = temp

        return await self._api_request(API_SETROOMTHERMPOINT_URL, data=data)

    async def set_therm_mode(
        self, home_id: str, mode: str, schedule_id: str | None = None
    ) -> dict[str, Any]:
        """Set home thermostat mode."""
        from .const import API_SETTHERMMODE_URL
        
        data = {
            "home_id": home_id,
            "mode": mode,
        }
        
        if schedule_id:
            data["schedule_id"] = schedule_id

        return await self._api_request(API_SETTHERMMODE_URL, data=data)


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

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        _LOGGER.debug("Starting data update")
        try:
            # Get homes data on first run to get home_id
            if not self.home_id:
                _LOGGER.debug("No home_id set, fetching homes data")
                homes_data = await self.api_client.get_homes_data()
                _LOGGER.debug("Homes data received")
                homes = homes_data.get("body", {}).get("homes", [])
                
                if not homes:
                    _LOGGER.error("No homes found in account")
                    raise UpdateFailed("No homes found in account")
                
                # Use first home
                self.home_id = homes[0]["id"]
                _LOGGER.info("Using home_id: %s", self.home_id)

            # Get home status
            _LOGGER.debug("Fetching home status for home_id: %s", self.home_id)
            status_data = await self.api_client.get_home_status(self.home_id)
            _LOGGER.debug("Home status received")

            status_body = status_data.get("body", {})
            home_data = status_body.get("home", {})

            if not self.home_id:
                self.home_id = home_data.get("id")
                _LOGGER.info("Home ID updated from status: %s", self.home_id)

            rooms: list[dict[str, Any]] = home_data.get("rooms", []) or []
            schedules_list: list[dict[str, Any]] = home_data.get("schedules", []) or []

            schedules: dict[str, dict[str, Any]] = {}
            selected_schedule_id: str | None = None
            for schedule in schedules_list:
                schedule_id = schedule.get("id")
                if not schedule_id:
                    continue
                schedules[schedule_id] = schedule
                if schedule.get("selected"):
                    selected_schedule_id = schedule_id

            rooms_by_id: dict[str, dict[str, Any]] = {}
            for room in rooms:
                room_id = room.get("id")
                if room_id:
                    rooms_by_id[room_id] = room

            return {
                "home_id": self.home_id,
                "home_name": home_data.get("name"),
                "status": status_body,
                "rooms": rooms,
                "rooms_by_id": rooms_by_id,
                "schedules": schedules,
                "selected_schedule_id": selected_schedule_id,
            }

        except ConfigEntryAuthFailed as err:
            _LOGGER.error("Authentication error: %s", err)
            # Re-raise auth errors
            raise err
        except Exception as err:
            _LOGGER.exception("Error communicating with API: %s", err)
            _LOGGER.error("Exception type: %s", type(err).__name__)
            _LOGGER.error("Exception args: %s", err.args)
            raise UpdateFailed(f"Error communicating with API: {err}") from err
