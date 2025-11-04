"""Sensor platform for Muller Intuis Connect."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class MullerSensorDescription(SensorEntityDescription):
    """Describe a Muller Intuis sensor."""

    value_fn: Callable[[dict[str, Any]], Any]


SENSOR_DESCRIPTIONS: tuple[MullerSensorDescription, ...] = (
    MullerSensorDescription(
        key="therm_measured_temperature",
        name="Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda room: room.get("therm_measured_temperature"),
    ),
    MullerSensorDescription(
        key="heating_power_request",
        name="Heating Power",
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda room: room.get("heating_power_request"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Muller Intuis sensor platform."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator = entry_data["coordinator"]

    rooms = coordinator.data.get("rooms", []) or []
    if not rooms:
        _LOGGER.debug("No rooms available for sensor creation")
        return

    entities: list[MullerIntuisRoomSensor] = []
    for room in rooms:
        room_id = room.get("id")
        if not room_id:
            continue
        for description in SENSOR_DESCRIPTIONS:
            if description.value_fn(room) is None:
                continue
            entities.append(
                MullerIntuisRoomSensor(coordinator, room_id=room_id, description=description)
            )

    if entities:
        async_add_entities(entities)
        _LOGGER.info("Added %s Muller Intuis sensors", len(entities))
    else:
        _LOGGER.debug("No sensor entities created for Muller Intuis")


class MullerIntuisRoomSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Muller Intuis room sensor."""

    entity_description: MullerSensorDescription

    def __init__(
        self,
        coordinator,
        *,
        room_id: str,
        description: MullerSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._room_id = room_id
        room = self._get_room()
        room_name = room.get("name", room_id)
        home_id = self._get_home_id()
        self._attr_name = f"{room_name} {description.name}"
        unique_id_base = f"{home_id}_{room_id}" if home_id else room_id
        self._attr_unique_id = f"{unique_id_base}_{description.key}"
        home_name = coordinator.data.get("home_name")
        if home_id:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, home_id)},
                name=home_name or "Muller Intuis Home",
                manufacturer="Muller",
            )

    @property
    def available(self) -> bool:
        """Return entity availability."""
        room = self._get_room()
        return room.get("reachable", True)

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        room = self._get_room()
        return self.entity_description.value_fn(room)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        room = self._get_room()
        return {"room_id": self._room_id, "anticipating": room.get("anticipating")}

    def _get_home_id(self) -> str | None:
        """Return the home ID from the coordinator."""
        home_id = self.coordinator.data.get("home_id")
        if home_id:
            return str(home_id)
        return getattr(self.coordinator, "home_id", None)

    def _get_room(self) -> dict[str, Any]:
        """Return the room data from the coordinator."""
        rooms_by_id = self.coordinator.data.get("rooms_by_id")
        if isinstance(rooms_by_id, dict):
            room = rooms_by_id.get(self._room_id)
            if room:
                return room

        for room in self.coordinator.data.get("rooms", []) or []:
            if room.get("id") == self._room_id:
                return room

        return {}
