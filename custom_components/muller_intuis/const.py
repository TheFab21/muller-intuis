"""Constants for the Muller Intuis Connect integration."""

DOMAIN = "muller_intuis"

# Configuration keys
CONF_HOME_ID = "home_id"

# API endpoints
API_BASE_URL = "https://app.muller-intuitiv.net"
API_AUTH_URL = f"{API_BASE_URL}/oauth2/token"
API_HOMES_URL = f"{API_BASE_URL}/api/homesdata"
API_HOMESTATUS_URL = f"{API_BASE_URL}/api/homestatus"
API_SETROOMTHERMPOINT_URL = f"{API_BASE_URL}/api/setroomthermpoint"
API_SETTHERMMODE_URL = f"{API_BASE_URL}/api/setthermmode"

# OAuth2 parameters
OAUTH_USER_PREFIX = "muller"
OAUTH_SCOPE = "read_muller write_muller"
OAUTH_GRANT_TYPE = "password"

# Update intervals
SCAN_INTERVAL_SECONDS = 300  # 5 minutes
TOKEN_REFRESH_MARGIN_SECONDS = 300  # 5 minutes before expiry

# Modes
MODE_SCHEDULE = "schedule"
MODE_AWAY = "away"
MODE_HG = "hg"  # Hors-gel / Frost protection

# HVAC modes mapping
HVAC_MODE_MAP = {
    MODE_SCHEDULE: "auto",
    MODE_AWAY: "eco",
    MODE_HG: "off",
    "manual": "heat",
}

# Preset modes
PRESET_SCHEDULE = "schedule"
PRESET_AWAY = "away"
PRESET_FROST_PROTECTION = "frost_protection"
PRESET_MANUAL = "manual"

# Attributes
ATTR_ROOM_ID = "room_id"
ATTR_SCHEDULE_ID = "schedule_id"
ATTR_MODE = "mode"
ATTR_TEMP = "temp"
ATTR_TIMETABLE = "timetable"
ATTR_ZONES = "zones"
ATTR_NAME = "name"

# Services
SERVICE_SET_SCHEDULE = "set_schedule"
SERVICE_SYNC_SCHEDULE = "sync_schedule"
SERVICE_CREATE_SCHEDULE = "create_schedule"
SERVICE_DELETE_SCHEDULE = "delete_schedule"
SERVICE_RENAME_SCHEDULE = "rename_schedule"
SERVICE_SET_ROOM_THERMPOINT = "set_room_thermpoint"
SERVICE_SET_HOME_MODE = "set_home_mode"
