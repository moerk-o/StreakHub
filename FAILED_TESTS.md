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

**Aktueller Fehler:** `homeassistant.config_entries.OperationNotAllowed`
```
The config entry 'Tracker B' (streakhub) with entry_id '...' cannot be set up
because it is in state ConfigEntryState.LOADED, but needs to be in the
ConfigEntryState.NOT_LOADED state
```

**Root Cause Analyse:**
Der Test ist **FALSCH geschrieben** - er folgt nicht dem korrekten Home-Assistant-Verhalten.

**Home-Assistant-Verhalten (setup.py Zeilen 458-473):**
Wenn `async_setup(entry1)` aufgerufen wird und die Domain noch nicht geladen ist:
1. Home Assistant ruft `async_setup_component(domain)` auf
2. `async_setup_component` lädt **ALLE** Config Entries dieser Domain
3. Also werden Entry 1 **und** Entry 2 automatisch geladen
4. Der anschließende Aufruf `async_setup(entry2)` schlägt fehl, da Entry 2 bereits LOADED ist

**Test-Ablauf (fehlerhaft):**
```python
entry1.add_to_hass(hass)
entry2.add_to_hass(hass)
await hass.config_entries.async_setup(entry1.entry_id)  # Lädt BEIDE Entries!
await hass.config_entries.async_setup(entry2.entry_id)  # FEHLER: bereits geladen
```

**Korrektes Muster:**
```python
entry1.add_to_hass(hass)
entry2.add_to_hass(hass)
await hass.config_entries.async_setup(entry1.entry_id)  # Lädt beide automatisch
await hass.async_block_till_done()
# KEIN zweiter async_setup-Aufruf nötig!
```

**Fazit:** Der Test muss korrigiert werden - der zweite `async_setup`-Aufruf muss entfernt werden.

---

## Nächste Schritte

Test `test_storage_multiple_trackers` benötigt Korrektur: Den zweiten `async_setup(entry2)` Aufruf entfernen.
