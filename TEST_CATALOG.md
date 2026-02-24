# Test-Katalog: StreakHub Integration

**Version:** 1.1.0
**Stand:** Februar 2026

---

## Übersicht

Dieser Katalog listet alle Tests für die StreakHub Integration auf. Er dient als Übersicht und Checkliste für die Testabdeckung.

**Für allgemeine Test-Richtlinien siehe:** [TESTING_GUIDE.md](TESTING_GUIDE.md)

## Qualitätsziele

| Metrik | Ziel |
|--------|------|
| Test-Coverage (Kernlogik) | **100%** |
| Test-Coverage (Gesamt) | **100%** |
| Alle Edge-Cases abgedeckt | **100%** |

---

## Testkatalog

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
| 2.7 | `test_rank_sensor_icon_rank_2_3` | `mdi:trophy` |
| 2.8 | `test_rank_sensor_icon_rank_0` | `mdi:medal-outline` |
| 2.9 | `test_rank_sensor_attributes` | `top_3` vorhanden (Liste) |
| 2.10 | `test_reset_button_icon` | `mdi:restart` |
| 2.11 | `test_days_to_goal_consistency` | `goal_date` konsistent mit `days_to_goal` |
| 2.12 | `test_days_to_goal_no_goal` | `goal_date` nicht vorhanden bei goal=0 |

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
| 3.10 | `test_config_flow_with_goal` | Goal-Eingabe funktioniert |
| 3.11 | `test_config_flow_goal_default_zero` | Default = 0 |

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

### 3.8 Service undo_last_event (test_undo.py)

| ID | Test | Beschreibung |
|----|------|--------------|
| 8.1 | `test_undo_after_button_press` | Stellt vorherigen Streak wieder her |
| 8.2 | `test_undo_restores_correct_streak_start` | Streak-Start korrekt wiederhergestellt |
| 8.3 | `test_undo_removes_history_entry` | History-Eintrag wird entfernt |
| 8.4 | `test_undo_without_event` | → `ServiceValidationError` (kein Event) |
| 8.5 | `test_undo_with_empty_history` | → `ServiceValidationError` (History leer) |

### 3.9 Goal-Tracking (test_goal.py)

| ID | Test | Beschreibung |
|----|------|--------------|
| 9.1 | `test_goal_number_entity_exists` | Number Entity erstellt |
| 9.2 | `test_goal_number_set_value` | Wert setzen funktioniert |
| 9.3 | `test_days_to_goal_positive` | Positive Werte korrekt |
| 9.4 | `test_days_to_goal_zero` | Wert 0 bei Zielerreichung |
| 9.5 | `test_days_to_goal_negative` | Negative Werte bei Überschreitung |
| 9.6 | `test_days_to_goal_icon_changes` | Icon wechselt bei ≤0 |
| 9.7 | `test_has_goal_binary_sensor_off` | off bei goal=0 |
| 9.8 | `test_has_goal_binary_sensor_on` | on bei goal>0 |

### 3.10 Storage & Persistenz (test_storage.py)

| ID | Test | Beschreibung |
|----|------|--------------|
| 10.1 | `test_storage_empty_creates_tracker` | Neue Installation → Tracker wird angelegt |
| 10.2 | `test_storage_persists_after_reload` | Daten bleiben erhalten |
| 10.3 | `test_storage_multiple_trackers` | Zwei Tracker unabhängig voneinander |
| 10.4 | `test_storage_entry_removal` | Tracker-Daten werden aus Storage entfernt |
| 10.5 | `test_storage_version` | Version = 1 korrekt gesetzt |
| 10.6 | `test_migration_adds_goal_field` | Alte Daten bekommen goal=0 |

### 3.11 Edge Cases (test_edge_cases.py)

| ID | Test | Beschreibung |
|----|------|--------------|
| 11.1 | `test_edge_leap_year_boundary` | Streak über 28./29. Feb hinweg |
| 11.2 | `test_edge_year_boundary` | Streak über 31.12/01.01 hinweg |
| 11.3 | `test_edge_very_long_streak` | 5 Jahre (1826+ Tage) korrekt |
| 11.4 | `test_edge_empty_history` | Nur aktueller Streak, top_3 hat 1 Eintrag |
| 11.5 | `test_edge_exactly_3_history_entries` | top_3 Verdrängungslogik |
| 11.6 | `test_edge_current_streak_zero` | Am Event-Tag, top_3 korrekt sortiert |

### 3.12 Mitternacht-Verhalten (test_midnight.py)

| ID | Test | Beschreibung |
|----|------|--------------|
| 12.1 | `test_midnight_streak_increments` | 23:59 → 00:01: Streak erhöht sich um 1 |
| 12.2 | `test_midnight_timezone_berlin` | Lokale Mitternacht, nicht UTC |
| 12.3 | `test_midnight_dst_spring` | Streak korrekt über Sommerzeitumstellung |
| 12.4 | `test_midnight_dst_fall` | Streak korrekt über Winterzeitumstellung |

### 3.13 Robustheit (test_robustness.py)

| ID | Test | Beschreibung |
|----|------|--------------|
| 13.1 | `test_robust_missing_streak_start` | `streak_start` fehlt → graceful handling |
| 13.2 | `test_robust_invalid_date_format` | `streak_start: "invalid"` → Fehlerbehandlung |
| 13.3 | `test_robust_missing_history` | `history` fehlt → leere Liste annehmen |
| 13.4 | `test_robust_coordinator_no_data` | `coordinator.data is None` → Entities zeigen None |

---

## Zusammenfassung

| Kategorie | Anzahl Tests |
|-----------|--------------|
| Setup & Translations | 4 |
| Entity-Eigenschaften | 12 |
| ConfigFlow | 11 |
| Streak-Berechnung | 6 |
| Ranking-Berechnung | 10 |
| Reset-Button | 7 |
| Service set_streak_start | 14 |
| Service undo_last_event | 5 |
| Goal-Tracking | 8 |
| Storage & Persistenz | 6 |
| Edge Cases | 6 |
| Mitternacht-Verhalten | 4 |
| Robustheit | 4 |
| **Gesamt** | **97 Tests** |

---

## Änderungshistorie

| Version | Datum | Änderung |
|---------|-------|----------|
| 1.1.0 | Februar 2026 | Coverage-Ziele auf 100% angepasst, Goal-Tracking Tests hinzugefügt |
| 1.0.0 | Dezember 2025 | Initiale Version |
