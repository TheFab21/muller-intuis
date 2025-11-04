"""Select platform for Muller Intuis Connect."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Muller Intuis select platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    
    # Pour l'instant, on ne crée pas d'entités
    # Cela sera implémenté dans une version future
    _LOGGER.info("Select platform setup completed (no entities created yet)")
    
    # TODO: Créer l'entité select pour les plannings
