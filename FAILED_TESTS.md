# Fehlgeschlagene Tests - Analyse

**Datum:** 28. Dezember 2025
**Stand:** Nach Korrektur der 0-day-Tests
**Gesamt:** 113 Tests | **Bestanden:** 103 | **Fehlgeschlagen:** 1 | **Übersprungen:** 9

---

## Durchgeführte Korrekturen

### Korrektur: 0-Tage-Streak-Berechnung (abgeschlossen)
4 Tests erwarteten fälschlich, dass Streaks gespeichert werden, obwohl sie gemäß konzept.md 0 Tage sind:
- ✅ test_button_press_on_streak_start_day → `assert len(history) == 0`
- ✅ test_button_press_consecutive_days → `assert history[0]["days"] == 9`
- ✅ test_service_history_correct → `assert history[0]["days"] == 6`
- ✅ test_service_zero_day_old_streak → `assert len(history) == 0`

### Frühere Korrekturen
- History-Berechnung 10 → 9 Tage (5 Tests)
- UTC-Umstellung (5 Tests)
- test_edge_very_long_streak: 1827 → 1828 Tage
- test_config_flow_name_required: pytest.raises(InvalidData)

---

## Verbleibender 1 fehlgeschlagener Test

### test_storage_multiple_trackers

**Datei:** `tests/test_storage.py:68`

**Fehler:** `homeassistant.exceptions.ServiceNotFound: streakhub.set_streak_start`

**Analyse:**
Der Test verwendet nur den Button-Service (`button.press`), nicht `streakhub.set_streak_start`. Der Fehler deutet auf ein Problem bei der Service-Registrierung hin, wenn mehrere Config Entries geladen werden.

**Test-Ablauf:**
1. Zwei MockConfigEntry erstellen (Tracker A, Tracker B)
2. Beide zu hass hinzufügen
3. Beide async_setup aufrufen
4. Button von Tracker A drücken → **ServiceNotFound**

**Mögliche Ursachen:**
1. Service wird nur beim ersten Config Entry registriert
2. Test-Isolation-Problem
3. Race-Condition bei mehreren async_setup Aufrufen

**Korrektur:** Separat untersuchen - vermutlich Bug in `__init__.py` bei Service-Registrierung.

---

## Nächste Schritte

Test 5 (test_storage_multiple_trackers) benötigt separate Untersuchung der Service-Registrierung.
