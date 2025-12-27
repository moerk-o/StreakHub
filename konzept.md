# Konzept: Home Assistant Integration `streakhub`

**Version:** 0.1.0 (Konzept)
**Datum:** 27. Dezember 2025
**Zielplattform:** Home Assistant Custom Integration
**Entwicklungssprache:** Englisch (Code, Kommentare, Variablen, Commits, Dokumentation)
**Konzeptsprache:** Deutsch (dieses Dokument)
**Übersetzungen:** Englisch (Fallback), Deutsch

---

## 1. Projektübersicht

### 1.1 Zweck

Die `streak_tracker` Integration ermöglicht das Tracken von "Streaks" – also Zeiträumen zwischen wiederholten Ereignissen. Typische Anwendungsfälle:

- **Verzicht-Tracking:** "Tage ohne Zucker", "Tage ohne Zigaretten", "Tage ohne Alkohol"
- **Gewohnheits-Tracking (invertiert):** "Tage seit dem letzten Sport" (niedrig = schlecht)
- **Allgemeines Tracking:** Jede Art von Ereignis, dessen Abstände man messen möchte

Die Integration bietet:

- Beliebig viele unabhängige Tracker
- Aktueller Streak in Tagen
- Platzierung des aktuellen Streaks (Top 3 oder nicht)
- Historische Top 3 mit Gamification-Aspekt (🥇🥈🥉)
- Nachträgliche Korrektur des Streak-Starts

### 1.2 Kernkonzept

Ein **Streak** ist der Zeitraum zwischen zwei Ereignissen. Der Streak zählt die Tage an denen das Ereignis NICHT stattfand.

**Wichtig:** Ein Streak endet erst, wenn ein neuer beginnt. Es gibt keinen Zustand "kein aktiver Streak".

### 1.3 Namenskonvention

- **Domain:** `streakhub`
- **Entity Prefix:** Benutzerdefinierter Name im ConfigFlow (z.B. "Zucker" → `sensor.zucker_*`)

---

## 2. Die Streak-Logik im Detail

Dieses Kapitel erklärt die zentrale Berechnungslogik der Integration. Das korrekte Verständnis ist essentiell für die Implementierung.

### 2.1 Grundprinzip: Was zählt ein Streak?

Ein Streak zählt die **Tage OHNE das Ereignis**. Der Tag an dem das Ereignis stattfindet (= Button wird gedrückt) gehört zu **keinem** Streak.

### 2.2 Beispiel-Timeline

Angenommen wir tracken "Tage ohne Zucker":

```
Legende:
  ✓ = Tag ohne Zucker (zählt zum Streak)
  ✗ = Tag mit Zucker (Event-Tag, zählt NICHT)
  [n] = Streak-Wert an diesem Tag
```

```
01.01: Streak beginnt (streak_start = 01.01)
01.01: ✓ [1] - 1 Tag ohne Zucker
02.01: ✓ [2] - 2 Tage ohne Zucker
03.01: ✓ [3] - 3 Tage ohne Zucker
...
12.01: ✓ [12] - 12 Tage ohne Zucker
13.01: ✓ [13] - 13 Tage ohne Zucker
14.01: ✗ [0] - ZUCKER! Button gedrückt → Streak = 0
15.01: ✓ [1] - 1 Tag ohne Zucker (neuer Streak)
16.01: ✓ [2] - 2 Tage ohne Zucker
```

### 2.3 Was passiert beim Button-Druck?

Wenn der Button am Tag X gedrückt wird:

| Schritt | Beschreibung | Wert |
|---------|--------------|------|
| 1 | Event-Tag (Tag MIT Ereignis) | X |
| 2 | Letzter Tag des alten Streaks | X - 1 |
| 3 | Erster Tag des neuen Streaks | X + 1 |
| 4 | Streak-Wert am Event-Tag | 0 |

**Beispiel:** Button wird am 14.01 gedrückt:
- Event-Tag: 14.01
- Alter Streak endet: 13.01
- Neuer Streak beginnt: 15.01
- Am 14.01 zeigt der Sensor: 0

### 2.4 Berechnung des Streak-Werts

```python
def calculate_streak(streak_start: date, today: date) -> int:
    """Berechnet den aktuellen Streak-Wert."""
    if today < streak_start:
        # Wir sind noch am Event-Tag (vor dem neuen Streak-Start)
        return 0
    
    # Tage seit Streak-Start (inklusive Start-Tag)
    return (today - streak_start).days + 1
```

### 2.5 Edge Case: Button zweimal am selben Tag

Was passiert wenn der Button an zwei aufeinanderfolgenden Tagen gedrückt wird?

```
14.01: ✗ [0] - Button gedrückt
15.01: ✗ [0] - Button erneut gedrückt
16.01: ✓ [1] - 1 Tag ohne Ereignis
```

**Analyse vom zweiten Button-Druck (15.01):**
- Event-Tag: 15.01
- Alter Streak endete: 14.01
- Aber 14.01 war selbst ein Event-Tag!
- Alter Streak-Zeitraum: 15.01 (Start) bis 14.01 (Ende) = **0 Tage**

**Regel:** Streaks mit 0 Tagen werden **nicht** in die History gespeichert.

### 2.6 Edge Case: Button am Tag des Streak-Starts

Was wenn der Button am selben Tag gedrückt wird an dem der Streak gestartet ist?

```
15.01: Streak beginnt (streak_start = 15.01)
15.01: ✗ [0] - Button am selben Tag gedrückt
16.01: ✓ [1] - 1 Tag ohne Ereignis
```

**Analyse:**
- Event-Tag: 15.01
- Alter Streak: 15.01 bis 14.01 = **0 Tage** (negativ → wird zu 0)
- Neuer Streak beginnt: 16.01

**Regel:** Auch hier wird nichts in die History gespeichert.

### 2.7 Zusammenfassung der Button-Logik

```python
def handle_button_press(today: date):
    """Verarbeitet einen Button-Druck."""
    event_day = today  # Tag an dem das Ereignis stattfand
    old_streak_end = event_day - timedelta(days=1)  # Letzter Tag OHNE Ereignis
    new_streak_start = event_day + timedelta(days=1)  # Erster Tag OHNE Ereignis
    
    # Alten Streak berechnen
    old_streak_days = (old_streak_end - streak_start).days + 1
    
    # Nur speichern wenn > 0 Tage
    if old_streak_days > 0:
        history.append({
            "start": streak_start,
            "end": old_streak_end,
            "days": old_streak_days
        })
    
    # Neuen Streak starten
    streak_start = new_streak_start
```

---

## 3. Datenmodell

### 3.1 Persistenz

Die Integration speichert ihre Daten in `.storage/streakhub` als JSON:

```json
{
  "version": 1,
  "data": {
    "trackers": {
      "zucker": {
        "streak_start": "2025-01-15",
        "history": [
          {"start": "2024-11-01", "end": "2024-12-24", "days": 54},
          {"start": "2025-01-01", "end": "2025-01-13", "days": 13},
          {"start": "2024-08-15", "end": "2024-08-22", "days": 8}
        ]
      },
      "sport": {
        "streak_start": "2025-01-20",
        "history": []
      }
    }
  }
}
```

### 3.2 Datenfelder

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `streak_start` | `date` (ISO 8601) | Erster Tag des aktuellen Streaks (erster Tag OHNE Ereignis) |
| `history` | `list[dict]` | Liste aller abgeschlossenen Streaks |
| `history[].start` | `date` (ISO 8601) | Erster Tag des Streaks |
| `history[].end` | `date` (ISO 8601) | Letzter Tag des Streaks |
| `history[].days` | `int` | Dauer in Tagen |

### 3.3 Top 3 Berechnung

#### Sortierung und Gleichstands-Auflösung

Bei der Top-3-Berechnung gilt folgende Sortierregel:

1. **Primär:** Anzahl Tage (absteigend, mehr Tage = besser)
2. **Sekundär:** Startdatum (absteigend, neuer = besser bei Gleichstand)

**Regel:** Bei gleicher Tageszahl gewinnt der **neuere** Streak. Ein neuer Streak mit gleicher Tageszahl verdrängt einen älteren aus der Top-3-Anzeige.

**Beispiel:**
- History enthält: `{start: "2024-01-01", days: 10}` und `{start: "2024-06-01", days: 10}`
- Sortiert: `2024-06-01` kommt vor `2024-01-01` (neuer gewinnt bei Gleichstand)

```python
def calculate_top_3(streak_start: date, history: list, today: date) -> list:
    """Berechnet die Top 3 aller Streaks."""
    current_streak_days = calculate_streak(streak_start, today)

    # Alle Streaks sammeln (History + aktueller)
    all_streaks = []

    # History-Einträge mit Rang-Platzhalter
    for h in history:
        all_streaks.append({
            "rank": 0,  # Wird später gesetzt
            "start": h["start"],
            "end": h["end"],
            "days": h["days"]
        })

    # Aktueller Streak (end = null bedeutet "läuft noch")
    all_streaks.append({
        "rank": 0,
        "start": streak_start.isoformat(),
        "end": None,
        "days": current_streak_days
    })

    # Nach Tagen sortieren (absteigend), bei Gleichstand nach Start (absteigend/neuer zuerst)
    top_3 = sorted(
        all_streaks,
        key=lambda x: (x["days"], x["start"]),
        reverse=True
    )[:3]

    # Ränge setzen
    for i, streak in enumerate(top_3):
        streak["rank"] = i + 1

    return top_3
```

### 3.4 Rang-Berechnung

```python
def calculate_rank(top_3: list) -> int:
    """Ermittelt den Rang des aktuellen Streaks (0 wenn nicht in Top 3)."""
    for streak in top_3:
        if streak["end"] is None:  # Aktueller Streak
            return streak["rank"]
    return 0  # Nicht in Top 3
```

---

## 4. Entities

Die Integration erstellt **3 Entities pro Tracker**.

### 4.1 `streak` – Aktueller Streak

#### Beschreibung

Zeigt die Anzahl der Tage seit dem letzten Ereignis. Am Tag des Ereignisses (Button-Druck) ist der Wert 0.

#### State und Eigenschaften

| Eigenschaft | Wert |
|-------------|------|
| **Entity ID Pattern** | `sensor.{name}_streak` |
| **Device Class** | `None` |
| **State Class** | `measurement` |
| **Unit of Measurement** | `d` (Tage) |
| **Icon** | `mdi:counter` |

| State | Format | Beispiel |
|-------|--------|----------|
| `<Tage>` | Integer | `14` |
| `0` | Integer | Am Event-Tag |

#### Attribute

| Attribut | Typ | Beschreibung |
|----------|-----|--------------|
| `streak_start` | `str` (ISO 8601) | Erster Tag des aktuellen Streaks |

#### Code-Beispiel

```python
class StreakSensor(CoordinatorEntity, SensorEntity):
    _attr_device_class = None
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "d"
    _attr_icon = "mdi:counter"

    @property
    def native_value(self) -> int:
        streak_start = date.fromisoformat(self.coordinator.data["streak_start"])
        today = date.today()
        
        if today < streak_start:
            return 0
        
        return (today - streak_start).days + 1

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "streak_start": self.coordinator.data["streak_start"]
        }
```

---

### 4.2 `rank` – Aktuelle Platzierung

#### Beschreibung

Zeigt die Platzierung des aktuellen Streaks in der All-Time Top 3. Enthält als Attribut die komplette Top 3 für Dashboard-Anzeigen.

#### State und Eigenschaften

| Eigenschaft | Wert |
|-------------|------|
| **Entity ID Pattern** | `sensor.{name}_rank` |
| **Device Class** | `None` |
| **State Class** | `None` |
| **Icon** | Dynamisch basierend auf Rang |

| State | Bedeutung | Icon |
|-------|-----------|------|
| `1` | Aktueller Streak ist Platz 1 (Rekord!) | `mdi:trophy` |
| `2` | Aktueller Streak ist Platz 2 | `mdi:medal-outline` |
| `3` | Aktueller Streak ist Platz 3 | `mdi:medal-outline` |
| `0` | Nicht in Top 3 | `mdi:trophy-outline` |

#### Attribute

| Attribut | Typ | Beschreibung |
|----------|-----|--------------|
| `top_3` | `list[dict]` | Die drei längsten Streaks mit Rang |

**Struktur von `top_3`:**

```yaml
top_3:
  - rank: 1
    start: "2024-11-01"
    end: "2024-12-24"
    days: 54
  - rank: 2
    start: "2025-01-14"
    end: null           # ← Aktueller Streak (läuft noch)
    days: 28
  - rank: 3
    start: "2025-01-01"
    end: "2025-01-13"
    days: 13
```

#### Code-Beispiel

```python
class RankSensor(CoordinatorEntity, SensorEntity):
    _attr_device_class = None
    _attr_state_class = None

    @property
    def native_value(self) -> int:
        top_3 = self._calculate_top_3()
        return self._calculate_rank(top_3)

    @property
    def icon(self) -> str:
        rank = self.native_value
        if rank == 1:
            return "mdi:trophy"
        elif rank in (2, 3):
            return "mdi:medal-outline"
        return "mdi:trophy-outline"

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "top_3": self._calculate_top_3()
        }

    def _calculate_top_3(self) -> list[dict]:
        data = self.coordinator.data
        streak_start = date.fromisoformat(data["streak_start"])
        today = date.today()
        
        # Aktuellen Streak berechnen
        if today < streak_start:
            current_days = 0
        else:
            current_days = (today - streak_start).days + 1
        
        # Alle Streaks sammeln
        all_streaks = []
        for h in data["history"]:
            all_streaks.append({
                "rank": 0,
                "start": h["start"],
                "end": h["end"],
                "days": h["days"]
            })
        
        all_streaks.append({
            "rank": 0,
            "start": data["streak_start"],
            "end": None,
            "days": current_days
        })
        
        # Sortieren und Top 3
        top_3 = sorted(all_streaks, key=lambda x: x["days"], reverse=True)[:3]
        
        # Ränge setzen
        for i, streak in enumerate(top_3):
            streak["rank"] = i + 1
        
        return top_3

    def _calculate_rank(self, top_3: list) -> int:
        for streak in top_3:
            if streak["end"] is None:
                return streak["rank"]
        return 0
```

---

### 4.3 `reset` – Reset Button

#### Beschreibung

Button zum Beenden des aktuellen Streaks. Drücken bedeutet "Heute ist das Ereignis eingetreten".

#### Eigenschaften

| Eigenschaft | Wert |
|-------------|------|
| **Entity ID Pattern** | `button.{name}_reset` |
| **Device Class** | `None` |
| **Icon** | `mdi:restart` |

#### Verhalten bei Druck

Siehe [Kapitel 2.7 - Zusammenfassung der Button-Logik](#27-zusammenfassung-der-button-logik).

#### Code-Beispiel

```python
class ResetButton(CoordinatorEntity, ButtonEntity):
    _attr_icon = "mdi:restart"

    async def async_press(self) -> None:
        await self.coordinator.async_handle_event(date.today())
```

---

## 5. Services

### 5.1 `streakhub.set_streak_start`

Setzt das Startdatum des aktuellen Streaks. Dient zur nachträglichen Korrektur wenn ein Button-Druck vergessen wurde.

#### Bedeutung

`set_streak_start(date)` bedeutet: **"Am Tag vor diesem Datum war das Ereignis, ich hatte vergessen zu drücken."**

#### Parameter

| Parameter | Typ | Required | Beschreibung |
|-----------|-----|----------|--------------|
| `entity_id` | `str` | Ja | Entity ID des Streak-Sensors |
| `date` | `date` | Ja | Neues Startdatum (erster Tag OHNE Ereignis) |

#### Beispiel

```
Aktueller Streak: Start 20.01
Heute: 27.01

User merkt: "Oh, ich hab am 24.01 Zucker gegessen aber nicht gedrückt!"
User ruft: set_streak_start(25.01)

Was passiert:
- Event-Tag (vergessen): 24.01
- Alter Streak endet: 23.01
- Alter Streak: 20.01 - 23.01 (4 Tage) → in History
- Neuer Streak beginnt: 25.01
- Heute (27.01): Streak = 3 Tage
```

#### Verhalten

```python
async def async_set_streak_start(self, new_start: date) -> None:
    """Setzt den Streak-Start (für vergessene Button-Drücke)."""
    event_day = new_start - timedelta(days=1)  # Der vergessene Event-Tag
    old_streak_end = event_day - timedelta(days=1)  # Letzter Tag OHNE Ereignis
    
    # Alten Streak berechnen
    old_start = date.fromisoformat(self.data["streak_start"])
    old_streak_days = (old_streak_end - old_start).days + 1
    
    if old_streak_days > 0:
        self.data["history"].append({
            "start": self.data["streak_start"],
            "end": old_streak_end.isoformat(),
            "days": old_streak_days
        })
    
    # Neuen Streak starten
    self.data["streak_start"] = new_start.isoformat()
    
    await self._store.async_save(self._all_data)
    await self.async_refresh()
```

#### Validierung und Fehlermeldungen

| Check | Fehler | Translation Key |
|-------|--------|-----------------|
| `date > today + 1` | Datum darf nicht in der Zukunft liegen | `date_in_future` |
| `date <= streak_start` | Datum muss nach dem aktuellen Streak-Start liegen | `date_before_streak_start` |

#### Code-Beispiel (Validierung)

```python
from homeassistant.exceptions import ServiceValidationError

async def handle_set_streak_start(call: ServiceCall) -> None:
    new_start = call.data["date"]
    tracker_data = coordinator.data
    current_start = date.fromisoformat(tracker_data["streak_start"])
    today = date.today()
    
    # Validierung 1: Nicht in der Zukunft
    if new_start > today + timedelta(days=1):
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="date_in_future",
        )
    
    # Validierung 2: Nach aktuellem Streak-Start
    if new_start <= current_start:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="date_before_streak_start",
            translation_placeholders={"streak_start": current_start.isoformat()}
        )
    
    # Alles okay, ausführen
    await coordinator.async_set_streak_start(new_start)
```

#### Übersetzungen (strings.json)

```json
{
  "exceptions": {
    "date_in_future": {
      "message": "The date cannot be in the future."
    },
    "date_before_streak_start": {
      "message": "The date must be after the current streak start ({streak_start})."
    }
  }
}
```

#### Service-Definition (services.yaml)

```yaml
set_streak_start:
  name: Set Streak Start
  description: Sets the start date of the current streak (for missed button presses)
  target:
    entity:
      integration: streakhub
      domain: sensor
  fields:
    date:
      name: Date
      description: The first day WITHOUT the event (day after the missed event)
      required: true
      selector:
        date:
```

---

## 6. ConfigFlow

### 6.1 Übersicht

Die Integration wird ausschließlich über die UI konfiguriert (kein YAML). Der ConfigFlow besteht aus einem einzelnen Schritt.

### 6.2 Konfigurationsparameter

| Parameter | Typ | Required | Default | Beschreibung |
|-----------|-----|----------|---------|--------------|
| `name` | `str` | Ja | - | Name des Trackers, wird zum Entity-Prefix |
| `initial_date` | `date` | Nein | heute | Optionales Startdatum für den ersten Streak |

### 6.3 ConfigFlow-Prozess

```
┌─────────────────────────────────────┐
│         async_step_user             │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ Name: [Zucker___________]   │    │
│  │                             │    │
│  │ Start-Datum: [2025-01-01]   │    │
│  │ (optional)                  │    │
│  └─────────────────────────────┘    │
│                                     │
│           [Submit]                  │
└─────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│      async_create_entry             │
│                                     │
│  - Set Unique ID (slugify(name))    │
│  - Create Config Entry              │
│  - Initialize Storage               │
│  - Start Integration Setup          │
└─────────────────────────────────────┘
```

### 6.4 Code-Beispiel

```python
class StreakHubConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors = {}

        if user_input is not None:
            unique_id = slugify(user_input[CONF_NAME])
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data=user_input
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME): str,
                vol.Optional(CONF_INITIAL_DATE, default=date.today().isoformat()): selector.DateSelector(),
            }),
            errors=errors,
        )
```

---

## 7. Technische Implementierung

### 7.1 Dateistruktur

```
streakhub/
├── custom_components/
│   └── streakhub/
│       ├── __init__.py          # Integration setup
│       ├── button.py            # Reset button entity
│       ├── config_flow.py       # UI configuration
│       ├── const.py             # Constants
│       ├── coordinator.py       # DataUpdateCoordinator
│       ├── manifest.json        # Integration metadata
│       ├── sensor.py            # Streak & Rank sensors
│       ├── services.yaml        # Service definitions
│       ├── strings.json         # Englische Übersetzungen
│       └── translations/
│           └── de.json          # German
```

### 7.2 DataUpdateCoordinator

Die Integration nutzt einen `DataUpdateCoordinator` für zentrales Datenmanagement.

**Update-Intervall:** 1 Stunde (oder bei Mitternacht neu berechnen)

**Warum Coordinator?** Obwohl die Daten lokal sind, sorgt der Coordinator für:
- Einheitliche Datenquelle für alle Entities
- Automatische Updates aller Entities bei Änderungen
- Saubere Handhabung von Speicher-Operationen

#### Code-Beispiel

```python
class StreakHubCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, store: Store, tracker_id: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"streakhub_{tracker_id}",
            update_interval=timedelta(hours=1),
        )
        self._store = store
        self._tracker_id = tracker_id
        self._all_data = None

    async def _async_update_data(self) -> dict:
        self._all_data = await self._store.async_load()
        return self._all_data["trackers"][self._tracker_id]

    async def async_handle_event(self, event_day: date) -> None:
        """Verarbeitet ein Ereignis (Button-Druck oder Service-Aufruf)."""
        data = self.data
        old_start = date.fromisoformat(data["streak_start"])
        
        old_streak_end = event_day - timedelta(days=1)
        new_streak_start = event_day + timedelta(days=1)
        
        old_streak_days = (old_streak_end - old_start).days + 1
        
        if old_streak_days > 0:
            data["history"].append({
                "start": data["streak_start"],
                "end": old_streak_end.isoformat(),
                "days": old_streak_days
            })
        
        data["streak_start"] = new_streak_start.isoformat()
        
        await self._store.async_save(self._all_data)
        await self.async_refresh()

    async def async_set_streak_start(self, new_start: date) -> None:
        """Setzt den Streak-Start (für vergessene Button-Drücke)."""
        event_day = new_start - timedelta(days=1)
        await self.async_handle_event(event_day)
```

### 7.3 Storage

Die Integration nutzt den Home Assistant `Store` für persistente Speicherung.

```python
from homeassistant.helpers.storage import Store

STORAGE_VERSION = 1
STORAGE_KEY = "streakhub"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    data = await store.async_load()
    
    if data is None:
        data = {"trackers": {}}
    
    tracker_id = slugify(entry.data[CONF_NAME])
    
    if tracker_id not in data["trackers"]:
        data["trackers"][tracker_id] = {
            "streak_start": entry.data.get(CONF_INITIAL_DATE, date.today().isoformat()),
            "history": []
        }
        await store.async_save(data)
    
    # Coordinator erstellen...
```

### 7.4 Device Registration

Alle Entities eines Trackers werden unter einem gemeinsamen Device gruppiert.

| Feld | Wert |
|------|------|
| **Name** | Benutzerdefinierter Name (z.B. "Zucker") |
| **Manufacturer** | "StreakHub" |
| **Software Version** | Version aus `manifest.json` |
| **Identifier** | `entry_id` des Config Entry |

### 7.5 manifest.json

```json
{
  "domain": "streakhub",
  "name": "StreakHub",
  "version": "1.0.0",
  "documentation": "https://github.com/...",
  "codeowners": ["@..."],
  "config_flow": true,
  "integration_type": "service",
  "iot_class": "calculated",
  "requirements": []
}
```

---

## 8. Dashboard-Beispiele

### 8.1 Einfache Anzeige

```yaml
type: entities
entities:
  - entity: sensor.zucker_streak
    name: Tage ohne Zucker
  - entity: sensor.zucker_rank
    name: Platzierung
  - entity: button.zucker_reset
    name: Zucker gegessen!
```

### 8.2 Pokal-Anzeige mit Template

```yaml
type: markdown
content: |
  {% set rank = states('sensor.zucker_rank') | int %}
  {% if rank == 1 %}
  # 🥇 NEUER REKORD!
  {% elif rank == 2 %}
  # 🥈 Platz 2
  {% elif rank == 3 %}
  # 🥉 Platz 3
  {% else %}
  # Weiter so!
  {% endif %}
  
  **{{ states('sensor.zucker_streak') }} Tage** ohne Zucker
```

### 8.3 Top 3 Bestenliste

```yaml
type: markdown
content: |
  ## 🏆 Bestenliste
  {% set top3 = state_attr('sensor.zucker_rank', 'top_3') %}
  {% for streak in top3 %}
  {% if streak.rank == 1 %}🥇{% elif streak.rank == 2 %}🥈{% else %}🥉{% endif %} **{{ streak.days }} Tage** ({{ streak.start }}{% if streak.end %} – {{ streak.end }}{% else %} – läuft{% endif %})
  {% endfor %}
```

### 8.4 Rekord direkt abrufen

```yaml
# Der Rekord ist immer der erste Eintrag in top_3
{{ state_attr('sensor.zucker_rank', 'top_3')[0].days }} Tage
```

---

## 9. Übersetzungen

### 9.1 strings.json (Englisch - Fallback)

```json
{
  "config": {
    "step": {
      "user": {
        "title": "Add StreakHub Tracker",
        "description": "Create a new StreakHub tracker to monitor days between events.",
        "data": {
          "name": "Name",
          "initial_date": "Initial start date (optional)"
        }
      }
    },
    "error": {
      "already_configured": "A tracker with this name already exists."
    }
  },
  "entity": {
    "sensor": {
      "streak": {
        "name": "Streak"
      },
      "rank": {
        "name": "Rank"
      }
    },
    "button": {
      "reset": {
        "name": "Reset"
      }
    }
  },
  "services": {
    "set_streak_start": {
      "name": "Set Streak Start",
      "description": "Sets the start date of the current streak (for missed button presses).",
      "fields": {
        "date": {
          "name": "Date",
          "description": "The first day WITHOUT the event (day after the missed event)."
        }
      }
    }
  },
  "exceptions": {
    "date_in_future": {
      "message": "The date cannot be in the future."
    },
    "date_before_streak_start": {
      "message": "The date must be after the current streak start ({streak_start})."
    }
  }
}
```

### 9.2 translations/de.json (Deutsch)

```json
{
  "config": {
    "step": {
      "user": {
        "title": "StreakHub Tracker hinzufügen",
        "description": "Erstelle einen neuen StreakHub Tracker um Tage zwischen Ereignissen zu zählen.",
        "data": {
          "name": "Name",
          "initial_date": "Initiales Startdatum (optional)"
        }
      }
    },
    "error": {
      "already_configured": "Ein Tracker mit diesem Namen existiert bereits."
    }
  },
  "entity": {
    "sensor": {
      "streak": {
        "name": "Streak"
      },
      "rank": {
        "name": "Platzierung"
      }
    },
    "button": {
      "reset": {
        "name": "Zurücksetzen"
      }
    }
  },
  "services": {
    "set_streak_start": {
      "name": "Streak-Start setzen",
      "description": "Setzt das Startdatum des aktuellen Streaks (für vergessene Button-Drücke).",
      "fields": {
        "date": {
          "name": "Datum",
          "description": "Der erste Tag OHNE das Ereignis (Tag nach dem vergessenen Ereignis)."
        }
      }
    }
  },
  "exceptions": {
    "date_in_future": {
      "message": "Das Datum darf nicht in der Zukunft liegen."
    },
    "date_before_streak_start": {
      "message": "Das Datum muss nach dem aktuellen Streak-Start ({streak_start}) liegen."
    }
  }
}
```

---

## 10. Edge Cases Zusammenfassung

| Situation | Verhalten |
|-----------|-----------|
| Erster Start | `streak_start` = heute, `history` = leer, `rank` = 1 |
| Button am Event-Tag | `sensor.streak` zeigt 0 |
| Button zweimal hintereinander | 0-Tage-Streak wird NICHT gespeichert |
| Button am Streak-Start-Tag | 0-Tage-Streak wird NICHT gespeichert |
| `set_streak_start` in Zukunft | `ServiceValidationError` |
| `set_streak_start` vor Streak-Start | `ServiceValidationError` |
| Weniger als 3 Streaks | `top_3` enthält weniger als 3 Einträge |

---

## 11. Offene Punkte

| Punkt | Status | Entscheidung |
|-------|--------|--------------|
| History-Begrenzung | Entschieden | Unbegrenzt (Datenmenge minimal) |
| Statistik-Sensor | Später | Nicht im MVP |
| Übersetzungen | MVP | Englisch + Deutsch |
| HACS-Distribution | Später | Nach stabilem Release |

---

## 12. Ressourcen

### Home Assistant Development

| Thema | Link |
|-------|------|
| Developer Documentation | https://developers.home-assistant.io/ |
| Sensor Entity | https://developers.home-assistant.io/docs/core/entity/sensor/ |
| Button Entity | https://developers.home-assistant.io/docs/core/entity/button/ |
| ConfigFlow | https://developers.home-assistant.io/docs/config_entries_config_flow_handler/ |
| DataUpdateCoordinator | https://developers.home-assistant.io/docs/integration_fetching_data/#coordinated-single-api-poll-for-data-for-all-entities |
| Storage | https://developers.home-assistant.io/docs/api/storage/ |
| Services | https://developers.home-assistant.io/docs/dev_101_services/ |
| Service Exceptions | https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/action-exceptions/ |

### Referenz-Integrationen

| Integration | Link | Relevanz |
|-------------|------|----------|
| Counter (HA Core) | https://github.com/home-assistant/core/tree/dev/homeassistant/components/counter | Ähnliches Konzept |
| Timer (HA Core) | https://github.com/home-assistant/core/tree/dev/homeassistant/components/timer | Persistenz-Muster |
| solstice_season | (lokal) | Strukturvorlage |

---

*Dieses Konzept dient als Grundlage für die Implementierung der `streakhub` Home Assistant Integration.*
