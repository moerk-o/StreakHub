# Test-Katalog: StreakHub Integration

**Version:** 1.2.0
**Stand:** November 2026

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
| 1.1 | `test_setup_component_minimal` | Setup funktioniert mit minimaler Config |
| 1.2 | `test_config_entry_setup_creates_entities` | Entities werden erstellt |
| 1.3 | `test_entity_ids_follow_pattern` | `sensor.{name}_streak`, `sensor.{name}_rank`, etc. |
| 1.4 | `test_config_entry_unload` | Integration kann entladen werden |
| 1.5 | `test_config_entry_remove_cleans_up_entities` | Entities werden beim Entfernen gelöscht |
| 1.6 | `test_setup_without_initial_date_starts_today` | Ohne Startdatum beginnt der Streak heute |
| 1.7 | `test_device_reports_integration_version` | Gerät zeigt die Version aus der `manifest.json` |

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
| 3.12 | `test_config_flow_default_date_uses_local_day` | Vorgabe "heute" folgt der HA-Zeitzone, nicht der Systemuhr |
| 3.13 | `test_config_flow_tomorrow_uses_local_day` | Grenze "morgen" folgt der HA-Zeitzone |

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

### 3.7 Services (test_service.py)

**Service: set_streak_start**

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

**Service: undo_last_event**

| ID | Test | Beschreibung |
|----|------|--------------|
| 7.15 | `test_undo_after_button_press` | Stellt vorherigen Streak wieder her |
| 7.16 | `test_undo_after_set_streak_start` | Undo funktioniert nach set_streak_start |
| 7.17 | `test_undo_not_possible_no_recent_event` | → `ServiceValidationError` (kein Event) |
| 7.18 | `test_undo_not_possible_twice` | → `ServiceValidationError` (zweimal undo) |
| 7.19 | `test_undo_with_existing_history` | History wird korrekt wiederhergestellt |
| 7.20 | `test_undo_on_rank_sensor` | → Fehler (nicht erlaubt) |
| 7.21 | `test_undo_on_reset_button` | → Fehler (nicht erlaubt) |

**Beide Services**

| ID | Test | Beschreibung |
|----|------|--------------|
| 7.22 | `test_service_on_entity_of_other_integration` | Entity einer anderen Integration wird übersprungen |
| 7.23 | `test_service_on_unloaded_tracker` | Entity eines entladenen Trackers wird übersprungen, kein Fehler |

### 3.8 Goal-Tracking (test_goal.py)

| ID | Test | Beschreibung |
|----|------|--------------|
| 8.1 | `test_goal_number_entity_exists` | Number Entity erstellt |
| 8.2 | `test_goal_number_set_value` | Wert setzen funktioniert |
| 8.3 | `test_days_to_goal_positive` | Positive Werte korrekt |
| 8.4 | `test_days_to_goal_zero` | Wert 0 bei Zielerreichung |
| 8.5 | `test_days_to_goal_negative` | Negative Werte bei Überschreitung |
| 8.6 | `test_days_to_goal_icon_changes` | Icon wechselt bei ≤0 |
| 8.7 | `test_has_goal_binary_sensor_off` | off bei goal=0 |
| 8.8 | `test_has_goal_binary_sensor_on` | on bei goal>0 |

### 3.9 Storage & Persistenz (test_storage.py)

| ID | Test | Beschreibung |
|----|------|--------------|
| 9.1 | `test_storage_empty_creates_tracker` | Neue Installation → Tracker wird angelegt |
| 9.2 | `test_storage_persists_after_reload` | Daten bleiben erhalten |
| 9.3 | `test_storage_multiple_trackers` | Zwei Tracker unabhängig voneinander |
| 9.4 | `test_storage_entry_removal` | Tracker-Daten werden aus Storage entfernt |
| 9.5 | `test_storage_version` | Version = 1 korrekt gesetzt |
| 9.6 | `test_migration_adds_goal_field` | Alte Daten bekommen goal=0 |
| 9.7 | `test_storage_remove_tracker_without_data` | Entfernen aus leerem Storage ändert nichts |

### 3.10 Edge Cases (test_edge_cases.py)

| ID | Test | Beschreibung |
|----|------|--------------|
| 10.1 | `test_edge_leap_year_boundary` | Streak über 28./29. Feb hinweg |
| 10.2 | `test_edge_year_boundary` | Streak über 31.12/01.01 hinweg |
| 10.3 | `test_edge_very_long_streak` | 5 Jahre (1826+ Tage) korrekt |
| 10.4 | `test_edge_empty_history` | Nur aktueller Streak, top_3 hat 1 Eintrag |
| 10.5 | `test_edge_exactly_3_history_entries` | top_3 Verdrängungslogik |
| 10.6 | `test_edge_current_streak_zero` | Am Event-Tag, top_3 korrekt sortiert |
| 10.7 | `test_edge_multiple_same_day_events` | Mehrere Events am selben Tag |

### 3.11 Mitternacht-Verhalten (test_midnight.py)

| ID | Test | Beschreibung |
|----|------|--------------|
| 11.1 | `test_midnight_streak_increments` | 23:59 → 00:01: Streak erhöht sich um 1 |
| 11.2 | `test_midnight_timezone_berlin` | Lokale Mitternacht, nicht UTC |
| 11.3 | `test_midnight_dst_spring` | Streak korrekt über Sommerzeitumstellung |
| 11.4 | `test_midnight_dst_fall` | Streak korrekt über Winterzeitumstellung |

### 3.12 Robustheit (test_robustness.py)

| ID | Test | Beschreibung |
|----|------|--------------|
| 12.1 | `test_robust_missing_streak_start` | `streak_start` fehlt → graceful handling |
| 12.2 | `test_robust_invalid_date_format` | `streak_start: "invalid"` → Fehlerbehandlung |
| 12.3 | `test_robust_missing_history` | `history` fehlt → leere Liste annehmen |
| 12.4 | `test_robust_coordinator_no_data` | `coordinator.data is None` → Sensor `unknown`, Binary Sensor `off`, Ziel 0 |
| 12.5 | `test_robust_refresh_without_tracker_data` | Leerer Storage / fehlender Tracker → Update schlägt fehl, Entities `unavailable` (2 Fälle) |
| 12.6 | `test_robust_actions_without_loaded_data` | Ohne geladene Daten ändern Event, Startdatum, Ziel und Undo nichts |

### 3.13 Logik, Unit-Tests ohne Home Assistant (test_logic.py)

| ID | Test | Beschreibung |
|----|------|--------------|
| 13.1 | `test_streak_on_start_day` | Am Starttag ist der Streak 1 |
| 13.2 | `test_streak_after_multiple_days` | Tage werden korrekt gezählt |
| 13.3 | `test_streak_on_event_day` | Am Event-Tag (vor `streak_start`) ist der Streak 0 |
| 13.4 | `test_streak_long_period` | Lange Zeiträume korrekt |
| 13.5 | `test_streak_same_day_as_start` | `streak_start` = heute |
| 13.6 | `test_single_current_streak` | Top 3 nur mit aktuellem Streak |
| 13.7 | `test_current_streak_is_record` | Aktueller Streak länger als alle History-Einträge |
| 13.8 | `test_current_streak_not_in_top_3` | Aktueller Streak zu kurz für Top 3 |
| 13.9 | `test_tie_breaking_newer_wins` | Bei Gleichstand gewinnt der neuere Streak |
| 13.10 | `test_fewer_than_3_streaks` | Top 3 mit weniger als 3 Streaks |
| 13.11 | `test_zero_day_current_streak` | Aktueller Streak 0 (Event-Tag) |
| 13.12 | `test_rank_1` | Rang 1 |
| 13.13 | `test_rank_2` | Rang 2 |
| 13.14 | `test_rank_3` | Rang 3 |
| 13.15 | `test_not_in_top_3` | Nicht in Top 3 → Rang 0 |
| 13.16 | `test_normal_button_press` | Event beendet Streak und startet neuen |
| 13.17 | `test_button_press_on_same_day_as_start` | Event am Starttag ergibt 0-Tage-Streak |
| 13.18 | `test_consecutive_button_presses` | Events an zwei aufeinanderfolgenden Tagen |
| 13.19 | `test_does_not_mutate_input` | Eingabedaten bleiben unverändert |
| 13.20 | `test_valid_date` | Gültiges Datum → kein Fehler |
| 13.21 | `test_date_in_future` | Datum in der Zukunft → Fehler-Key |
| 13.22 | `test_date_tomorrow_is_valid` | Heute + 1 ist gültig (Event war heute) |
| 13.23 | `test_date_before_streak_start` | Datum vor Streak-Start → Fehler-Key |
| 13.24 | `test_date_equal_to_streak_start` | Datum = Streak-Start → Fehler-Key |
| 13.25 | `test_set_streak_start` | Neuer Streak-Start erzeugt korrekten History-Eintrag |
| 13.26 | `test_create_initial_tracker_data` | Struktur der initialen Tracker-Daten |
| 13.27 | `test_create_initial_storage_data` | Struktur der initialen Storage-Daten |
| 13.28 | `test_leap_year_streak` | Streak über Schaltjahr-Grenze |
| 13.29 | `test_year_boundary_streak` | Streak über Jahreswechsel |
| 13.30 | `test_very_long_streak` | Sehr langer Streak |
| 13.31 | `test_top_3_with_many_history_entries` | Top 3 aus vielen History-Einträgen |
| 13.32 | `test_restores_previous_streak` | Undo stellt den beendeten Streak wieder her |
| 13.33 | `test_not_possible_without_recent_event` | Undo ohne Event → nicht möglich |
| 13.34 | `test_not_possible_with_empty_history` | Undo mit leerer History → nicht möglich |
| 13.35 | `test_days_remaining` | Verbleibende Tage bis zum Ziel |
| 13.36 | `test_goal_reached` | Ziel erreicht → 0 |
| 13.37 | `test_goal_exceeded` | Ziel überschritten → negativ |
| 13.38 | `test_no_goal` | Kein Ziel → kein Wert |

---

## Zusammenfassung

| Kategorie | Anzahl Tests |
|-----------|--------------|
| Setup & Translations | 7 |
| Entity-Eigenschaften | 12 |
| ConfigFlow | 13 |
| Streak-Berechnung | 6 |
| Ranking-Berechnung | 10 |
| Reset-Button | 7 |
| Services (set_streak_start + undo) | 23 |
| Goal-Tracking | 8 |
| Storage & Persistenz | 7 |
| Edge Cases | 7 |
| Mitternacht-Verhalten | 4 |
| Robustheit | 6 |
| Logik (Unit-Tests) | 38 |
| **Gesamt** | **148 Tests** (149 Läufe, 12.5 mit 2 Fällen) |

---

## Änderungshistorie

| Version | Datum | Änderung |
|---------|-------|----------|
| 1.2.0 | November 2026 | Tests für 100 % Coverage ergänzt (1.6, 7.22–7.23, 9.7, 12.5–12.6), Regressionstests für Geräteversion (1.7) und Zeitzone im Config Flow (3.12–3.13), 12.4 prüft jetzt die Entity-Zustände, Logik-Tests (3.13) aufgenommen |
| 1.1.0 | Februar 2026 | Coverage-Ziele auf 100% angepasst, Goal-Tracking Tests hinzugefügt |
| 1.0.0 | Dezember 2025 | Initiale Version |
