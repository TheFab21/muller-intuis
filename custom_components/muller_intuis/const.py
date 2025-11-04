"""Constantes pour l'intégration Muller Intuis."""

DOMAIN = "muller_intuis"

# API URLs
API_BASE_URL = "https://api.netatmo.com"
AUTH_URL = f"{API_BASE_URL}/oauth2/token"
HOME_STATUS_URL = f"{API_BASE_URL}/api/homestatus"
SET_THERMPOINT_URL = f"{API_BASE_URL}/api/setthermpoint"
SET_THERM_MODE_URL = f"{API_BASE_URL}/api/setthermmode"
GET_MEASURE_URL = f"{API_BASE_URL}/api/getmeasure"
GET_ROOM_MEASURE_URL = f"{API_BASE_URL}/api/getroommeasure"
SYNC_SCHEDULE_URL = f"{API_BASE_URL}/api/syncschedule"
SWITCH_SCHEDULE_URL = f"{API_BASE_URL}/api/switchschedule"
CREATE_NEW_SCHEDULE_URL = f"{API_BASE_URL}/api/createnewschedule"
DELETE_SCHEDULE_URL = f"{API_BASE_URL}/api/deleteschedule"
RENAME_SCHEDULE_URL = f"{API_BASE_URL}/api/renamehomeschedule"

# Modes de chauffage
THERM_MODE_SCHEDULE = "schedule"
THERM_MODE_AWAY = "away"
THERM_MODE_HG = "hg"  # Hors-gel
THERM_MODE_MANUAL = "manual"

THERM_MODES = [
    THERM_MODE_SCHEDULE,
    THERM_MODE_AWAY,
    THERM_MODE_HG,
    THERM_MODE_MANUAL,
]

# Modes Home Assistant
PRESET_SCHEDULE = "schedule"
PRESET_AWAY = "away"
PRESET_HG = "frost_protection"
PRESET_MANUAL = "manual"

# Mapping des modes
MODE_NETATMO_TO_HA = {
    THERM_MODE_SCHEDULE: PRESET_SCHEDULE,
    THERM_MODE_AWAY: PRESET_AWAY,
    THERM_MODE_HG: PRESET_HG,
    THERM_MODE_MANUAL: PRESET_MANUAL,
}

MODE_HA_TO_NETATMO = {v: k for k, v in MODE_NETATMO_TO_HA.items()}

# Attributs
ATTR_SCHEDULE_ID = "schedule_id"
ATTR_SCHEDULE_NAME = "schedule_name"
ATTR_SELECTED_SCHEDULE = "selected_schedule"
ATTR_ZONES = "zones"
ATTR_TIMETABLE = "timetable"
ATTR_AWAY_TEMP = "away_temp"
ATTR_HG_TEMP = "hg_temp"
ATTR_HEATING_POWER_REQUEST = "heating_power_request"
ATTR_REACHABLE = "reachable"
ATTR_ANTICIPATING = "anticipating"

# Services
SERVICE_SET_SCHEDULE = "set_schedule"
SERVICE_SYNC_SCHEDULE = "sync_schedule"
SERVICE_CREATE_SCHEDULE = "create_schedule"
SERVICE_DELETE_SCHEDULE = "delete_schedule"
SERVICE_RENAME_SCHEDULE = "rename_schedule"
SERVICE_SET_ROOM_THERMPOINT = "set_room_thermpoint"
SERVICE_SET_HOME_MODE = "set_home_mode"

# Limites
MIN_TEMP = 7
MAX_TEMP = 30
TARGET_TEMP_STEP = 0.5
