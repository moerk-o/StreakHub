# Testkonzept: StreakHub Integration

**Version:** 1.0.0
**Datum:** 28. Dezember 2025
**Status:** Entwurf

---

## 1. Übersicht

Dieses Dokument beschreibt das Testkonzept für die StreakHub Home Assistant Integration. Es definiert die Testinfrastruktur, Teststrategien und den vollständigen Testkatalog.

### 1.1 Ziele

- Sicherstellung der korrekten Funktionalität aller Komponenten
- Abdeckung aller Edge-Cases gemäß konzept.md
- Regressionssicherheit bei Änderungen
- CI-fähige, automatisierte Tests

### 1.2 Testpyramide

```
                    ┌─────────────────────┐
                    │   E2E-Tests         │  (Optional, manuell)
                    │   (Echte HA-Instanz)│
                    └──────────┬──────────┘
                               │
               ┌───────────────┴───────────────┐
               │     Integration-Tests         │  pytest-homeassistant-custom-component
               │  (ConfigFlow, Entities,       │  + freezegun
               │   Services, Storage)          │
               └───────────────┬───────────────┘
                               │
    ┌──────────────────────────┴──────────────────────────┐
    │              Unit-Tests (Pure Logic)                │  pytest (bereits vorhanden)
    │  (calculate_streak, process_event, Top3, etc.)      │
    └─────────────────────────────────────────────────────┘
```

---

## 2. Testinfrastruktur

### 2.1 Verzeichnisstruktur

```
streakhub/
├── custom_components/
│   └── streakhub/                    # Produktiv-Code
│       ├── __init__.py
│       ├── logic.py
│       ├── coordinator.py
│       ├── sensor.py
│       ├── button.py
│       ├── config_flow.py
│       └── ...
├── tests/
│   ├── conftest.py                   # Fixtures + Plugin-Setup
│   ├── custom_components/            # Kopie für pytest-Plugin (siehe 2.5)
│   │   └── streakhub/               # Muss mit Produktiv-Code synchron sein!
│   ├── test_logic.py                 # Unit-Tests (bereits vorhanden)
│   ├── test_setup.py                 # Setup & Translations
│   ├── test_entities.py              # Entity-Eigenschaften
│   ├── test_config_flow.py           # ConfigFlow-Validierung
│   ├── test_streak_calculation.py    # Streak-Berechnung mit freezegun
│   ├── test_ranking.py               # Ranking-Berechnung
│   ├── test_reset_button.py          # Reset-Button Funktionalität
│   ├── test_service.py               # Service set_streak_start
│   ├── test_storage.py               # Storage & Persistenz
│   ├── test_edge_cases.py            # Edge Cases
│   ├── test_midnight.py              # Mitternacht-Verhalten (TZ-aware)
│   └── test_robustness.py            # Negative Tests / Robustheit
├── requirements-test.txt             # Test-Dependencies
└── pyproject.toml                    # Pytest-Konfiguration
```

### 2.2 Dependencies (requirements-test.txt)

```
pytest==8.3.4
pytest-asyncio==0.24.0
pytest-cov==6.0.0
pytest-homeassistant-custom-component==0.13.205
freezegun==1.5.1
ruff==0.8.6
```

### 2.3 Pytest-Konfiguration (pyproject.toml)

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
asyncio_mode = "auto"
filterwarnings = [
    "ignore::DeprecationWarning",
]
```

### 2.5 Synchronisation: tests/custom_components/

> **WICHTIG:** Das pytest-homeassistant-custom-component Plugin lädt die Integration
> aus `tests/custom_components/`, NICHT aus `custom_components/`!

Nach jeder Änderung am Produktiv-Code muss die Kopie aktualisiert werden:

```bash
# Gesamtes Verzeichnis synchronisieren
cp -r custom_components/streakhub/* tests/custom_components/streakhub/

# Oder einzelne Datei nach Änderung
cp custom_components/streakhub/config_flow.py tests/custom_components/streakhub/
```

**Fehlerquelle:** Wenn Tests fehlschlagen obwohl der Produktiv-Code korrekt ist,
prüfen ob `tests/custom_components/streakhub/` aktuell ist!

### 2.4 conftest.py Struktur

```python
"""Common test fixtures for StreakHub integration tests."""
import pytest
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Use pytest-homeassistant-custom-component plugin
pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading of custom integrations in Home Assistant."""
    return enable_custom_integrations


# =============================================================================
# Config Entry Fixtures
# =============================================================================

@pytest.fixture
def basic_config_entry():
    """Create a basic config entry for testing."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        domain="streakhub",
        data={
            "name": "Zucker",
            "initial_date": "2025-01-01",
        },
        unique_id="zucker",
        version=1,
    )


@pytest.fixture
def config_entry_without_date():
    """Create a config entry without initial_date (should default to today)."""
    ...


@pytest.fixture
def config_entry_with_history():
    """Create a config entry with pre-existing history data."""
    ...


# =============================================================================
# Edge Case Fixtures
# =============================================================================

@pytest.fixture
def config_entry_leap_year():
    """Config entry starting on Feb 29 (leap year)."""
    ...


@pytest.fixture
def config_entry_year_boundary():
    """Config entry crossing year boundary."""
    ...
```

---

## 3. Testkatalog

### 3.1 Setup & Translations (test_setup.py)

| ID | Test | Beschreibung |
|----|------|--------------|
| 1.1 | `test_integration_loads` | Import funktioniert, Domain = "streakhub" |
| 1.2 | `test_entity_ids_correct` | `sensor.{name}_streak`, `sensor.{name}_rank`, `button.{name}_reset` |
| 1.3 | `test_translations_en` | Friendly Names EN: "Streak", "Rank", "Reset" |
| 1.4 | `test_translations_de` | Friendly Names DE: "Serie", "Platzierung", "Zurücksetzen" |

### 3.2 Entity-Eigenschaften (test_entities.py)

| ID | Test | Beschreibung |
|----|------|--------------|
| 2.1 | `test_streak_sensor_state_class` | `SensorStateClass.MEASUREMENT` |
| 2.2 | `test_streak_sensor_unit` | `d` (Tage) |
| 2.3 | `test_streak_sensor_icon` | `mdi:counter` |
| 2.4 | `test_streak_sensor_attributes` | `streak_start` vorhanden (ISO 8601) |
| 2.5 | `test_rank_sensor_state_class` | `None` (kein Measurement) |
| 2.6 | `test_rank_sensor_icon_rank_1` | `mdi:trophy` |
| 2.7 | `test_rank_sensor_icon_rank_2_3` | `mdi:medal-outline` |
| 2.8 | `test_rank_sensor_icon_rank_0` | `mdi:trophy-outline` |
| 2.9 | `test_rank_sensor_attributes` | `top_3` vorhanden (Liste) |
| 2.10 | `test_reset_button_icon` | `mdi:restart` |

### 3.3 ConfigFlow (test_config_flow.py)

| ID | Test | Beschreibung |
|----|------|--------------|
| 3.1 | `test_config_flow_name_required` | Ohne Name → Fehler |
| 3.2 | `test_config_flow_date_optional` | Ohne Datum → Default heute |
| 3.3 | `test_config_flow_date_in_past` | Erlaubt ✓ |
| 3.4 | `test_config_flow_date_today` | Erlaubt ✓ |
| 3.5 | `test_config_flow_date_tomorrow` | Erlaubt ✓ (heute+1) |
| 3.6 | `test_config_flow_date_day_after_tomorrow` | Abgelehnt (heute+2) |
| 3.7 | `test_config_flow_date_far_future` | Abgelehnt |
| 3.8 | `test_config_flow_duplicate_name` | Abgelehnt → "already_configured" |
| 3.9 | `test_config_flow_unique_id_generation` | `slugify(name)` korrekt |

### 3.4 Streak-Berechnung (test_streak_calculation.py)

| ID | Test | Beschreibung |
|----|------|--------------|
| 4.1 | `test_streak_day_1` | Am Starttag ist Streak = 1 |
| 4.2 | `test_streak_day_5` | Nach 5 Tagen ist Streak = 5 |
| 4.3 | `test_streak_event_day_is_zero` | Am Reset-Tag ist Streak = 0 |
| 4.4 | `test_streak_across_year_boundary` | 30.12 → 02.01 = 4 Tage |
| 4.5 | `test_streak_across_leap_year` | 28.02.2024 → 01.03.2024 = 3 Tage |
| 4.6 | `test_streak_very_long` | 1000+ Tage korrekt |

### 3.5 Ranking-Berechnung (test_ranking.py)

| ID | Test | Beschreibung |
|----|------|--------------|
| 5.1 | `test_rank_first_streak_is_rank_1` | Neue Integration, kein History → Rang 1 |
| 5.2 | `test_rank_current_is_record` | Aktueller Streak länger als alle History |
| 5.3 | `test_rank_current_is_rank_2` | Aktueller Streak ist zweitlängster |
| 5.4 | `test_rank_current_is_rank_3` | Aktueller Streak ist drittlängster |
| 5.5 | `test_rank_current_not_in_top_3` | Aktueller Streak nicht in Top 3 → Rang 0 |
| 5.6 | `test_rank_tie_breaking` | Bei Gleichstand gewinnt neuerer Streak |
| 5.7 | `test_rank_fewer_than_3_streaks` | `top_3` enthält nur vorhandene Einträge |
| 5.8 | `test_rank_updated_after_reset` | Nach Button-Druck korrekte Neuberechnung |
| 5.9 | `test_rank_updated_after_service` | Nach `set_streak_start` korrekte Neuberechnung |
| 5.10 | `test_rank_with_many_history_entries` | 100+ Einträge, Top 3 korrekt selektiert |

### 3.6 Reset-Button (test_reset_button.py)

| ID | Test | Beschreibung |
|----|------|--------------|
| 6.1 | `test_button_press_sets_streak_zero` | Streak wird 0 am Event-Tag |
| 6.2 | `test_button_press_new_streak_tomorrow` | `streak_start` = Event-Tag + 1 |
| 6.3 | `test_button_press_writes_history` | Alter Streak in History (wenn > 0 Tage) |
| 6.4 | `test_button_press_zero_day_streak_not_saved` | Doppel-Klick schreibt keine 0-Tage-Einträge |
| 6.5 | `test_button_press_on_streak_start_day` | 0-Tage-Streak wird nicht gespeichert |
| 6.6 | `test_button_press_updates_top_3` | Attribut enthält neuen History-Eintrag |
| 6.7 | `test_button_press_consecutive_days` | Tag 1 + Tag 2 drücken → nur erster in History |

### 3.7 Service set_streak_start (test_service.py)

| ID | Test | Beschreibung |
|----|------|--------------|
| 7.1 | `test_service_valid_date` | Streak-Start wird geändert, alter Streak in History |
| 7.2 | `test_service_history_correct` | Alter Streak mit korrektem Start/End/Days gespeichert |
| 7.3 | `test_service_date_tomorrow` | Erlaubt (heute+1, Event war heute) |
| 7.4 | `test_service_date_today` | Erlaubt (Event war gestern) |
| 7.5 | `test_service_date_in_past` | Erlaubt (vergessener Event) |
| 7.6 | `test_service_date_day_after_tomorrow` | → `ServiceValidationError` |
| 7.7 | `test_service_date_far_future` | → `ServiceValidationError` |
| 7.8 | `test_service_date_before_streak_start` | → `ServiceValidationError` |
| 7.9 | `test_service_date_equals_streak_start` | → `ServiceValidationError` |
| 7.10 | `test_service_on_streak_sensor` | Funktioniert ✓ |
| 7.11 | `test_service_on_rank_sensor` | → Fehler (nicht erlaubt) |
| 7.12 | `test_service_on_reset_button` | → Fehler (nicht erlaubt) |
| 7.13 | `test_service_on_foreign_entity` | → Fehler (nicht StreakHub) |
| 7.14 | `test_service_zero_day_old_streak` | Wird nicht in History gespeichert |

### 3.8 Storage & Persistenz (test_storage.py)

| ID | Test | Beschreibung |
|----|------|--------------|
| 8.1 | `test_storage_empty_creates_tracker` | Neue Installation → Tracker wird angelegt |
| 8.2 | `test_storage_persists_after_reload` | Daten bleiben erhalten |
| 8.3 | `test_storage_multiple_trackers` | Zwei Tracker unabhängig voneinander |
| 8.4 | `test_storage_entry_removal` | Tracker-Daten werden aus Storage entfernt |
| 8.5 | `test_storage_version` | Version = 1 korrekt gesetzt |

### 3.9 Edge Cases (test_edge_cases.py)

| ID | Test | Beschreibung |
|----|------|--------------|
| 9.1 | `test_edge_leap_year_boundary` | Streak über 28./29. Feb hinweg |
| 9.2 | `test_edge_year_boundary` | Streak über 31.12/01.01 hinweg |
| 9.3 | `test_edge_very_long_streak` | 5 Jahre (1826+ Tage) korrekt |
| 9.4 | `test_edge_empty_history` | Nur aktueller Streak, top_3 hat 1 Eintrag |
| 9.5 | `test_edge_exactly_3_history_entries` | top_3 Verdrängungslogik |
| 9.6 | `test_edge_current_streak_zero` | Am Event-Tag, top_3 korrekt sortiert |

### 3.10 Mitternacht-Verhalten (test_midnight.py)

| ID | Test | Beschreibung |
|----|------|--------------|
| 10.1 | `test_midnight_streak_increments` | 23:59 → 00:01: Streak erhöht sich um 1 |
| 10.2 | `test_midnight_timezone_berlin` | Lokale Mitternacht, nicht UTC |
| 10.3 | `test_midnight_dst_spring` | Streak korrekt über Sommerzeitumstellung |
| 10.4 | `test_midnight_dst_fall` | Streak korrekt über Winterzeitumstellung |

### 3.11 Robustheit (test_robustness.py)

| ID | Test | Beschreibung |
|----|------|--------------|
| 11.1 | `test_robust_missing_streak_start` | `streak_start` fehlt → graceful handling |
| 11.2 | `test_robust_invalid_date_format` | `streak_start: "invalid"` → Fehlerbehandlung |
| 11.3 | `test_robust_missing_history` | `history` fehlt → leere Liste annehmen |
| 11.4 | `test_robust_coordinator_no_data` | `coordinator.data is None` → Entities zeigen None |

---

## 4. Test-Patterns

### 4.1 Basis-Test-Pattern (Integration)

```python
@pytest.mark.asyncio
async def test_example(hass: HomeAssistant, basic_config_entry):
    """Test description."""
    # Arrange: Config Entry hinzufügen
    basic_config_entry.add_to_hass(hass)

    # Act: Setup ausführen
    assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
    await hass.async_block_till_done()

    # Assert: Ergebnis prüfen
    sensor = hass.states.get("sensor.zucker_streak")
    assert sensor is not None
    assert int(sensor.state) == expected_value
```

### 4.2 Time-Travel-Pattern (freezegun)

> **WICHTIG: Immer UTC verwenden!**
>
> Home Assistant's `dt_util.now()` verwendet intern `DEFAULT_TIME_ZONE`, das initial
> auf UTC gesetzt ist. `freezegun` friert zwar `datetime.now()` ein, aber
> `dt_util.now()` kann davon abweichen, wenn verschiedene Zeitzonen verwendet werden.
>
> **Regel:** Alle `freeze_time()` Aufrufe MÜSSEN UTC verwenden (`+00:00` oder `Z`).
> Das `set_utc` Fixture in conftest.py stellt sicher, dass HA ebenfalls UTC nutzt.

```python
@pytest.mark.asyncio
async def test_streak_after_5_days(hass: HomeAssistant, basic_config_entry):
    """Test streak is 5 after 5 days."""
    basic_config_entry.add_to_hass(hass)

    # Freeze time to 5 days after streak start - IMMER UTC verwenden!
    with freeze_time("2025-01-05 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
        await hass.async_block_till_done()

        sensor = hass.states.get("sensor.zucker_streak")
        assert int(sensor.state) == 5
```

### 4.3 Service-Call-Pattern

```python
@pytest.mark.asyncio
async def test_service_call(hass: HomeAssistant, basic_config_entry):
    """Test service call."""
    basic_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
    await hass.async_block_till_done()

    # Call service
    await hass.services.async_call(
        "streakhub",
        "set_streak_start",
        {
            "entity_id": "sensor.zucker_streak",
            "date": "2025-01-15",
        },
        blocking=True,
    )

    # Verify result
    sensor = hass.states.get("sensor.zucker_streak")
    assert sensor.attributes["streak_start"] == "2025-01-15"
```

### 4.4 Error-Expectation-Pattern

```python
@pytest.mark.asyncio
async def test_service_rejects_future_date(hass: HomeAssistant, basic_config_entry):
    """Test service rejects date too far in future."""
    basic_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(basic_config_entry.entry_id)
    await hass.async_block_till_done()

    with freeze_time("2025-01-10 12:00:00+00:00"):  # UTC!
        with pytest.raises(ServiceValidationError) as exc_info:
            await hass.services.async_call(
                "streakhub",
                "set_streak_start",
                {
                    "entity_id": "sensor.zucker_streak",
                    "date": "2025-01-20",  # 10 days in future
                },
                blocking=True,
            )

        assert "date_in_future" in str(exc_info.value)
```

---

## 5. Ausführung

### 5.1 Lokale Ausführung

```bash
# Virtuelle Umgebung erstellen
python -m venv venv
source venv/bin/activate

# Dependencies installieren
pip install -r requirements-test.txt

# Alle Tests ausführen
pytest

# Mit Coverage
pytest --cov=custom_components/streakhub --cov-report=html

# Einzelne Testdatei
pytest tests/test_config_flow.py

# Einzelner Test
pytest tests/test_config_flow.py::test_config_flow_date_tomorrow -v
```

### 5.2 CI-Integration (GitHub Actions)

```yaml
# .github/workflows/tests.yml
name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install -r requirements-test.txt

      - name: Run tests
        run: pytest --cov=custom_components/streakhub

      - name: Upload coverage
        uses: codecov/codecov-action@v4
```

---

## 6. Qualitätsziele

| Metrik | Ziel |
|--------|------|
| Test-Coverage (logic.py) | > 95% |
| Test-Coverage (gesamt) | > 80% |
| Alle Edge-Cases aus konzept.md | 100% |
| CI-Pipeline grün | Pflicht vor Merge |

---

## 7. Zusammenfassung

| Kategorie | Anzahl Tests |
|-----------|--------------|
| Setup & Translations | 4 |
| Entity-Eigenschaften | 10 |
| ConfigFlow | 9 |
| Streak-Berechnung | 6 |
| Ranking-Berechnung | 10 |
| Reset-Button | 7 |
| Service set_streak_start | 14 |
| Storage & Persistenz | 5 |
| Edge Cases | 6 |
| Mitternacht-Verhalten | 4 |
| Robustheit | 4 |
| **Gesamt** | **79 Tests** |

---

## 8. Änderungshistorie

| Version | Datum | Änderung |
|---------|-------|----------|
| 1.0.0 | 28.12.2025 | Initiale Version |
