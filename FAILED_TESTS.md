# Test-Status

**Datum:** 28. Dezember 2025
**Gesamt:** 113 Tests | **Bestanden:** 104 | **Fehlgeschlagen:** 0 | **Übersprungen:** 9

---

## Übersprungene Tests (9)

### Config Flow Validierung (2 Tests)

Diese Tests sind übersprungen, weil die Config-Flow-Validierung für Zukunftsdaten noch nicht implementiert ist:

| Test | Datei | Grund |
|------|-------|-------|
| `test_config_flow_date_day_after_tomorrow` | test_config_flow.py | Config Flow Validierung noch nicht implementiert |
| `test_config_flow_date_far_future` | test_config_flow.py | Config Flow Validierung noch nicht implementiert |

### Storage Mocking für History (7 Tests)

Diese Tests benötigen vorpopulierte History-Daten im Storage, was noch nicht implementiert ist:

| Test | Datei | Grund |
|------|-------|-------|
| `test_rank_sensor_icon_rank_2_3` | test_entities.py | Requires storage mocking for pre-populated history |
| `test_rank_sensor_icon_rank_0` | test_entities.py | Requires storage mocking for pre-populated history |
| `test_rank_current_is_rank_2` | test_ranking.py | Requires storage mocking for pre-populated history |
| `test_rank_current_is_rank_3` | test_ranking.py | Requires storage mocking for pre-populated history |
| `test_rank_current_not_in_top_3` | test_ranking.py | Requires storage mocking for pre-populated history |
| `test_rank_tie_breaking` | test_ranking.py | Requires storage mocking for pre-populated history |
| `test_rank_with_many_history_entries` | test_ranking.py | Requires storage mocking for pre-populated history |

---

## Nächste Schritte

1. **Config Flow Validierung:** Implementieren, dass Datumsangaben > morgen im Config Flow abgelehnt werden
2. **Storage Mocking Fixture:** Ein Fixture erstellen, das `hass_storage` mit vorpopulierten History-Daten befüllt
