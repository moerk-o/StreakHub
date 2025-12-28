"""Constants for the StreakHub integration."""

from typing import Final

DOMAIN: Final = "streakhub"

# Storage
STORAGE_KEY: Final = "streakhub"
STORAGE_VERSION: Final = 1

# Configuration keys
CONF_NAME: Final = "name"
CONF_INITIAL_DATE: Final = "initial_date"

# Entity keys
ENTITY_STREAK: Final = "streak"
ENTITY_RANK: Final = "rank"
ENTITY_RESET: Final = "reset"

# Platforms
PLATFORMS: Final = ["sensor", "button"]

# Icons
ICON_STREAK: Final = "mdi:counter"
ICON_RESET: Final = "mdi:restart"
ICON_TROPHY: Final = "mdi:trophy"
ICON_TROPHY_OUTLINE: Final = "mdi:trophy-outline"
ICON_MEDAL: Final = "mdi:medal-outline"

# Unit
UNIT_DAYS: Final = "d"
