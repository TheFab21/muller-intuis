"""Capteurs pour Muller Intuis."""
import logging
from datetime import datetime, timedelta

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfPower, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configurer les capteurs."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]

    entities = []

    # Créer les capteurs pour chaque pièce
    rooms = coordinator.data.get("rooms", [])
    for room in rooms:
        room_id = room["id"]
        room_name = room.get("name", f"Room {room_id}")

        # Capteur de température
        entities.append(
            MullerIntuisTemperatureSensor(coordinator, room_id, room_name)
        )

        # Capteur de puissance de chauffe
        entities.append(
            MullerIntuisHeatingPowerSensor(coordinator, room_id, room_name)
        )

        # Capteur d'énergie journalière
        entities.append(
            MullerIntuisDailyEnergySensor(coordinator, api, room_id, room_name)
        )

    # Capteurs de plannings
    schedules = coordinator.data.get("schedules", {})
    for schedule_id, schedule in schedules.items():
        entities.append(MullerIntuisScheduleSensor(coordinator, schedule_id, schedule))

    # Capteur du planning actif
    entities.append(MullerIntuisActiveScheduleSensor(coordinator))

    async_add_entities(entities)


class MullerIntuisBaseSensor(CoordinatorEntity, SensorEntity):
    """Classe de base pour les capteurs Muller Intuis."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, room_id, room_name):
        """Initialiser le capteur."""
        super().__init__(coordinator)
        self._room_id = room_id
        self._room_name = room_name

    @property
    def device_info(self):
        """Informations sur le device."""
        return {
            "identifiers": {(DOMAIN, self._room_id)},
            "name": self._room_name,
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


class MullerIntuisTemperatureSensor(MullerIntuisBaseSensor):
    """Capteur de température."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, room_id, room_name):
        """Initialiser le capteur."""
        super().__init__(coordinator, room_id, room_name)
        self._attr_name = "Temperature"
        self._attr_unique_id = f"{DOMAIN}_{room_id}_temperature"

    @property
    def native_value(self):
        """Valeur du capteur."""
        return self.room_data.get("therm_measured_temperature")


class MullerIntuisHeatingPowerSensor(MullerIntuisBaseSensor):
    """Capteur de puissance de chauffe."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.WATT

    def __init__(self, coordinator, room_id, room_name):
        """Initialiser le capteur."""
        super().__init__(coordinator, room_id, room_name)
        self._attr_name = "Heating Power"
        self._attr_unique_id = f"{DOMAIN}_{room_id}_heating_power"

    @property
    def native_value(self):
        """Valeur du capteur."""
        heating_power_request = self.room_data.get("heating_power_request", 0)
        # Convertir le pourcentage en watts (supposons 1000W max par radiateur)
        max_power = 1000
        return int(heating_power_request * max_power / 100)


class MullerIntuisDailyEnergySensor(MullerIntuisBaseSensor):
    """Capteur d'énergie quotidienne."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

    def __init__(self, coordinator, api, room_id, room_name):
        """Initialiser le capteur."""
        super().__init__(coordinator, room_id, room_name)
        self.api = api
        self._attr_name = "Daily Energy"
        self._attr_unique_id = f"{DOMAIN}_{room_id}_daily_energy"
        self._last_reset = datetime.now().date()
        self._energy_today = 0

    @property
    def native_value(self):
        """Valeur du capteur."""
        return self._energy_today

    async def async_update(self):
        """Mettre à jour l'énergie."""
        today = datetime.now().date()
        
        # Réinitialiser si on change de jour
        if today != self._last_reset:
            self._last_reset = today
            self._energy_today = 0

        # Récupérer les mesures
        try:
            end_time = int(datetime.now().timestamp())
            begin_time = int(datetime.combine(today, datetime.min.time()).timestamp())

            measures = await self.api.async_get_room_measure(
                self._room_id,
                scale="30min",
                type_measure="sum_energy_elec",
                date_begin=begin_time,
                date_end=end_time,
            )

            if measures and "body" in measures:
                values = measures["body"][0].get("value", [[]])
                total_wh = sum(v[0] for v in values if v and len(v) > 0)
                self._energy_today = round(total_wh / 1000, 3)  # Convertir en kWh
        except Exception as err:
            _LOGGER.error("Erreur lors de la récupération de l'énergie: %s", err)


class MullerIntuisScheduleSensor(CoordinatorEntity, SensorEntity):
    """Capteur pour un planning."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, schedule_id, schedule_data):
        """Initialiser le capteur."""
        super().__init__(coordinator)
        self._schedule_id = schedule_id
        self._schedule_name = schedule_data.get("name", schedule_id)
        self._attr_name = f"Schedule {self._schedule_name}"
        self._attr_unique_id = f"{DOMAIN}_schedule_{schedule_id}"

    @property
    def native_value(self):
        """État du capteur."""
        schedules = self.coordinator.data.get("schedules", {})
        schedule = schedules.get(self._schedule_id, {})
        return schedule.get("selected", False)

    @property
    def extra_state_attributes(self):
        """Attributs du planning."""
        schedules = self.coordinator.data.get("schedules", {})
        schedule = schedules.get(self._schedule_id, {})
        
        return {
            "schedule_id": self._schedule_id,
            "name": schedule.get("name"),
            "timetable": schedule.get("timetable", []),
            "zones": schedule.get("zones", []),
            "away_temp": schedule.get("away_temp"),
            "hg_temp": schedule.get("hg_temp"),
        }


class MullerIntuisActiveScheduleSensor(CoordinatorEntity, SensorEntity):
    """Capteur du planning actif."""

    _attr_has_entity_name = True
    _attr_name = "Active Schedule"

    def __init__(self, coordinator):
        """Initialiser le capteur."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_active_schedule"

    @property
    def native_value(self):
        """Nom du planning actif."""
        schedules = self.coordinator.data.get("schedules", {})
        for schedule_id, schedule in schedules.items():
            if schedule.get("selected"):
                return schedule.get("name", schedule_id)
        return None

    @property
    def extra_state_attributes(self):
        """Attributs du planning actif."""
        schedules = self.coordinator.data.get("schedules", {})
        for schedule_id, schedule in schedules.items():
            if schedule.get("selected"):
                return {
                    "schedule_id": schedule_id,
                    "timetable": schedule.get("timetable", []),
                    "zones": schedule.get("zones", []),
                }
        return {}
