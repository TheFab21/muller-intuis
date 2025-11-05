"""Config flow for Muller Intuis Connect integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CLIENT_ID): str,
        vol.Required(CONF_CLIENT_SECRET): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def validate_auth(
    hass: HomeAssistant, client_id: str, client_secret: str, username: str, password: str
) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    session = async_get_clientsession(hass)

    auth_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "username": username,
        "password": password,
        "grant_type": "password",
        "user_prefix": "muller",
        "scope": "read_muller write_muller",
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    try:
        async with session.post(
            "https://app.muller-intuitiv.net/oauth2/token",
            data=auth_data,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                _LOGGER.error("Authentication failed: %s - %s", response.status, error_text)
                raise InvalidAuth(f"Authentication failed with status {response.status}")

            data = await response.json()

            if "access_token" not in data:
                _LOGGER.error("No access_token in response: %s", data)
                raise InvalidAuth("No access_token in response")

            return {
                "access_token": data["access_token"],
                "refresh_token": data["refresh_token"],
                "expires_in": data.get("expires_in", 10800),
            }

    except aiohttp.ClientError as err:
        _LOGGER.error("Connection error during authentication: %s", err)
        raise CannotConnect from err
    except Exception as err:
        _LOGGER.error("Unexpected error during authentication: %s", err)
        raise InvalidAuth from err


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Muller Intuis Connect."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                auth_info = await validate_auth(
                    self.hass,
                    user_input[CONF_CLIENT_ID],
                    user_input[CONF_CLIENT_SECRET],
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD],
                )

                await self.async_set_unique_id(user_input[CONF_USERNAME].lower())
                self._abort_if_unique_id_configured()

                data = {
                    CONF_CLIENT_ID: user_input[CONF_CLIENT_ID],
                    CONF_CLIENT_SECRET: user_input[CONF_CLIENT_SECRET],
                    CONF_USERNAME: user_input[CONF_USERNAME],
                    CONF_PASSWORD: user_input[CONF_PASSWORD],
                    "access_token": auth_info["access_token"],
                    "refresh_token_value": auth_info["refresh_token"],
                    "expires_in": auth_info["expires_in"],
                }

                return self.async_create_entry(
                    title=f"Muller Intuis ({user_input[CONF_USERNAME]})",
                    data=data,
                )

            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class InvalidAuth(Exception):
    """Error to indicate there is invalid auth."""
