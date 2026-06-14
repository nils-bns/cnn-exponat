# Storage Layer

Dieses Dokument beschreibt Aufbau, Verantwortlichkeiten und Zusammenspiel der Komponenten im `storage/`-Package. Es richtet sich an Entwickler, die den Code warten, erweitern oder debuggen.

---

## Inhaltsverzeichnis

1. [Einordnung in die Gesamtarchitektur](#einordnung-in-die-gesamtarchitektur)
2. [Package-Struktur](#package-struktur)
3. [Interface](#interface)
4. [ConfigManager](#configmanager)
5. [Default-Konfiguration](#default-konfiguration)
6. [Serialisierung und Deserialisierung](#serialisierung-und-deserialisierung)
7. [Atomare Schreiboperationen](#atomare-schreiboperationen)
8. [Migrationslogik](#migrationslogik)
9. [Seiteneffekte](#seiteneffekte)
10. [Fehlerbehandlung](#fehlerbehandlung)
11. [JSON-Schema](#json-schema)
12. [Design-Entscheidungen](#design-entscheidungen)
13. [Erweiterung](#erweiterung)

---

## Einordnung in die Gesamtarchitektur

Die Anwendung folgt einer Drei-Schichten-Architektur:

```
View (PyQt6)  -->  Core (Services + Facade)  -->  Storage (JSON-Config)
```

Der Storage Layer ist die unterste Schicht. Er ist ausschliesslich fuer die Persistierung der Konfiguration zustaendig -- also das Laden und Speichern der `config.json`. Er enthaelt keine Geschaeftslogik und keine Validierung. Beides gehoert in den Core Layer.

Der Core Layer spricht den Storage Layer ueber das `IConfigStorage`-Protocol an. Die konkrete Implementation (`ConfigManager`) wird in `main.py` instanziiert und per Dependency Injection an den Core uebergeben. Der Storage Layer hat seinerseits eine Abhaengigkeit zum Core, da er die Datenmodelle (`ConfigData`, `LayerPresets`, `PresetConfig`) von dort importiert.

---

## Package-Struktur

```
storage/
    __init__.py             # Public API: ConfigManager, IConfigStorage, get_default_config
    interfaces.py           # IConfigStorage Protocol
    config_manager.py       # JSON-Persistierung (Laden, Speichern, Serialisierung)
    default_config.py       # Default-Presets fuer alle ResNet18-Layer
```

Die `__init__.py` exportiert genau drei Symbole:

```python
__all__ = [
    'ConfigManager',       # Konkrete Implementation
    'IConfigStorage',      # Protocol (fuer Type Hints im Core)
    'get_default_config',  # Factory-Funktion fuer Default-Config
]
```

---

## Interface

Definiert in `interfaces.py`. Das Protocol `IConfigStorage` beschreibt die Schnittstelle, die der Core Layer vom Storage erwartet:

```
load_config() -> ConfigData
save_config(config: ConfigData) -> None
```

Es handelt sich um ein `typing.Protocol` (strukturelles Subtyping). `ConfigManager` erbt nicht explizit von `IConfigStorage`, sondern erfuellt das Protocol implizit durch die passenden Methodensignaturen. Das ist konsistent mit der Handhabung im Core Layer (siehe `core/core-doc.md`, Abschnitt "Design-Entscheidungen").

Bei Fehlern werden `ConfigLoadError` bzw. `ConfigSaveError` geworfen. Beide sind in `core/exceptions.py` definiert.

---

## ConfigManager

**Datei:** `config_manager.py`

Zentrale Klasse des Storage Layers. Uebernimmt die gesamte JSON-I/O-Logik.

### Konstruktor

Erwartet einen optionalen Dateipfad (Default: `config.json` relativ zum Arbeitsverzeichnis). Der Pfad wird intern als `Path`-Objekt gespeichert.

### load_config

Laedt die Konfiguration aus der JSON-Datei und gibt ein `ConfigData`-Objekt zurueck. Wenn die Datei nicht existiert, wird automatisch eine Default-Konfiguration erstellt, gespeichert und zurueckgegeben. Bei korruptem JSON wird eine `ConfigLoadError` geworfen.

### save_config

Serialisiert ein `ConfigData`-Objekt und schreibt es in die JSON-Datei. Der Schreibvorgang ist atomar (siehe Abschnitt "Atomare Schreiboperationen"). Falls das Zielverzeichnis noch nicht existiert, wird es angelegt.

### Interne Methoden

Die Serialisierung und Deserialisierung ist in sechs private Methoden aufgeteilt, je eine pro Richtung fuer die drei Ebenen der Datenstruktur:

| Methode | Richtung | Ebene |
|---------|----------|-------|
| `_serialize_config` | Python -> dict | ConfigData |
| `_serialize_layer_presets` | Python -> dict | LayerPresets |
| `_serialize_preset` | Python -> dict | PresetConfig |
| `_deserialize_config` | dict -> Python | ConfigData |
| `_deserialize_layer_presets` | dict -> Python | LayerPresets |
| `_deserialize_preset` | dict -> Python | PresetConfig |

---

## Default-Konfiguration

**Datei:** `default_config.py`

Die Funktion `get_default_config()` liefert ein vollstaendiges `ConfigData`-Objekt mit Presets fuer alle fuenf ResNet18-Layer (`conv1`, `layer1` bis `layer4`). Jeder Layer hat drei vorkonfigurierte Presets mit unterschiedlichen Channel-Auswahlen, Colormaps und Blend-Modes.

Diese Funktion wird in zwei Situationen aufgerufen:

1. Beim ersten Start der Anwendung, wenn noch keine `config.json` existiert. Der `ConfigManager` ruft dann intern `_create_default_config()` auf, das die Defaults generiert und sofort auf die Platte schreibt.
2. In Tests, um eine bekannte Ausgangskonfiguration herzustellen.

Die Default-Werte sind bewusst konservativ gewaehlt: Alle Presets verwenden `visualization_mode="colormap"`, `normalize=True` und Channel-Indizes, die innerhalb der tatsaechlichen Channel-Anzahl des jeweiligen Layers liegen.

---

## Serialisierung und Deserialisierung

Die Umwandlung zwischen Python-Objekten und JSON-kompatiblen Dictionarys passiert manuell. Es gibt kein Framework wie Pydantic oder Marshmallow -- die Konvertierung ist explizit in den `_serialize_*` und `_deserialize_*` Methoden implementiert.

Beim Deserialisieren werden fehlende Felder mit vernuenftigen Defaults aufgefangen:

| Feld | Default bei fehlendem Key |
|------|--------------------------|
| `version` | `"1.0"` |
| `presets` | `{}` (leeres Dict) |
| `layer_name` | `""` |
| `active_preset_id` | `0` |
| `preset_id` | `0` |
| `name` | `""` |
| `channels` | `[]` |
| `colormap` | `"viridis"` |
| `normalize` | `True` |
| `blend_mode` | `"max"` |
| `visualization_mode` | `"colormap"` |

Diese Defaults machen das System robust gegenueber unvollstaendigen oder aelteren Config-Dateien. Ein Preset, das vor der Einfuehrung von `visualization_mode` gespeichert wurde, bekommt automatisch `"colormap"` zugewiesen.

---

## Atomare Schreiboperationen

Der `save_config`-Vorgang schreibt nicht direkt in die Zieldatei, sondern folgt einem Write-then-Replace-Pattern:

1. Die serialisierten Daten werden in eine temporaere Datei (`config.tmp`) geschrieben.
2. Die temporaere Datei wird per `Path.replace()` an den Platz der eigentlichen Config-Datei verschoben.

`Path.replace()` nutzt intern `os.replace()`, das auf Windows `MoveFileEx` mit `MOVEFILE_REPLACE_EXISTING` aufruft. Das ist eine einzelne Betriebssystem-Operation. Falls die Anwendung waehrend des Schreibens abstuerzt, bleibt entweder die alte Config-Datei intakt (Absturz vor dem Replace) oder die neue ist vollstaendig geschrieben (Absturz nach dem Replace). Ein Zustand mit korrupter oder leerer Datei wird vermieden.

---

## Migrationslogik

In `_deserialize_preset` gibt es Logik zum Umgang mit aelteren Config-Formaten:

**visualization_mode:** Alte Configs kennen dieses Feld nicht. Beim Laden wird `"colormap"` als Default verwendet. Das Feld wird beim naechsten Speichern automatisch mit geschrieben, wodurch die Config stillschweigend migriert wird.

**Custom-Colormap:** Wenn ein Preset die inzwischen nicht mehr unterstuetzte Colormap `"custom"` verwendet, wird sie beim Laden auf `"viridis"` umgeschrieben und eine Warnung geloggt. Auch hier erfolgt die Migration beim naechsten Speichern.

Beide Migrationen sind verlustfrei und erfordern keinen manuellen Eingriff.

---

## Seiteneffekte

Der Storage Layer ist im Vergleich zum Core Layer ueberschaubar, hat aber Methoden, die auf das Dateisystem schreiben. Diese Seiteneffekte sind relevant fuer Tests (Mocking noetig) und fuer das Verstaendnis, wann tatsaechlich Disk-I/O stattfindet.

### Uebersicht

| Methode | Art des Seiteneffekts |
|---------|-----------------------|
| `load_config()` | Dateisystem lesen; bei fehlender Datei zusaetzlich schreiben |
| `save_config()` | Dateisystem schreiben (temp-Datei + replace) |
| `_create_default_config()` | Dateisystem schreiben (ruft `save_config` auf) |

### ConfigManager

**`load_config()`** -- Liest die `config.json` vom Dateisystem. Das allein ist ein Seiteneffekt im formalen Sinn (I/O), aber der weniger offensichtliche Fall ist wichtiger: Wenn die Datei nicht existiert, wird `_create_default_config()` aufgerufen, das eine vollstaendige Default-Config auf die Platte schreibt. Ein reiner "Lese"-Aufruf kann also eine Datei erzeugen. Dieses Verhalten ist gewollt (siehe Design-Entscheidungen), muss aber beim Testen beruecksichtigt werden -- ein `load_config()` auf ein leeres temporaeres Verzeichnis hinterlaesst eine Datei.

**`save_config()`** -- Schreibt zwei Dateien: zuerst `config.tmp`, dann wird diese per `Path.replace()` an den Platz von `config.json` verschoben. Falls das Verzeichnis noch nicht existiert, wird es angelegt (`mkdir(parents=True)`). Nach dem Aufruf existiert also garantiert sowohl das Verzeichnis als auch die Config-Datei.

**`_create_default_config()`** -- Interne Methode, die `get_default_config()` aufruft und das Ergebnis sofort per `save_config()` persistiert. Die Seiteneffekte sind identisch mit denen von `save_config()`.

### Seiteneffektfreie Methoden und Funktionen

Alles andere im Storage Layer ist seiteneffektfrei:

- `get_default_config()` erzeugt ein `ConfigData`-Objekt rein im Speicher, ohne Dateisystem-Zugriff.
- Alle `_serialize_*` und `_deserialize_*` Methoden transformieren Daten zwischen Dictionarys und Dataclasses, ohne I/O.
- Der Konstruktor von `ConfigManager` speichert nur den Pfad und loggt eine Zeile. Er oeffnet keine Dateien und liest nichts.

---

## Fehlerbehandlung

Der Storage Layer verwendet zwei spezifische Exceptions aus `core/exceptions.py`:

| Exception | Wird geworfen wenn | Typischer Ausloeser |
|-----------|--------------------|--------------------|
| `ConfigLoadError` | JSON nicht geladen oder geparst werden kann | Korrupte Datei, fehlende Lese-Rechte |
| `ConfigSaveError` | Datei nicht geschrieben werden kann | Fehlende Schreibrechte, volle Festplatte |

Bei fehlender Config-Datei wird keine Exception geworfen -- stattdessen wird die Default-Konfiguration angelegt. Das ist gewollt, damit die Anwendung beim ersten Start ohne manuelle Konfiguration laeuft.

Alle Fehlerfaelle werden vor dem Werfen der Exception geloggt (`logger.error`). Normale Vorgaenge wie das Anlegen einer Default-Config werden als `logger.warning` bzw. `logger.info` protokolliert.

---

## JSON-Schema

Die `config.json` hat folgende Struktur:

```json
{
  "version": "1.0",
  "presets": {
    "conv1": {
      "layer_name": "conv1",
      "active_preset_id": 0,
      "presets": [
        {
          "preset_id": 0,
          "name": "Edge Detection",
          "channels": [0, 1, 2],
          "colormap": "viridis",
          "normalize": true,
          "blend_mode": "max",
          "visualization_mode": "colormap"
        }
      ]
    },
    "layer1": { ... },
    "layer2": { ... },
    "layer3": { ... },
    "layer4": { ... }
  }
}
```

Die Top-Level-Keys von `presets` entsprechen den ResNet18-Layer-Namen. Jeder Layer enthaelt bis zu drei Presets (ID 0, 1, 2) und verweist per `active_preset_id` auf das aktuell ausgewaehlte Preset. Die Datei wird mit `indent=2` und `ensure_ascii=False` geschrieben, um sie menschenlesbar zu halten.

---

## Design-Entscheidungen

### Manuelle Serialisierung statt Framework

Die Konvertierung zwischen Python-Objekten und JSON erfolgt von Hand. Ein Framework wie Pydantic waere moeglich, wuerde aber eine zusaetzliche Abhaengigkeit einfuehren und fuer das relativ simple Schema keinen wesentlichen Vorteil bringen. Die manuelle Variante macht die Migrationslogik (Default-Werte, Custom-Colormap-Umschreibung) explizit und leicht nachvollziehbar.

### Kein Caching

Der `ConfigManager` speichert intern keinen Zustand. Jeder Aufruf von `load_config()` liest die Datei neu von der Platte. Das vermeidet Konsistenzprobleme bei mehrfachem Laden/Speichern und haelt die Klasse zustandslos. Da Config-Laden kein Performance-kritischer Pfad ist (passiert beim Start und beim Preset-Wechsel, nicht im Render-Loop), ist der Overhead vernachlaessigbar.

### Keine Validierung im Storage Layer

Die Validierung der Datenmodelle (`preset_id` in [0, 1, 2], gueltiger `blend_mode`, etc.) findet ausschliesslich in den `__post_init__`-Methoden der Dataclasses im Core Layer statt. Der Storage Layer deserialisiert nur und uebergibt die Objekte. Wenn die JSON-Daten ungueltig sind, schlaegt die Validierung beim Erstellen der Dataclass fehl -- nicht beim Parsen.

### Default-Config wird auf Platte geschrieben

Wenn beim Start keine `config.json` existiert, wird die Default-Konfiguration nicht nur im Speicher zurueckgegeben, sondern sofort auf die Platte geschrieben. Das stellt sicher, dass spaetere Aenderungen (z.B. Preset-Wechsel durch den Benutzer) persistent gespeichert werden koennen, ohne einen Sonderfall fuer "Config existiert noch nicht" behandeln zu muessen.

---

## Erweiterung

### Neues Feld in PresetConfig

1. Das Feld in `core/models.py` zu `PresetConfig` hinzufuegen (mit Default-Wert).
2. In `_serialize_preset` das Feld ins Dictionary aufnehmen.
3. In `_deserialize_preset` das Feld per `data.get()` mit einem sinnvollen Default auslesen. Dadurch werden alte Config-Dateien, die das Feld noch nicht enthalten, automatisch migriert.
4. In `default_config.py` das Feld in allen Default-Presets setzen.

### Neuen Layer unterstuetzen

Die Default-Config in `default_config.py` um einen weiteren `LayerPresets`-Block erweitern und ihn ins `presets`-Dictionary aufnehmen. Am ConfigManager selbst muss nichts geaendert werden -- die Serialisierung ist generisch ueber alle Layer-Keys.

### Anderes Speicherformat (z.B. SQLite)

1. Neue Klasse erstellen, die das `IConfigStorage`-Protocol erfuellt (`load_config`, `save_config`).
2. In `main.py` die neue Klasse statt `ConfigManager` instanziieren.
3. Der restliche Code (Core, View) bleibt unveraendert, da er nur gegen das Protocol programmiert ist.
