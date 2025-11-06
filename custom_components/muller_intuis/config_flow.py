"""Config flow for Muller Intuis Connect integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import aiohttp

from .const import (
    DOMAIN,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    OAUTH_TOKEN_URL,
)

_LOGGER = logging.getLogger(__name__)


class MullerIntuisConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Muller Intuis Connect."""
    
    VERSION = 1
    
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            # Valider les identifiants
            try:
                await self._test_credentials(
                    user_input[CONF_CLIENT_ID],
                    user_input[CONF_CLIENT_SECRET],
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD],
                )
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Créer l'entrée
                return self.async_create_entry(
                    title="Muller Intuis Connect",
                    data=user_input,
                )
        
        # Afficher le formulaire
        data_schema = vol.Schema(
            {
                vol.Required(CONF_CLIENT_ID): str,
                vol.Required(CONF_CLIENT_SECRET): str,
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )
        
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
    
    async def _test_credentials(
        self,
        client_id: str,
        client_secret: str,
        username: str,
        password: str,
    ) -> bool:
        """Test if credentials are valid."""
        session = async_get_clientsession(self.hass)
        
        data = {
            "grant_type": "password",
            "client_id": client_id,
            "client_secret": client_secret,
            "username": username,
            "password": password,
            "scope": "read_muller write_muller",
            "user_prefix": "muller",
        }
        
        try:
            async with session.post(OAUTH_TOKEN_URL, data=data, timeout=10) as response:
                if response.status == 200:
                    return True
                elif response.status in [401, 403]:
                    raise InvalidAuth
                else:
                    raise CannotConnect
        except aiohttp.ClientError as err:
            _LOGGER.error("Connection error: %s", err)
            raise CannotConnect from err


class InvalidAuth(Exception):
    """Error to indicate there is invalid auth."""


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""
