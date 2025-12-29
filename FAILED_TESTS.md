# Test-Status

**Datum:** 29. Dezember 2025
**Gesamt:** 113 Tests | **Bestanden:** 106 | **Fehlgeschlagen:** 0 | **Übersprungen:** 7

---

## Übersprungene Tests (7)

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

1. **Storage Mocking Fixture:** Ein Fixture erstellen, das `hass_storage` mit vorpopulierten History-Daten befüllt

