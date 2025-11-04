"""Climate platform for Muller Intuis Connect."""

from __future__ import annotations

import logging
from typing import Any, cast

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    DOMAIN,
    PRESET_AWAY,
    PRESET_FROST_PROTECTION,
    PRESET_MANUAL,
    PRESET_SCHEDULE,
)

ROOM_MODE_TO_PRESET = {
    "schedule": PRESET_SCHEDULE,
    "manual": PRESET_MANUAL,
    "away": PRESET_AWAY,
    "hg": PRESET_FROST_PROTECTION,
}

HVAC_MODE_TO_ROOM_MODE = {
    HVACMode.AUTO: "schedule",
    HVACMode.HEAT: "manual",
    HVACMode.OFF: "hg",
}

ROOM_MODE_TO_HVAC_MODE = {
    "schedule": HVACMode.AUTO,
    "manual": HVACMode.HEAT,
    "away": HVACMode.HEAT,
    "hg": HVACMode.OFF,
}

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Muller Intuis climate platform."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator = entry_data["coordinator"]
    api_client = entry_data["api_client"]

    rooms = coordinator.data.get("rooms", []) or []
    if not rooms:
        _LOGGER.warning("No rooms reported by Muller Intuis API; no climate entities created")
        return

    entities: list[MullerIntuisClimate] = []
    for room in rooms:
        room_id = room.get("id")
        if not room_id:
            continue
        entities.append(MullerIntuisClimate(coordinator, api_client, room_id))

    if entities:
        async_add_entities(entities)
        _LOGGER.info("Added %s Muller Intuis climate entities", len(entities))
    else:
        _LOGGER.warning("No valid rooms found to create Muller Intuis climate entities")


class MullerIntuisClimate(CoordinatorEntity, ClimateEntity):
    """Representation of a Muller Intuis climate device."""

    _attr_has_entity_name = True
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
    )
    _attr_hvac_modes = [HVACMode.AUTO, HVACMode.HEAT, HVACMode.OFF]
    _attr_preset_modes = [
        PRESET_SCHEDULE,
        PRESET_MANUAL,
        PRESET_AWAY,
        PRESET_FROST_PROTECTION,
    ]

    def __init__(self, coordinator, api_client, room_id: str) -> None:
        """Initialize the climate device."""
        super().__init__(coordinator)
        self._api = api_client
        self._room_id = room_id
        room = self._get_room()
        room_name = room.get("name", room_id)
        home_id = self._get_home_id()
        self._attr_name = room_name
        self._attr_unique_id = f"{home_id}_{self._room_id}_climate" if home_id else f"{self._room_id}_climate"
        home_name = self.coordinator.data.get("home_name")
        if home_id:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, home_id)},
                name=home_name or "Muller Intuis Home",
                manufacturer="Muller",
            )

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        room = self._get_room()
        return cast(float | None, room.get("therm_measured_temperature"))

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        room = self._get_room()
        return cast(float | None, room.get("therm_setpoint_temperature"))

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current operation mode."""
        room_mode = self._get_room().get("therm_setpoint_mode")
        return ROOM_MODE_TO_HVAC_MODE.get(room_mode, HVACMode.AUTO)

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode."""
        room_mode = self._get_room().get("therm_setpoint_mode")
        return ROOM_MODE_TO_PRESET.get(room_mode)

    @property
    def available(self) -> bool:
        """Return if the device is available."""
        room = self._get_room()
        return room.get("reachable", True)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        room = self._get_room()
        attributes: dict[str, Any] = {}
        for key in ("heating_power_request", "anticipating"):
            if key in room:
                attributes[key] = room[key]
        attributes["room_id"] = self._room_id
        return attributes

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        return 7.0

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        return 30.0

    @property
    def target_temperature_step(self) -> float:
        """Return the supported temperature step."""
        return 0.5

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        home_id = self._get_home_id()
        if not home_id:
            _LOGGER.error("Cannot set temperature without home ID")
            return

        _LOGGER.debug("Setting temperature to %s for room %s", temperature, self._room_id)
        await self._api.set_room_thermpoint(
            home_id,
            self._room_id,
            "manual",
            temp=float(temperature),
        )
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        room_mode = HVAC_MODE_TO_ROOM_MODE.get(hvac_mode)
        if room_mode is None:
            _LOGGER.error("Unsupported HVAC mode %s", hvac_mode)
            return

        home_id = self._get_home_id()
        if not home_id:
            _LOGGER.error("Cannot set HVAC mode without home ID")
            return

        temp: float | None = None
        if room_mode == "manual":
            temp = self.target_temperature

        _LOGGER.debug(
            "Setting HVAC mode %s (API mode %s) for room %s", hvac_mode, room_mode, self._room_id
        )
        await self._api.set_room_thermpoint(home_id, self._room_id, room_mode, temp=temp)
        await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set a new preset mode."""
        room_mode = None
        for mode, preset in ROOM_MODE_TO_PRESET.items():
            if preset == preset_mode:
                room_mode = mode
                break

        if room_mode is None:
            _LOGGER.error("Unsupported preset mode %s", preset_mode)
            return

        home_id = self._get_home_id()
        if not home_id:
            _LOGGER.error("Cannot set preset mode without home ID")
            return

        temp: float | None = None
        if room_mode == "manual":
            temp = self.target_temperature

        _LOGGER.debug(
            "Setting preset %s (API mode %s) for room %s", preset_mode, room_mode, self._room_id
        )
        await self._api.set_room_thermpoint(home_id, self._room_id, room_mode, temp=temp)
        await self.coordinator.async_request_refresh()

    def _get_home_id(self) -> str | None:
        """Return the home ID from the coordinator."""
        home_id = self.coordinator.data.get("home_id")
        if home_id:
            return cast(str, home_id)
        return cast(str | None, getattr(self.coordinator, "home_id", None))

    def _get_room(self) -> dict[str, Any]:
        """Return the room data for this entity."""
        rooms_by_id = self.coordinator.data.get("rooms_by_id")
        if isinstance(rooms_by_id, dict):
            room = rooms_by_id.get(self._room_id)
            if room:
                return room

        for room in self.coordinator.data.get("rooms", []) or []:
            if room.get("id") == self._room_id:
                return room

        return {}
