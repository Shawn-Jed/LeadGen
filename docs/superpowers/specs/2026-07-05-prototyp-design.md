# Subsystem C — Prototyp (Live-Demo pro Lead)

**Datum:** 2026-07-05
**Status:** Design (bereit für Planung)
**Kontext:** Fünftes Subsystem (C) des LeadGen-Akquise-Cockpits. Baut auf Discovery (A),
Tracking (B) und Outreach (D) auf und speist D.

## Problem

Eine Kaltakquise-Mail mit reinem Text („Ihre Website hat kein Mobil-Layout") überzeugt
schwächer als eine Mail mit einer klickbaren Live-Demo der verbesserten Seite. Discovery
kennt die konkrete Schwäche jedes Betriebs bereits (Tier 2/3). Es fehlt der Schritt, der
daraus eine überzeugende Demo macht und deren Link in die Outreach-Mail bringt.

## Ziel

Pro Lead **optional** (Opt-in per Schalter, nicht automatisch für alle) eine maßgeschneiderte
One-Pager-Demo der verbesserten Website erzeugen, live unter einer URL hosten und den Link
in den Outreach-Flow einspeisen. Der Kunde klickt den Link und sieht die Demo sofort live —
ohne eigenen Aufwand.

## Entscheidungen (aus dem Brainstorming)

| Frage | Entscheidung |
|---|---|
| Wann bauen? | **Opt-in pro Lead** — Schalter im Lead-Drawer, nicht automatisch |
| Was entsteht? | **Live One-Pager** unter einer klickbaren URL |
| Hosting? | **GitHub Pages** — Kunde klickt, Browser lädt Live-Seite, kein Kundenaufwand |
| Wer baut das HTML? | **Claude Code** (prototyp-Skill), wie beim Outreach-Muster — jede Demo individuell |
| Deploy-Ziel | Eigenes **öffentliches Repo `prototyp`**, pro Lead Ordner `/<slug>/` |
| URL-Form | `shawn-jed.github.io/prototyp/<slug>` (Repo-Name ist in der URL sichtbar) |
| Kopplung an D | Fertige URL **füllt den Outreach-Wizard automatisch vor** (mode=link) |
| Demo-Schutz | **Keine** noindex/Hinweise — saubere Seite, stärkster Effekt |

## Architektur

Das Design **spiegelt bewusst das Outreach-Muster (Subsystem D)** — gleiche Form, bekannter
Code, wiederverwendbare Testmuster. C und D sind fast identisch geformt: Opt-in im Cockpit →
Auftrag → Claude Code baut das Artefakt → Ergebnis/Link zurück ins Cockpit.

### Fluss

```
Lead-Drawer: Schalter "🎨 Prototyp bauen"
   │
   ▼
POST /api/leads/<slug>/prototyp/request      → Auftrag: status "pending"
   │
   ▼
Claude Code (prototyp-Skill, Watch-Loop)
   • GET /api/prototyp/pending                → offene Aufträge (slug)
   • Lead-Kontext aus GET /api/state          → firma, schwaeche, branche, ucp, ort
   • baut maßgeschneiderte One-Pager index.html
   • POST /api/leads/<slug>/prototyp/draft {html}
        │
        ▼
   Backend deployt:  prototyp-Repo /<slug>/index.html  →  git add/commit/push
        │
        ▼
   Store: status "ready", url = shawn-jed.github.io/prototyp/<slug>
   │
   ▼
Cockpit pollt GET /api/leads/<slug>/prototyp → zeigt Link + "öffnen"
   │
   ▼
Outreach-Wizard (D): prototyp = {mode: "link", url} vorausgefüllt
```

## Komponenten

Alle Backend-Dateien unter `backend/`, analog zu den bestehenden Outreach-Modulen.

### `prototyp.py` — Zustands-Store (spiegelt `outreach.py` exakt)

Verwaltet pro Lead den Prototyp-Zustand. Zustände:

- `none` — kein Prototyp angefordert (Default; kein Store-Eintrag)
- `pending` — Schalter auf „Ja", wartet auf Claude Code
- `ready` — HTML gebaut, deployt, URL verfügbar

Datenfelder pro Lead: `status`, `url` (bei ready), `angefordert_am`, `erstellt_am`.

Persistenz: **eigener JSON-Store `<root>/prototyp/<slug>.json`**, exakt wie `outreach.py`
(`<root>/outreach/<slug>.json`). Keyed per `slug` — dadurch **unabhängig davon, ob der Lead
kalt (in `pipeline.md`) oder warm (`leads/<slug>.md`) ist.** Das ist wichtig: einen Prototyp
baut man gerade, um einen noch kalten Lead zu überzeugen. Kein Frontmatter-Eingriff, kein
`leadtool`-Change nötig.

Reine Funktionen (testbar ohne Netz/Git): `save_request(root, slug)`,
`mark_ready(root, slug, url)`, `load(root, slug)`, `list_pending(root)`.

### `deploy.py` — Pages-Deploy (analog `mailer.py`, injizierbar)

Nimmt fertiges HTML + slug, schreibt es ins prototyp-Repo und pusht.

- `deploy(slug, html, *, repo_path, pusher=None) -> str` — schreibt `<repo>/<slug>/index.html`,
  ruft den Pusher (git add/commit/push), gibt die Pages-URL zurück.
- Der **Pusher ist injizierbar** (Default: echter git-Aufruf; im Test: Fake, der nichts pusht).
  Gleiches Muster wie `mailer.smtp_factory`.
- URL-Bildung: `https://<user>.github.io/<repo>/<slug>` aus Config.

Konfiguration in `backend/.env` (Vorlage `.env.example` erweitern):
`PROTOTYP_REPO_PATH` (lokaler Pfad zum ausgecheckten prototyp-Repo),
`PROTOTYP_PAGES_BASE` (z.B. `https://shawn-jed.github.io/prototyp`).

### Kein `leadtool`-Eingriff nötig

Der gesamte Prototyp-Zustand lebt im eigenen JSON-Store (wie bei Outreach). Der Sales-Status
des Leads bleibt unberührt — Prototyp ist ein unabhängiges Artefakt, kein Pipeline-Schritt.
`build_state()` in `app.py` reichert die Lead-Sicht um den Prototyp-Status an (liest den Store),
damit das Frontend Schalter/Link zeigen kann.

### API-Endpunkte (`app.py`, analog Outreach)

| Methode | Pfad | Zweck |
|---|---|---|
| POST | `/api/leads/<slug>/prototyp/request` | Schalter „Ja" → Auftrag `pending` anlegen |
| GET  | `/api/prototyp/pending` | offene Aufträge für Claude Code (Liste `{slug}`) |
| POST | `/api/leads/<slug>/prototyp/draft` | Claude schreibt HTML zurück → Backend deployt → `ready` + url |
| GET  | `/api/leads/<slug>/prototyp` | Status/URL fürs Frontend-Polling |

### `.claude/skills/prototyp/SKILL.md` — Claude Code als Demo-Builder

Analog zum `outreach`-Skill:
1. Offene Aufträge holen (`GET /api/prototyp/pending`).
2. Für jeden Auftrag Lead-Kontext lesen (`GET /api/state`, Feld `leads`, passender `slug`):
   `firma`, `schwaeche`, `branche`, `ort`, `ucp`.
3. Maßgeschneiderte One-Pager-`index.html` bauen: adressiert die konkrete Schwäche, spiegelt
   Branche/Ort, moderne responsive Gestaltung, Firmenname/Leistungen plausibel. Keine
   erfundenen Fakten über den Betrieb hinaus, kein externes CDN (self-contained HTML/CSS).
4. Zurückschreiben (`POST /api/leads/<slug>/prototyp/draft` mit `{html}`). Backend deployt.
5. Watch-Modus über `/loop`-Skill möglich (offene Aufträge in kurzem Intervall abgreifen).

### Frontend — Drawer-Block (analog Outreach-Wizard)

Im Lead-Detail-Drawer ein Bereich „🎨 Prototyp":
- Status `none`: Button „Prototyp bauen" → `POST …/prototyp/request`.
- Status `pending`: „Demo wird gebaut…" (pollt `GET …/prototyp`). Ohne laufendes Claude Code
  bleibt der Auftrag `pending` — Hinweistext analog Outreach.
- Status `ready`: Link + Button „Demo öffnen" (öffnet URL im neuen Tab).

### Integration mit Outreach (D)

Ist der Prototyp `ready`, füllt der Outreach-Wizard das bestehende `prototyp`-Feld automatisch
mit `{mode: "link", url}` vor. Minimaler Eingriff im Frontend-Wizard (`openOutreach`), da das
Feld bereits existiert. C speist D, kein Doppeleintrag der URL.

## Deploy-Repo (einmaliges Setup)

- Neues **öffentliches** GitHub-Repo `prototyp` (Shawn-Jed/prototyp), GitHub Pages aktiviert
  (Branch `main`, Root).
- Lokal ausgecheckt; Pfad in `PROTOTYP_REPO_PATH`.
- Getrennt vom privaten LeadGen-Werkzeug-Repo, weil Pages öffentlich sein muss und LeadGen
  Lead-Daten/Schwächen enthält, die nicht öffentlich werden dürfen.

## Fehlerbehandlung

- **Deploy schlägt fehl** (Push-Fehler, Repo-Pfad fehlt): Auftrag bleibt `pending`, Fehler wird
  an Claude Code / ins Cockpit zurückgemeldet (Toast). Kein halb-fertiger `ready`-Zustand.
- **Kein Claude Code aktiv:** Auftrag bleibt `pending`, Cockpit zeigt „wird gebaut…".
- **Config fehlt** (`PROTOTYP_REPO_PATH`/`PROTOTYP_PAGES_BASE`): `/prototyp/draft` gibt einen
  klaren Fehler zurück, statt still zu scheitern.
- **Ungültiges/leeres HTML** vom Draft: Backend lehnt ab (Mindestprüfung: enthält `<html`).

## Recht / Risiko

Die Demo trägt Firmenname/Leistungen des Betriebs und ist öffentlich unter Shawns Pages-URL,
ohne noindex/Hinweis (bewusste Entscheidung für maximalen Effekt). Restrisiko: könnte als
offizielle Firmenseite missverstanden werden oder Markennennung berühren. Kein Blocker für die
Implementierung; Shawn verantwortet den Einsatz pro Lead (wie bei Outreach). Falls sich das
Risiko später als relevant zeigt, ist ein noindex-Flag nachrüstbar.

## Testing

Analog zur Outreach-Testsuite, alle ohne Netz/echten Push:

- `test_prototyp_store.py` — Zustandsübergänge none → pending → ready(+url), `list_pending()`;
  funktioniert für kalte wie warme Leads (Store ist slug-basiert, unabhängig vom Lead-Typ).
- `test_deploy.py` — `deploy()` mit **injiziertem Fake-Pusher**: schreibt Datei an richtigen
  Pfad, bildet korrekte URL, ruft Pusher genau einmal. Kein echter git-Push im Test.
- API-Tests — die vier Endpunkte (request legt pending an; pending listet; draft deployt via
  Fake-Pusher und setzt ready+url; get liefert Status).

## Nicht im Scope (bewusst ausgeklammert)

- Automatische Prototyp-Erzeugung für alle Leads (es bleibt Opt-in).
- Custom Domain / schönere URL (Repo-Name in der URL wird akzeptiert).
- Screenshot/Thumbnail der Demo im Cockpit (nur Link).
- Versionierung/Update einer bereits gebauten Demo (erste Version: einmal bauen; erneutes
  Bauen überschreibt).

## Abhängigkeiten

- Setzt Subsystem D (Outreach) voraus — bereits gebaut und in `main`.
- Einmaliges GitHub-Setup: öffentliches `prototyp`-Repo mit Pages.
- Keine neuen Python-Runtime-Dependencies (git via Subprozess, stdlib).
