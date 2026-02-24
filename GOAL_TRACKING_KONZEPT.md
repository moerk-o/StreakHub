# Goal-Tracking Feature - Implementierungsplan

## Übersicht

Feature Request aus GitHub Issue #1: Möglichkeit ein Streak-Ziel zu setzen und die verbleibenden/überschrittenen Tage zu sehen.

**Branch**: `feature/goal-tracking`

---

## Feature-Spezifikation

### 1. Config Flow Erweiterung

**Neues Feld**: "Streak-Goal (Tage)"
- Typ: Integer
- Default: `0` (kein Ziel)
- Erlaubte Werte: `0` (kein Ziel) oder `1-999` (Ziel in Tagen)
- Optional, wie `initial_date`
- UI: Number Selector mit Min/Max Validierung

### 2. Days-to-Goal Sensor

**Entity**: `sensor.{name}_days_to_goal`
- **Wird immer erstellt** (auch bei goal=0)
- **Berechnung**: `goal - current_streak`
- **Werte**:
  - `unavailable` wenn goal = 0 (kein Ziel gesetzt)
  - Positiv (z.B. `30`): "Noch 30 Tage bis Ziel"
  - `0`: "Ziel heute erreicht"
  - Negativ (z.B. `-20`): "20 Tage über Ziel hinaus"
- **Unit**: Tage (`d`)
- **State Class**: Measurement
- **Icon - 2 Zustände**:
  - Sensor > 0: `mdi:check-decagram-outline` (Ziel nicht erreicht)
  - Sensor ≤ 0: `mdi:check-decagram` (Ziel erreicht/übertroffen)

### 3. Has-Goal Binary Sensor (Diagnose)

**Entity**: `binary_sensor.{name}_has_goal`
- **State**:
  - `on`: goal > 0 (Ziel ist aktiv)
  - `off`: goal = 0 (kein Ziel gesetzt)
- **Entity Category**: `diagnostic` (nicht standardmäßig sichtbar)
- **Icon**: `mdi:flag-checkered`
- **Nutzen**:
  - Conditional Cards im Dashboard
  - Automationen
  - Companion Card Steuerung

### 4. Attribute

Beide neuen Sensoren bekommen optionale Attribute:
- `goal`: Der gesetzte Zielwert (0 = kein Ziel)

---

## Technische Implementierung

### Dateien die geändert werden müssen

#### 1. `custom_components/streakhub/const.py`
**Änderungen**:
- Neue Konstante: `CONF_GOAL: Final = "goal"`
- Neue Konstante: `ENTITY_DAYS_TO_GOAL: Final = "days_to_goal"`
- Neue Konstante: `ENTITY_HAS_GOAL: Final = "has_goal"`
- Icons: `ICON_GOAL_NOT_REACHED = "mdi:check-decagram-outline"`
- Icons: `ICON_GOAL_REACHED = "mdi:check-decagram"`
- Icons: `ICON_HAS_GOAL = "mdi:flag-checkered"`

#### 2. `custom_components/streakhub/logic.py`
**Änderungen**:
- `TrackerData` TypedDict erweitern:
  ```python
  class TrackerData(TypedDict):
      streak_start: str
      history: list[HistoryEntry]
      last_event_date: str | None
      goal: int  # NEU: 0 = kein Ziel, >0 = Ziel in Tagen
  ```
- `create_initial_tracker_data()` erweitern:
  - Parameter `goal: int = 0` hinzufügen
  - In returned dict `goal` setzen
- Neue Funktion `calculate_days_to_goal()`:
  ```python
  def calculate_days_to_goal(current_streak: int, goal: int) -> int | None:
      """Calculate days remaining to goal (negative if exceeded)."""
      if goal == 0:
          return None
      return goal - current_streak
  ```

#### 3. `custom_components/streakhub/config_flow.py`
**Änderungen**:
- Import: `CONF_GOAL` aus `const.py`
- Schema in `async_step_user()` erweitern:
  ```python
  vol.Optional(CONF_GOAL, default=0): selector.NumberSelector(
      selector.NumberSelectorConfig(
          min=0,
          max=999,
          step=1,
          mode=selector.NumberSelectorMode.BOX,
          unit_of_measurement="days",
      )
  )
  ```
- Validierung: Goal muss 0 oder positive Zahl sein
- Daten in `async_create_entry()` speichern

#### 4. `custom_components/streakhub/coordinator.py`
**Änderungen**:
- `async_initialize_tracker()`: Goal aus config lesen und an `create_initial_tracker_data()` übergeben
- Bei bestehendem Tracker: Migration für `goal` Feld (falls nicht vorhanden, default = 0)

#### 5. `custom_components/streakhub/__init__.py`
**Änderungen**:
- `CONF_GOAL` aus entry.data lesen
- An Coordinator übergeben

#### 6. `custom_components/streakhub/sensor.py`
**Änderungen**:
- Import neuer Konstanten
- Neue Funktion `_get_days_to_goal_value()`:
  ```python
  def _get_days_to_goal_value(coordinator: StreakHubCoordinator, today: date) -> int | None:
      goal = coordinator.data.get("goal", 0)
      if goal == 0:
          return None
      current_streak = _get_streak_value(coordinator, today)
      return goal - current_streak
  ```
- Neue Funktion `_get_days_to_goal_icon()`:
  ```python
  def _get_days_to_goal_icon(coordinator: StreakHubCoordinator, today: date) -> str:
      days_to_goal = _get_days_to_goal_value(coordinator, today)
      if days_to_goal is None or days_to_goal > 0:
          return ICON_GOAL_NOT_REACHED
      return ICON_GOAL_REACHED
  ```
- Neue Funktion `_get_days_to_goal_attributes()`:
  ```python
  def _get_days_to_goal_attributes(coordinator: StreakHubCoordinator, today: date) -> dict[str, Any]:
      return {"goal": coordinator.data.get("goal", 0)}
  ```
- Neue Sensor Description in `SENSOR_DESCRIPTIONS`:
  ```python
  StreakHubSensorEntityDescription(
      key=ENTITY_DAYS_TO_GOAL,
      translation_key=ENTITY_DAYS_TO_GOAL,
      state_class=SensorStateClass.MEASUREMENT,
      native_unit_of_measurement=UNIT_DAYS,
      icon_fn=_get_days_to_goal_icon,
      value_fn=_get_days_to_goal_value,
      extra_state_attributes_fn=_get_days_to_goal_attributes,
  )
  ```

#### 7. `custom_components/streakhub/binary_sensor.py` (NEU)
**Neue Datei erstellen**:
- Ähnlich wie `sensor.py` und `button.py`
- Binary Sensor Entity für "Has Goal"
- `BinarySensorEntity` subclass
- Entity Category: `diagnostic`
- State: `goal > 0`
- Icon: `mdi:flag-checkered`

Struktur:
```python
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorEntityDescription
from homeassistant.const import EntityCategory

@dataclass(frozen=True, kw_only=True)
class StreakHubBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Description for StreakHub binary sensor."""
    is_on_fn: Callable[[StreakHubCoordinator], bool]

def _get_has_goal_state(coordinator: StreakHubCoordinator) -> bool:
    goal = coordinator.data.get("goal", 0)
    return goal > 0

BINARY_SENSOR_DESCRIPTIONS: tuple[StreakHubBinarySensorEntityDescription, ...] = (
    StreakHubBinarySensorEntityDescription(
        key=ENTITY_HAS_GOAL,
        translation_key=ENTITY_HAS_GOAL,
        icon=ICON_HAS_GOAL,
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=_get_has_goal_state,
    ),
)

class StreakHubBinarySensor(CoordinatorEntity[StreakHubCoordinator], BinarySensorEntity):
    # Implementation analog zu StreakHubSensor
    @property
    def is_on(self) -> bool:
        return self.entity_description.is_on_fn(self.coordinator)
```

#### 8. `custom_components/streakhub/__init__.py` (Ergänzung)
**Änderungen**:
- Platform `binary_sensor` zu `PLATFORMS` hinzufügen

#### 9. `custom_components/streakhub/translations/en.json`
**Änderungen**:
```json
{
  "config": {
    "step": {
      "user": {
        "data": {
          "goal": "Streak Goal (days, 0 = no goal)"
        },
        "description": "Set up a new StreakHub tracker. The goal is optional - set to 0 if you don't want to track a specific target."
      }
    },
    "error": {
      "invalid_goal": "Goal must be 0 (no goal) or a positive number."
    }
  },
  "entity": {
    "sensor": {
      "days_to_goal": {
        "name": "Days to Goal"
      }
    },
    "binary_sensor": {
      "has_goal": {
        "name": "Has Goal"
      }
    }
  }
}
```

#### 10. `custom_components/streakhub/translations/de.json`
**Änderungen**:
```json
{
  "config": {
    "step": {
      "user": {
        "data": {
          "goal": "Streak-Ziel (Tage, 0 = kein Ziel)"
        },
        "description": "Richte einen neuen StreakHub-Tracker ein. Das Ziel ist optional - setze es auf 0, wenn du kein bestimmtes Ziel tracken möchtest."
      }
    },
    "error": {
      "invalid_goal": "Ziel muss 0 (kein Ziel) oder eine positive Zahl sein."
    }
  },
  "entity": {
    "sensor": {
      "days_to_goal": {
        "name": "Tage bis Ziel"
      }
    },
    "binary_sensor": {
      "has_goal": {
        "name": "Hat Ziel"
      }
    }
  }
}
```

---

## Migration & Backwards Compatibility

### Bestehende Tracker
- Tracker ohne `goal` Feld bekommen automatisch `goal = 0`
- Migration in `coordinator.py` bei `async_load_data()`:
  ```python
  if "goal" not in tracker_data:
      tracker_data["goal"] = 0
  ```
- Keine Storage-Version-Änderung nötig (abwärtskompatibel)

### Neue Entities
- Days-to-Goal Sensor: wird automatisch für alle Tracker erstellt
- Has-Goal Binary Sensor: wird automatisch für alle Tracker erstellt
- Bei bestehenden Trackern initial `unavailable` bzw. `off`

---

## Testing-Strategie

### Unit Tests

#### `tests/test_logic.py`
- Test: `test_calculate_days_to_goal_no_goal()` - goal=0 → None
- Test: `test_calculate_days_to_goal_positive()` - goal=100, streak=30 → 70
- Test: `test_calculate_days_to_goal_zero()` - goal=100, streak=100 → 0
- Test: `test_calculate_days_to_goal_negative()` - goal=100, streak=120 → -20
- Test: `test_create_initial_tracker_data_with_goal()` - goal wird gespeichert

#### `tests/test_config_flow.py`
- Test: `test_config_flow_with_goal()` - Goal-Eingabe funktioniert
- Test: `test_config_flow_goal_validation()` - Negative Werte werden abgelehnt
- Test: `test_config_flow_goal_default_zero()` - Default = 0

#### `tests/test_entities.py`
- Test: `test_days_to_goal_sensor_no_goal()` - unavailable bei goal=0
- Test: `test_days_to_goal_sensor_positive()` - Positive Werte
- Test: `test_days_to_goal_sensor_goal_reached()` - Wert 0
- Test: `test_days_to_goal_sensor_over_goal()` - Negative Werte
- Test: `test_days_to_goal_icon_changes()` - Icon wechselt bei ≤0
- Test: `test_has_goal_binary_sensor_off()` - off bei goal=0
- Test: `test_has_goal_binary_sensor_on()` - on bei goal>0

#### `tests/test_storage.py`
- Test: `test_migration_adds_goal_field()` - Alte Daten bekommen goal=0

### Integration Tests

#### Manueller Test-Plan
1. **Neuer Tracker mit Goal**:
   - Tracker anlegen mit goal=100
   - Prüfen: 3 Sensoren + Binary Sensor erstellt
   - Days-to-Goal zeigt korrekten Wert
   - Has-Goal ist `on`
   - Icon ist `outline`

2. **Neuer Tracker ohne Goal**:
   - Tracker anlegen mit goal=0 (oder leer)
   - Days-to-Goal zeigt `unavailable`
   - Has-Goal ist `off`

3. **Bestehender Tracker**:
   - HA neu starten
   - Prüfen: Neue Sensoren erscheinen
   - Initial `unavailable` und `off`

4. **Goal Erreichen**:
   - Tracker mit goal=10 auf Tag 10 bringen
   - Days-to-Goal = 0
   - Icon wechselt zu `solid`

5. **Goal Überschreiten**:
   - Weiter auf Tag 15
   - Days-to-Goal = -5
   - Icon bleibt `solid`

6. **Dashboard Conditional Card**:
   - Card nur zeigen wenn has_goal=on
   - Funktioniert wie erwartet

---

## Verifikation (nach Implementierung)

### Checklist
- [ ] Config Flow zeigt Goal-Feld
- [ ] Goal-Validierung funktioniert (0 oder 1-999)
- [ ] Days-to-Goal Sensor wird erstellt
- [ ] Has-Goal Binary Sensor wird erstellt
- [ ] Sensor zeigt `unavailable` bei goal=0
- [ ] Sensor zeigt positive Werte korrekt
- [ ] Sensor zeigt 0 bei Zielerreichung
- [ ] Sensor zeigt negative Werte bei Überschreitung
- [ ] Icon wechselt bei ≤0 zu solid
- [ ] Binary Sensor ist on/off korrekt
- [ ] Attribute `goal` vorhanden
- [ ] Translations DE/EN funktionieren
- [ ] Bestehende Tracker migrieren sauber
- [ ] Alle Unit Tests bestehen
- [ ] Keine Regression bei bestehenden Features

### Test Commands
```bash
# Unit Tests ausführen
pytest tests/ -v

# Spezifische Tests
pytest tests/test_logic.py::test_calculate_days_to_goal_positive -v
pytest tests/test_entities.py -v

# Coverage prüfen
pytest --cov=custom_components/streakhub tests/

# Linting
ruff check custom_components/streakhub/
mypy custom_components/streakhub/
```

---

## Offene Punkte / Später

### Nicht in diesem Feature enthalten:
- ❌ Options Flow (Goal nachträglich editieren)
- ❌ Fortschritts-Prozente
- ❌ Geschätzte Ziel-Datum
- ❌ Notifications bei Zielerreichung
- ❌ Multiple Goals pro Tracker

### Mögliche Erweiterungen:
- Options Flow für nachträgliche Goal-Änderung
- Progress-Bar Sensor (0-100%)
- Attribute `estimated_goal_date`
- Service `set_goal` analog zu `set_streak_start`

---

## Zusammenfassung

**Scope**:
- 1 neues Config-Feld (goal)
- 1 neuer Sensor (days_to_goal)
- 1 neuer Binary Sensor (has_goal)
- Dynamisches Icon für days_to_goal
- Migration für bestehende Tracker
- Tests für alle neuen Features

**Dateien**: 9 geändert, 1 neu
**Geschätzter Aufwand**: Mittel (ca. 3-4h inkl. Tests)
**Breaking Changes**: Keine
**Migration**: Automatisch, abwärtskompatibel
