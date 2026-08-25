# Better Todo — Spezifikation

Stand: 2026-08-25 · Status: **mit Nutzer abgestimmt, Basis für die Entwicklung**

Custom Home Assistant Integration + eigene Lovelace-Karte für eine funktionsreiche Todo-Verwaltung.
Verteilung ausschließlich über HACS-Releases (ein Repository, Integration liefert die Karte mit aus).

---

## 1. Grundarchitektur

- **Eigene Datenhaltung**, kein Aufsatz auf das HA-`todo`-Entity-Modell. Speicherung über
  `homeassistant.helpers.storage.Store` (JSON in `.storage/`, wird von HA-Backups automatisch erfasst).
- **Integration** (`custom_components/better_todo/`): Datenmodell, Wiederholungs-Engine,
  WebSocket-API, Services, Events, optionale Sensor-/Spiegel-Entities.
- **Karte**: eigenes Lovelace-Custom-Card-JavaScript, wird **von der Integration ausgeliefert**
  (statischer Pfad + automatische Registrierung als Lovelace-Ressource). Dadurch:
  ein HACS-Repo (Kategorie "Integration"), Karte und Backend immer versionsgleich.
- Karte kommuniziert über die **HA-WebSocket-API** mit eigenen Commands
  (volles Datenmodell, nicht auf Entity-Attribute beschränkt).
  **Berechtigungen** (Entscheidung 2026-08-25): destruktive Massen-Kommandos
  (`delete_list`, `clear_completed`) sind Admin-only; Aufgaben anlegen/bearbeiten/
  erledigen/löschen darf jeder angemeldete HA-Benutzer. Die Karte blendet
  Admin-Aktionen für Nicht-Admins aus.
- **Spätere Ausbaustufe**: optionales Spiegel-`todo`-Entity pro Liste (nur offene Aufgaben
  mit Solldatum) für Sprachassistenten / HA-App / Standard-Automationen. Wahrheit bleibt
  immer die eigene Datenhaltung.

## 2. Feature-Schalter (zentrale Konfiguration)

Im Options-Flow der Integration global an-/abschaltbar. Abgeschaltete Features werden
überall ausgeblendet (Karte, Dialoge, Services validieren trotzdem tolerant).
Skala: von „dumme Liste" bis Vollausbau.

| Schalter | Default | Wirkung |
|---|---|---|
| Prioritäten | aus | Prioritätsfeld an Aufgaben + Sortierung/Filter |
| Unteraufgaben | an | Checklisten unterhalb einer Aufgabe |
| Zuweisung | an | Aufgaben an Personen zuweisbar, „Meine Aufgaben"-Sicht |
| Rotation | an | rotierende Zuweisung (setzt Zuweisung voraus) |
| Perioden-Aufgaben & Streaks | an | Wochen-/Monats-Todos mit Strähnen |
| Tags | an | Schlagwörter an Aufgaben + Filter-Chips in der Karte |
| Spiegel-Todo-Entities | an | Standard-`todo`-Entity pro Liste (Companion-App, Watch, Sprachassistenten) |
| Kalender-Entities | an | `calendar`-Entity pro Liste; Aufgaben mit Fälligkeit erscheinen im HA-Kalender, wiederholende auf jedem Termin |
| Benachrichtigungen | — | über Erinnerungs-Events + eigene Automation (kein eigener Schalter nötig) |

## 3. Datenmodell

### 3.1 Liste
- `id`, `name`, `icon`, `farbe` (optional), `sortierung` (Position)
- Beispiele: Haushaltsaufgaben, Projekte am Haus, Gesunde Woche

### 3.2 Aufgabe
Gemeinsame Felder aller Typen:
- `id`, `listen_id`, `titel`, `notiz` (optional)
- `typ`: `einfach` | `wiederholend_plan` | `wiederholend_erledigung` | `periode`
- `status`: `offen` | `erledigt` (bei wiederholenden: Zustand der aktuellen Instanz)
- `prioritaet` (optional, Feature-Schalter)
- `unteraufgaben`: Liste aus `{titel, erledigt}` (Feature-Schalter)
- `zugewiesen_an`: `person`-Entity-ID (Feature-Schalter)
- `rotation`: `{personen: [person_ids], aktueller_index}` (Feature-Schalter; ersetzt feste
  Zuweisung — bei jeder neuen Instanz rückt die nächste Person aus dem definierten
  Personenkreis nach; Personenkreis pro Aufgabe frei wählbar, z. B. „Müll: Kinder",
  „Bad: Erwachsene")
- `sichtbar_ab` (optional): Aufgabe erscheint erst ab diesem Datum
- `faellig_am` (optional): Solldatum / Deadline
- `faellig_um` (optional): **Uhrzeit** zur Fälligkeit (Anzeige + Erinnerungen; die
  Wiederholungslogik rechnet weiterhin auf Tagesbasis)
- `erinnerungen` (optional): bis zu 5 Vorlaufzeiten (Minuten vor Fälligkeit); feuern als
  Event `better_todo_item_reminder` — Push-Benachrichtigungen baut man per Automation darauf.
  **Neustart-fest** (Entscheidung 2026-08-25): Erinnerungszeitpunkte, die in eine
  HA-Downtime fallen, werden nach dem Neustart einmalig nachgeholt (Fenster max. 48 h);
  bereits gefeuerte Erinnerungen und die Tageszusammenfassung werden persistiert
  (At-least-once: nur ein harter Absturz unmittelbar nach dem Senden kann eine
  Erinnerung wiederholen).
- `tags` (optional): freie Schlagwörter, quer zu Listen, filterbar in der Karte
- `sortierung` innerhalb der Liste (manuell, per Drag & Drop in der Karte)

### 3.3 Aufgabentypen im Detail

**a) Einfache Aufgabe** — einmalig, mit oder ohne Datum.
Optional beide Datumsfelder: `sichtbar_ab` (öffnet) und `faellig_am` (Deadline).
Beispiel Vertragskündigung: sichtbar ab 1.12., fällig 31.12. → Karte zeigt Countdown,
Farbeskalation bei näher rückender Deadline.

**b) Wiederholend, plan-basiert** — nächste Fälligkeit ergibt sich aus dem Plan,
unabhängig vom Erledigungszeitpunkt.
Beispiel: Rechnung fällig am 1.1., erledigt am 10.1. → nächste Instanz am 1.2.
Regelmechanik (eigene Regelstruktur, kein volles RRULE):
- täglich/wöchentlich/monatlich/jährlich mit Intervall k
- wöchentlich auch **mehrere Wochentage** (z. B. Mo+Do)
- monatlich: fester Tag (mit Klemmung bei kurzen Monaten), **„letzter Tag"** oder
  **„n-ter Wochentag"** (z. B. „2. Samstag", „letzter Mittwoch")
- optional **Enddatum** und/oder **maximale Anzahl Wiederholungen** — danach gilt die
  Aufgabe als abgeschlossen
- **Überfällig-Verhalten**: immer **eine** offene Aufgabe mit „n× fällig"-Zähler
  (kein Stapeln separater Instanzen — Entscheidung 2026-08-25). Beim Abhaken wählbar:
  **1× erledigen** (Zähler −1, Aufgabe bleibt offen solange n > 0) oder **alle erledigen**.
  Oberflächen ohne diese Wahl (Spiegel-Todo-Entity, also Companion-App/Watch/Sprache)
  erledigen **genau 1×** — nichts wird dort stillschweigend komplett geleert
  (Entscheidung 2026-08-25). „Alle erledigen" zählt alle konsumierten Vorkommen
  für `max. Wiederholungen`.
- Optional `vorlauf_tage`: Instanz wird erst n Tage vor Fälligkeit sichtbar.

**c) Wiederholend, erledigungs-basiert** — nächste Fälligkeit = Erledigungsdatum + Intervall.
Beispiel: Klo reinigen fällig 1.1., erledigt 20.1. → nächste Fälligkeit 20.2.
Intervall in Tagen/Wochen/Monaten. Nächste Instanz entsteht **erst bei Erledigung**
(nichts wird auf Vorrat angelegt).

**d) Perioden-Aufgabe (Habit)** — pro Woche/Monat genau einmal zu erledigen,
alle öffnen zu Periodenbeginn gemeinsam neu.
Beispiel „Gesunde Woche": einmal Fahrrad fahren, einmal vegetarisch essen.
- Pro Periode ein Zustand erledigt/nicht erledigt → daraus automatisch:
  - **Strähne**: „15 Wochen in Folge erledigt"
  - **Versäumnis**: „seit 3 Wochen nicht erledigt" (Markierung in der Karte)
- Periodengrenzen: Woche = Mo–So, Monat = Kalendermonat (Zeitzone Europe/Berlin,
  aus HA-Konfiguration übernommen).

### 3.4 Erledigungs-Historie
Ab Tag 1 mitgeschrieben, für jede Erledigung: `aufgaben_id`, `zeitpunkt`, `nutzer/person`.
Grundlage für Streaks, „zuletzt erledigt am", Statistiken („wer hat diesen Monat wie viel
gemacht"). Aufbewahrung konfigurierbar (Default: unbegrenzt, Datenmenge trivial).

### 3.5 Überspringen / Verschieben
- Plan-basiert & Periode: „diese Instanz überspringen" — zählt nicht als erledigt,
  zerstört aber Rhythmus/Strähne nicht (Streak wird „eingefroren", nicht zurückgesetzt).
- Erledigungs-basiert: nächste Fälligkeit manuell verschiebbar.

## 4. Automatisierungs-Schnittstelle

**Services** (Auszug): `better_todo.add_item`, `complete_item`, `skip_item`,
`update_item`, `remove_item` — damit Automationen Aufgaben anlegen können
(z. B. „Waschmaschine fertig → Aufgabe ‚Wäsche aufhängen'").

**Events**: `better_todo_item_completed`, `better_todo_item_due`,
`better_todo_item_overdue` — damit Automationen auf Aufgaben reagieren können.

**Sensoren** (optional, je Liste / je Person): Anzahl offene / heute fällige /
überfällige Aufgaben — für Badges, bedingte Karten, Automationen.

## 5. Lovelace-Karte

- Eine dynamische Karte, per Parameter konfigurierbar:
  - Quelle: eine Liste, mehrere Listen oder alle
  - Filter: Person („meine Aufgaben" = eingeloggter HA-Nutzer), Status, fällig bis, Typ
  - Darstellung: Gruppierung (nach Liste / Fälligkeit), Sortierung, kompakt/detailliert
  - optionales **Interaktionsmenü** in der Karte (Listen-/Filterwahl durch den Nutzer
    selbst), damit nicht pro Nutzer ein eigenes Dashboard gepflegt werden muss
- Anzeigen: Fälligkeit + Countdown bei Deadline-Aufgaben, Überfällig-Zähler,
  Streak-/Versäumnis-Badges bei Perioden-Aufgaben, zugewiesene Person (Avatar),
  Unteraufgaben-Fortschritt (z. B. 3/7)
- Interaktionen: abhaken, überspringen, Aufgabe anlegen/bearbeiten (Dialog), Unteraufgaben
- Design ausschließlich über **HA-Theme-Variablen** → passt sich automatisch jedem Theme an

## 6. Repository / HACS

- Repo: GitHub `Timmes123/ha-better-todo` (Arbeitstitel), HACS-Kategorie Integration
- Struktur: `custom_components/better_todo/` (inkl. `www/better-todo-card.js`),
  `hacs.json`, `manifest.json`, README, HACS-Validation-Action, getaggte Releases
- Deployment ausschließlich: Commit → Version-Bump → Release → HACS-Update → HA-Neustart

## 7. Karte — erweiterte Anforderungen (2026-08-25, aus Wettbewerbsanalyse)

- Sortier-Optionen pro Karte: manuell, Fälligkeit, Priorität, Titel, Person;
  manuelle Reihenfolge per Drag & Drop
- „Bald fällig"-Filter mit einstellbarem Vorlauf (Tage)
- Komfort: Kompakt-Modus, maximale Höhe mit internem Scrollen, optionale
  Bestätigung vor dem Erledigen
- **Visueller Karten-Editor** (GUI-Konfiguration statt nur YAML)
- Mehrsprachigkeit über DE/EN hinaus (FR, ES, IT, NL, PL, …)

## 8. Ausbaustufen (Grobplan)

1. ✅ **v0.2 MVP**: Listen, alle 4 Aufgabentypen, Wiederholungs-Engine, Historie,
   WebSocket-API, Karte mit Grundfunktionen, Zuweisung + Rotation, Feature-Schalter
2. **v0.3**: Uhrzeit + Erinnerungen, erweiterte Wiederholungsmuster, Tags,
   Spiegel-Todo- und Kalender-Entities, Karten-Ausbau (Sortierung, Drag & Drop,
   Editor, Komfort-Optionen, mehr Sprachen)
3. Sensoren (offene/fällige/überfällige je Liste & Person), Statistiken,
   Sections innerhalb von Listen, Kanban-Ansicht, Audit-Log, Aufgabe duplizieren
4. **KI-Anbindung** (optional): z. B. Aufgabenbilder über `ai_task`-Entities,
   Vorschläge. Architektur-Vorgabe schon jetzt: Datenmodell erweiterbar halten
   (Aufgaben verkraften unbekannte Zusatzfelder), KI-Aufrufe immer über
   HA-Standard-Schnittstellen (`ai_task`), nie fest an einen Anbieter gebunden
5. **Externer Sync** (CalDAV, externe Aufgaben-Dienste) — bewusst ganz hinten:
   vom Nutzer aktuell nicht benötigt, evtl. für andere Nutzer nach Veröffentlichung.
   Falls es kommt: Overlay-Prinzip (lokale Zusatzfelder über externen Items),
   unsere Spezialtypen bleiben lokal führend

---

*Offene Punkte werden hier ergänzt, Entscheidungen datiert nachgetragen.*
