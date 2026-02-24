"""Constants for the StreakHub integration."""

from typing import Final

DOMAIN: Final = "streakhub"

# Storage
STORAGE_KEY: Final = "streakhub"
STORAGE_VERSION: Final = 1

# Configuration keys
CONF_NAME: Final = "name"
CONF_INITIAL_DATE: Final = "initial_date"
CONF_GOAL: Final = "goal"

# Entity keys
ENTITY_STREAK: Final = "streak"
ENTITY_RANK: Final = "rank"
ENTITY_RESET: Final = "reset"
ENTITY_DAYS_TO_GOAL: Final = "days_to_goal"
ENTITY_HAS_GOAL: Final = "has_goal"
ENTITY_GOAL: Final = "goal"

# Platforms
PLATFORMS: Final = ["sensor", "button", "binary_sensor", "number"]

# Icons
ICON_STREAK: Final = "mdi:counter"
ICON_RESET: Final = "mdi:restart"
ICON_TROPHY: Final = "mdi:trophy"
ICON_TROPHY_OUTLINE: Final = "mdi:trophy-outline"
ICON_MEDAL: Final = "mdi:medal-outline"
ICON_GOAL_NOT_REACHED: Final = "mdi:check-decagram-outline"
ICON_GOAL_REACHED: Final = "mdi:check-decagram"
ICON_HAS_GOAL: Final = "mdi:flag-checkered"
ICON_GOAL: Final = "mdi:target"

# Unit
UNIT_DAYS: Final = "d"
