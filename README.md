# StreakHub

A Home Assistant custom integration for tracking streaks - the number of days between recurring events.

## Purpose

StreakHub enables tracking of "streaks" - periods between repeated events. Typical use cases:

- **Abstinence tracking:** "Days without sugar", "Days without cigarettes", "Days without alcohol"
- **Habit tracking (inverted):** "Days since last workout" (low = bad)
- **General tracking:** Any type of event where you want to measure intervals

Features:

- Unlimited independent trackers
- Current streak in days
- Ranking of current streak (Top 3 or not)
- Historical Top 3 with gamification aspect
- Retroactive correction of streak start

## Installation

### Manual Installation

1. Copy the `custom_components/streakhub` folder to your Home Assistant's `custom_components` directory
2. Restart Home Assistant
3. Go to **Settings** → **Devices & Services** → **Add Integration**
4. Search for "StreakHub" and follow the setup wizard

### HACS (Custom Repository)

This integration is not yet available in the default HACS repository. To install via HACS:

1. Open HACS in your Home Assistant
2. Click the three dots in the top right corner
3. Select "Custom repositories"
4. Add the repository URL and select "Integration" as category
5. Install "StreakHub"
6. Restart Home Assistant

## Configuration

StreakHub is configured entirely through the UI (no YAML configuration).

### Adding a Tracker

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "StreakHub"
3. Enter a name for your tracker (e.g., "Sugar", "Cigarettes", "Workout")
4. Optionally set an initial start date (defaults to today)
5. Click Submit

Each tracker creates its own device with associated entities.

## Entities

Each tracker creates 3 entities:

### Streak Sensor (`sensor.{name}_streak`)

Shows the number of days since the last event.

| Property | Value |
|----------|-------|
| State | Number of days (integer) |
| State Class | `measurement` |
| Unit | `d` (days) |
| Icon | `mdi:counter` |

**Attributes:**
- `streak_start`: First day of the current streak (ISO 8601 date)

**Behavior:**
- On the day of an event (button press): Shows `0`
- Otherwise: Shows days since streak start (inclusive)

### Rank Sensor (`sensor.{name}_rank`)

Shows the ranking of the current streak in the all-time Top 3.

| Property | Value |
|----------|-------|
| State | 1, 2, 3 (if in Top 3) or 0 (not in Top 3) |
| Icon | Dynamic based on rank |

**Icons:**
- Rank 1: `mdi:trophy` (Record!)
- Rank 2-3: `mdi:medal-outline`
- Not in Top 3: `mdi:trophy-outline`

**Attributes:**
- `top_3`: List of the three longest streaks

**Top 3 Structure:**
```yaml
top_3:
  - rank: 1
    start: "2024-11-01"
    end: "2024-12-24"
    days: 54
  - rank: 2
    start: "2025-01-14"
    end: null           # Current streak (still running)
    days: 28
  - rank: 3
    start: "2025-01-01"
    end: "2025-01-13"
    days: 13
```

### Reset Button (`button.{name}_reset`)

Button to end the current streak.

| Property | Value |
|----------|-------|
| Icon | `mdi:restart` |

**Behavior:**
Pressing means "the event happened today":
- Current streak ends (yesterday was the last day without the event)
- New streak starts tomorrow
- Streak sensor shows `0` today

## Services

### `streakhub.set_streak_start`

Corrects the streak start date for missed button presses.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `entity_id` | string | Yes | Entity ID of a StreakHub sensor |
| `date` | date | Yes | New start date (first day WITHOUT the event) |

**Example:**
```yaml
service: streakhub.set_streak_start
target:
  entity_id: sensor.sugar_streak
data:
  date: "2025-01-25"
```

**Use Case:**
If you forgot to press the button on January 24th, call the service with date `2025-01-25` (the day AFTER the forgotten event).

**Validation:**
- Date cannot be in the future
- Date must be after the current streak start

## Dashboard Examples

### Simple Entities Card

```yaml
type: entities
entities:
  - entity: sensor.sugar_streak
    name: Days without sugar
  - entity: sensor.sugar_rank
    name: Ranking
  - entity: button.sugar_reset
    name: Had sugar!
```

### Trophy Display with Template

```yaml
type: markdown
content: |
  {% set rank = states('sensor.sugar_rank') | int %}
  {% if rank == 1 %}
  # 🥇 NEW RECORD!
  {% elif rank == 2 %}
  # 🥈 2nd Place
  {% elif rank == 3 %}
  # 🥉 3rd Place
  {% else %}
  # Keep going!
  {% endif %}

  **{{ states('sensor.sugar_streak') }} days** without sugar
```

### Top 3 Leaderboard

```yaml
type: markdown
content: |
  ## 🏆 Leaderboard
  {% set top3 = state_attr('sensor.sugar_rank', 'top_3') %}
  {% for streak in top3 %}
  {% if streak.rank == 1 %}🥇{% elif streak.rank == 2 %}🥈{% else %}🥉{% endif %} **{{ streak.days }} days** ({{ streak.start }}{% if streak.end %} – {{ streak.end }}{% else %} – ongoing{% endif %})
  {% endfor %}
```

### Get Record Directly

```yaml
# The record is always the first entry in top_3
{{ state_attr('sensor.sugar_rank', 'top_3')[0].days }} days
```

## How Streaks Work

A streak counts the **days WITHOUT the event**. The day of the event (button press) belongs to **no** streak.

### Example Timeline

Tracking "Days without sugar":

```
01.01: Streak starts (streak_start = 01.01)
01.01: ✓ [1] - 1 day without sugar
02.01: ✓ [2] - 2 days without sugar
...
13.01: ✓ [13] - 13 days without sugar
14.01: ✗ [0] - SUGAR! Button pressed → Streak = 0
15.01: ✓ [1] - 1 day without sugar (new streak)
```

### Button Press Logic

When the button is pressed on day X:
1. Event day (day WITH event): X
2. Last day of old streak: X - 1
3. First day of new streak: X + 1
4. Streak value on event day: 0

### Edge Cases

| Situation | Behavior |
|-----------|----------|
| First start | `streak_start` = today, `history` = empty, `rank` = 1 |
| Button on event day | Streak sensor shows 0 |
| Button twice in a row | 0-day streak is NOT saved |
| Button on streak start day | 0-day streak is NOT saved |
| `set_streak_start` in future | ServiceValidationError |
| `set_streak_start` before streak start | ServiceValidationError |
| Fewer than 3 streaks | `top_3` contains fewer than 3 entries |

## Troubleshooting

### Streak shows 0 unexpectedly

This is correct behavior on the event day. The streak will show 1 starting tomorrow.

### Reset button doesn't work

Check the Home Assistant logs for errors. The button requires the integration to be fully loaded.

### Service call fails

Ensure:
- The entity ID is correct and belongs to StreakHub
- The date format is correct (YYYY-MM-DD)
- The date is not in the future
- The date is after the current streak start

### Data location

Tracker data is stored in `.storage/streakhub` in your Home Assistant configuration directory.

## License

This project is licensed under the MIT License.
