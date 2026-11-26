### 🐞 Bug Fixes
- **Device version**: Tracker devices now show the installed StreakHub version instead of a fixed 1.0.0
- **Start date around midnight**: The setup dialog now takes "today" from the Home Assistant time zone. Before, the default start date and the "tomorrow" limit could be off by one day when the system clock used a different time zone

### 🔧 Infrastructure
- **Requires Home Assistant 2025.3 or newer**: StreakHub now uses current Home Assistant APIs. The Marketplace and HACS offer this update only on supported versions
- Tests now run on the official `pytest-homeassistant` package with Python 3.14 and cover 100% of the code

### 📝 Documentation
- README describes installation via the Marketplace (Home Assistant 2026.11 and newer) and HACS

**Full Changelog**: https://github.com/moerk-o/StreakHub/compare/v1.2.0...v1.2.1

---

# v1.2.0

### ✨ New Features
- **Goal-Tracking**: Set streak goals and track progress with new entities
  - Number entity to set and adjust your goal
  - Days-to-Goal sensor shows days remaining (positive), reached (0), or exceeded (negative)
  - Has-Goal binary sensor for conditional dashboard cards
  - Full backward compatibility - existing trackers automatically migrate

### 🔧 Infrastructure
- Automatic migration for existing trackers (adds goal=0)
- Adds HACS Compatibility

**Full Changelog**: https://github.com/moerk-o/StreakHub/compare/v1.1.1...v1.2.0

---

# v1.1.1

### 🐞 Bug Fixes
- **Translations**: Improved consistency of `undo_last_event` service description across languages ([#v1.1.1](https://github.com/moerk-o/StreakHub/commit/56822f2))

### 📝 Documentation
- Updated README with undo service documentation and companion card information
- Added GitHub Actions release workflow

**Full Changelog**: https://github.com/moerk-o/StreakHub/compare/v1.1.0...v1.1.1

---

# v1.1.0

### ✨ New Features
- **Undo Service**: Added `undo_last_event` service to restore previous streak if button was pressed accidentally

### 🐞 Bug Fixes
- **Rank Sensor Icon**: Updated icon logic for better visual feedback

### 🔧 Infrastructure
- Added comprehensive test suite with 113+ tests
- Improved storage data generator for history mocking

**Full Changelog**: https://github.com/moerk-o/StreakHub/compare/v1.0.0...v1.1.0

---

# v1.0.0

### ✨ New Features
- Initial release of StreakHub
- Unlimited independent streak trackers
- Current streak calculation in days
- All-time Top 3 ranking with historical data
- Gamification with trophy/medal icons
- Retroactive correction of streak start dates
- Multi-language support (English, German)

### 🔧 Infrastructure
- Config Flow with date validation
- Entity description pattern for correct entity IDs
- Comprehensive test coverage
- Type safety with MyPy

**Full Changelog**: https://github.com/moerk-o/StreakHub/commits/main

---
