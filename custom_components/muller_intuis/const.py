"""Constants for the Muller Intuis Connect integration."""

DOMAIN = "muller_intuis"

# Configuration keys
CONF_HOME_ID = "home_id"

# API endpoints
API_BASE_URL = "https://app.muller-intuitiv.net"
API_AUTH_URL = f"{API_BASE_URL}/oauth2/token"
API_HOMESDATA_URL = f"{API_BASE_URL}/api/homesdata"
API_HOMESTATUS_URL = f"{API_BASE_URL}/api/homestatus"
API_SETSTATE_URL = f"{API_BASE_URL}/syncapi/v1/setstate"
API_SETTHERMMODE_URL = f"{API_BASE_URL}/api/setthermmode"

# OAuth2 parameters
OAUTH_USER_PREFIX = "muller"
OAUTH_SCOPE = "read_muller write_muller"
OAUTH_GRANT_TYPE = "password"

# Update intervals
SCAN_INTERVAL_SECONDS = 300  # 5 minutes
TOKEN_REFRESH_MARGIN_SECONDS = 300  # 5 minutes before expiry

# Modes for rooms
MODE_MANUAL = "manual"
MODE_HOME = "home"  # Follow house schedule
MODE_OFF = "off"    # Turn off this room
MODE_HG = "hg"      # Frost protection for this room

# Modes for home
MODE_SCHEDULE = "schedule"
MODE_AWAY = "away"
MODE_HOME_HG = "hg"  # Frost protection for entire home

# HVAC modes mapping
HVAC_MODE_MAP = {
    MODE_SCHEDULE: "auto",
    MODE_AWAY: "eco",
    MODE_HOME_HG: "off",
    MODE_MANUAL: "heat",
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
ATTR_DURATION = "duration"
ATTR_END_TIME = "endtime"

# Default duration for manual mode (in minutes)
DEFAULT_MANUAL_DURATION = 180  # 3 hours
MAX_MANUAL_DURATION = 720  # 12 hours
