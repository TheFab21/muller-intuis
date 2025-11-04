"""Config flow pour Muller Intuis Connect."""
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MullerIntuisAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class MullerIntuisConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gestion du flux de configuration."""

    VERSION = 1

    def __init__(self):
        """Initialiser le flux de configuration."""
        self.api = None
        self.home_id = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Gérer l'étape initiale."""
        errors = {}

        if user_input is not None:
            client_id = user_input[CONF_CLIENT_ID]
            client_secret = user_input[CONF_CLIENT_SECRET]

            # Créer une instance de l'API pour tester
            session = async_get_clientsession(self.hass)
            api = MullerIntuisAPI(client_id, client_secret, session, self.hass)

            # Tester l'authentification
            try:
                # Pour le premier setup, demander les tokens OAuth
                return await self.async_step_oauth()
            except Exception as err:
                _LOGGER.error("Erreur de connexion: %s", err)
                errors["base"] = "cannot_connect"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_CLIENT_ID): str,
                vol.Required(CONF_CLIENT_SECRET): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def async_step_oauth(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Étape OAuth pour obtenir les tokens."""
        errors = {}

        if user_input is not None:
            # Valider les tokens
            refresh_token = user_input.get("refresh_token")
            
            if not refresh_token:
                errors["base"] = "invalid_auth"
            else:
                # Sauvegarder la configuration
                return self.async_create_entry(
                    title="Muller Intuis Connect",
                    data={
                        CONF_CLIENT_ID: user_input[CONF_CLIENT_ID],
                        CONF_CLIENT_SECRET: user_input[CONF_CLIENT_SECRET],
                        "refresh_token": refresh_token,
                        "home_id": user_input.get("home_id"),
                    },
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_CLIENT_ID): str,
                vol.Required(CONF_CLIENT_SECRET): str,
                vol.Required("refresh_token"): str,
                vol.Optional("home_id"): str,
            }
        )

        return self.async_show_form(
            step_id="oauth",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "auth_url": "https://api.netatmo.com/oauth2/authorize",
                "instructions": "Suivez le processus OAuth sur le site Netatmo pour obtenir votre refresh_token",
            },
        )
