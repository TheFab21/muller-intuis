"""Support des entités climate pour Muller Intuis."""
import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_ANTICIPATING,
    ATTR_HEATING_POWER_REQUEST,
    ATTR_REACHABLE,
    DOMAIN,
    MAX_TEMP,
    MIN_TEMP,
    MODE_HA_TO_NETATMO,
    MODE_NETATMO_TO_HA,
    PRESET_AWAY,
    PRESET_HG,
    PRESET_MANUAL,
    PRESET_SCHEDULE,
    TARGET_TEMP_STEP,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configurer les entités climate."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]

    entities = []

    # Créer une entité climate pour chaque pièce
    rooms = coordinator.data.get("rooms", [])
    for room in rooms:
        entities.append(MullerIntuisClimate(coordinator, api, room))

    async_add_entities(entities)


class MullerIntuisClimate(CoordinatorEntity, ClimateEntity):
    """Représente un radiateur Muller Intuis."""

    _attr_has_entity_name = True
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = TARGET_TEMP_STEP
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.AUTO, HVACMode.OFF]
    _attr_preset_modes = [PRESET_SCHEDULE, PRESET_AWAY, PRESET_HG, PRESET_MANUAL]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
    )

    def __init__(self, coordinator, api, room_data):
        """Initialiser l'entité climate."""
        super().__init__(coordinator)
        self.api = api
        self._room_id = room_data["id"]
        self._attr_name = room_data.get("name", f"Room {self._room_id}")
        self._attr_unique_id = f"{DOMAIN}_{self._room_id}"
        self._room_data = room_data

    @property
    def device_info(self):
        """Informations sur le device."""
        return {
            "identifiers": {(DOMAIN, self._room_id)},
            "name": self._attr_name,
            "manufacturer": "Muller Intuis",
            "model": "Radiateur connecté",
        }

    @property
    def room_data(self):
        """Récupérer les données de la pièce."""
        rooms = self.coordinator.data.get("rooms", [])
        for room in rooms:
            if room["id"] == self._room_id:
                return room
        return {}

    @property
    def current_temperature(self):
        """Température actuelle."""
        return self.room_data.get("therm_measured_temperature")

    @property
    def target_temperature(self):
        """Température cible."""
        return self.room_data.get("therm_setpoint_temperature")

    @property
    def min_temp(self):
        """Température minimale."""
        return MIN_TEMP

    @property
    def max_temp(self):
        """Température maximale."""
        return MAX_TEMP

    @property
    def hvac_mode(self):
        """Mode HVAC actuel."""
        mode = self.room_data.get("therm_setpoint_mode")
        
        if mode == "off":
            return HVACMode.OFF
        elif mode == "schedule":
            return HVACMode.AUTO
        else:
            return HVACMode.HEAT

    @property
    def preset_mode(self):
        """Mode preset actuel."""
        mode = self.room_data.get("therm_setpoint_mode")
        return MODE_NETATMO_TO_HA.get(mode, PRESET_SCHEDULE)

    @property
    def extra_state_attributes(self):
        """Attributs supplémentaires."""
        room = self.room_data
        return {
            ATTR_HEATING_POWER_REQUEST: room.get("heating_power_request", 0),
            ATTR_REACHABLE: room.get("reachable", False),
            ATTR_ANTICIPATING: room.get("anticipating", False),
            "open_window": room.get("open_window", False),
        }

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Définir la température cible."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        await self.api.async_set_thermpoint(
            self._room_id, mode="manual", temp=temperature
        )
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Définir le mode HVAC."""
        if hvac_mode == HVACMode.OFF:
            mode = "off"
        elif hvac_mode == HVACMode.AUTO:
            mode = "schedule"
        else:
            mode = "manual"

        await self.api.async_set_thermpoint(self._room_id, mode=mode)
        await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Définir le preset mode."""
        netatmo_mode = MODE_HA_TO_NETATMO.get(preset_mode)
        if netatmo_mode:
            await self.api.async_set_thermpoint(self._room_id, mode=netatmo_mode)
            await self.coordinator.async_request_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Gérer les mises à jour du coordinateur."""
        self.async_write_ha_state()
