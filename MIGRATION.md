# Storage Migration Plan

This document describes the storage versioning and migration strategy for StreakHub.

## Current Version

**Storage Version: 1**

## Storage Location

Data is stored in `.storage/streakhub` within the Home Assistant configuration directory.

## Storage Structure (v1)

```json
{
  "version": 1,
  "data": {
    "trackers": {
      "<tracker_id>": {
        "streak_start": "<ISO 8601 date>",
        "history": [
          {
            "start": "<ISO 8601 date>",
            "end": "<ISO 8601 date>",
            "days": <integer>
          }
        ]
      }
    }
  }
}
```

## Migration Strategy

### General Principles

1. **Storage is versioned**: The `Store` class from Home Assistant handles version tracking automatically.

2. **Backward compatibility**: Older data formats are migrated to the current version on load.

3. **Non-destructive**: Migrations never delete user data; they transform it to the new format.

4. **Atomic saves**: Storage is saved atomically to prevent corruption.

### Implementation

The migration is handled in the `Store` class constructor via the `migration` parameter. When a new version is needed:

```python
async def async_migrate(old_data: dict) -> dict:
    """Migrate storage data to current version."""
    if old_data["version"] == 1:
        # Migration from v1 to v2 (example)
        old_data["version"] = 2
        # ... perform migration ...
    return old_data

store = Store(
    hass,
    STORAGE_VERSION,
    STORAGE_KEY,
    migration=async_migrate,
)
```

## Version History

### Version 1 (Initial Release)

**Schema:**
- `trackers`: Dictionary of tracker_id → TrackerData
- `TrackerData.streak_start`: ISO 8601 date string
- `TrackerData.history`: List of HistoryEntry
- `HistoryEntry.start`: ISO 8601 date string
- `HistoryEntry.end`: ISO 8601 date string
- `HistoryEntry.days`: Integer

**Notes:**
- Initial storage format
- No previous version to migrate from

## Future Migration Examples

### Example: Adding a new field (v1 → v2)

If we need to add a `created_at` timestamp to each tracker:

```python
async def async_migrate(old_data: dict) -> dict:
    if old_data["version"] == 1:
        for tracker_data in old_data["data"]["trackers"].values():
            # Add created_at with a default value
            tracker_data["created_at"] = tracker_data["streak_start"]
        old_data["version"] = 2
    return old_data
```

### Example: Renaming a field (v2 → v3)

If we need to rename `streak_start` to `current_streak_start`:

```python
async def async_migrate(old_data: dict) -> dict:
    # First apply v1 → v2 migration if needed
    if old_data["version"] == 1:
        # ... v1 → v2 migration ...
        old_data["version"] = 2

    if old_data["version"] == 2:
        for tracker_data in old_data["data"]["trackers"].values():
            tracker_data["current_streak_start"] = tracker_data.pop("streak_start")
        old_data["version"] = 3
    return old_data
```

### Example: Restructuring data (v3 → v4)

If we need to move history to a separate structure:

```python
async def async_migrate(old_data: dict) -> dict:
    # Apply previous migrations first...

    if old_data["version"] == 3:
        old_data["data"]["history_archive"] = {}
        for tracker_id, tracker_data in old_data["data"]["trackers"].items():
            old_data["data"]["history_archive"][tracker_id] = tracker_data.pop("history")
            tracker_data["history"] = []  # Keep only recent in tracker
        old_data["version"] = 4
    return old_data
```

## Testing Migrations

When adding a migration:

1. Create test fixtures with old format data
2. Run migration function
3. Verify new format is correct
4. Verify no data loss
5. Test edge cases (empty data, missing fields)

Example test:

```python
async def test_migrate_v1_to_v2():
    old_data = {
        "version": 1,
        "data": {
            "trackers": {
                "test": {
                    "streak_start": "2025-01-01",
                    "history": []
                }
            }
        }
    }

    new_data = await async_migrate(old_data)

    assert new_data["version"] == 2
    assert "created_at" in new_data["data"]["trackers"]["test"]
```

## Recovery Procedures

### Corrupted Storage

If storage becomes corrupted:

1. Home Assistant will fail to load the integration
2. Check logs for JSON parse errors
3. Manually inspect `.storage/streakhub`
4. If recoverable, fix JSON syntax
5. If not recoverable, delete file (data loss) and reconfigure

### Manual Backup

Users can backup their data by copying:
```
<config>/.storage/streakhub
```

### Manual Restore

To restore from backup:

1. Stop Home Assistant
2. Copy backup file to `.storage/streakhub`
3. Ensure file permissions are correct
4. Start Home Assistant

## Monitoring

Log messages for storage operations:

- `INFO`: Tracker initialized, tracker removed
- `DEBUG`: Storage loaded, storage saved, migration applied
- `ERROR`: Storage load failure, migration failure, corruption detected
