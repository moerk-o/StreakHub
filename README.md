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
- Goal tracking with progress monitoring
- Ranking of current streak (Top 3 or not)
- Historical Top 3 
- Retroactive correction of streak start

## Installation

Requires Home Assistant 2025.3 or newer.

StreakHub is not listed in the default catalog yet, so add it via its repository link.

### Marketplace (Home Assistant 2026.11 and newer)

1. Go to **Settings** → **Marketplace** → **Add from link**
2. Enter `moerk-o/StreakHub` and select **Add**
3. Open the repository page and select **Install**, then restart Home Assistant when the Marketplace asks for it
4. Go to **Settings** → **Devices & Services** → **Add Integration**
5. Search for "StreakHub" and follow the setup wizard

### HACS (Home Assistant 2026.10 and older)

1. Open HACS in your Home Assistant
2. Click the three dots in the top right corner
3. Select "Custom repositories"
4. Add `https://github.com/moerk-o/StreakHub` and select "Integration" as category
5. Install "StreakHub"
6. Restart Home Assistant
7. Go to **Settings** → **Devices & Services** → **Add Integration** and search for "StreakHub"

### Manual

1. Download `streakhub.zip` from the latest [GitHub release](https://github.com/moerk-o/StreakHub/releases)
2. Unpack it into `config/custom_components/streakhub` in your Home Assistant configuration
3. Restart Home Assistant
4. Go to **Settings** → **Devices & Services** → **Add Integration**
5. Search for "StreakHub" and follow the setup wizard

## Configuration

StreakHub is configured entirely through the UI (no YAML configuration).

### Adding a Tracker

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "StreakHub"
3. Enter a name for your tracker (e.g., "Sugar", "Cigarettes", "Workout")
4. Optionally set an initial start date (defaults to today)
5. Optionally set a streak goal in days (0 = no goal)
6. Click Submit

Each tracker creates its own device with associated entities.

## Entities

Each tracker creates 6 entities:

### Streak Sensor (`sensor.{name}_streak`)

Shows the number of days since the last event.

| Property | Value |
|----------|-------|
| State | Number of days (integer) |
| State Class | `measurement` |
| Unit | `d` (days) |

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

**Behavior:**
Pressing means "the event happened today":
- Current streak ends (yesterday was the last day without the event)
- New streak starts tomorrow
- Streak sensor shows `0` today

### Goal Number (`number.{name}_goal`)

Editable number entity to set and adjust your streak goal.

| Property | Value |
|----------|-------|
| State | Goal in days (0-999) |
| Unit | `d` (days) |

**Behavior:**
- Set to `0` for no goal (default)
- Set to any value 1-999 to define your target streak length
- Can be changed at any time without affecting current streak

### Days-to-Goal Sensor (`sensor.{name}_days_to_goal`)

Shows how many days remain until your goal is reached, or how many days you've exceeded it.

| Property | Value |
|----------|-------|
| State | Days remaining (integer) or `unknown` |
| State Class | `measurement` |
| Unit | `d` (days) |

**Attributes:**
- `goal`: The configured goal value
- `goal_date`: Expected date of goal achievement (only if goal > 0 and not yet reached)

**Values:**
- Positive (e.g., `30`): 30 days remaining until goal
- `0`: Goal reached today
- Negative (e.g., `-10`): Goal exceeded by 10 days
- `unknown`: No goal set (goal = 0)

### Has-Goal Binary Sensor (`binary_sensor.{name}_has_goal`)

Diagnostic sensor indicating whether a goal is currently set.

| Property | Value |
|----------|-------|
| State | `on` (goal set) or `off` (no goal) |
| Entity Category | `diagnostic` |

**Use Cases:**
- Show/hide goal-related dashboard cards conditionally
- Trigger automations when goal is set or cleared
- Display different UI elements based on goal status

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

### `streakhub.undo_last_event`

Restores the previous streak (for accidental button presses or corrections).

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `entity_id` | string | Yes | Entity ID of a StreakHub sensor |

**Example:**
```yaml
service: streakhub.undo_last_event
target:
  entity_id: sensor.sugar_streak
```

**Use Case:**
If you accidentally pressed the reset button or called `set_streak_start` by mistake, this service restores your previous streak.

**Limitations:**
- Only one undo per event (cannot undo twice in a row)
- Only works if there is a previous streak in history

## Companion Card

For the best dashboard experience, check out the [StreakHub Card](https://github.com/moerk-o/streakhub-card) - a custom Lovelace card with visual editor that displays your streaks with trophy icons, rank indicators, and a quick reset flow.

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

## License

MIT — see [LICENSE](LICENSE).

## Acknowledgments

- Development assisted by [Claude](https://claude.ai/) (Anthropic)

---

⭐ **Like StreakHub?** Instead of buying me a coffee, give the project a star on GitHub!
