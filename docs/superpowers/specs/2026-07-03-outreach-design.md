# Spec: Subsystem D — Outreach (Lead anschreiben)

**Datum:** 2026-07-03
**Status:** Design freigegeben, bereit für Implementierungsplan
**Kontext:** LeadGen (Akquise-Cockpit Hamburg). Subsystem D baut auf B (Tracking) auf.

## Ziel

Aus dem Lead-Detail heraus per Klick eine individuelle Akquise-Mail erstellen: ein
Wizard erfasst Angebot/Prototyp/Ton, **Claude Code** (nicht eine Server-seitige LLM-API)
entwirft die Mail, der Nutzer prüft eine Vorschau und gibt jede Mail einzeln frei, danach
sendet das Backend direkt per SMTP und protokolliert den Kontakt am Lead.

## Grundentscheidungen (aus dem Brainstorming)

| Frage | Entscheidung |
|-------|--------------|
| Versand | **Direktversand** nach Bildschirm-Freigabe (nicht nur Entwurf) |
| Empfänger-E-Mail | **Feld im Lead-Detail** (`kontakt.email`); Button aus, wenn leer |
| Sendetechnik | **SMTP mit App-Passwort** (Creds in `.env`, nicht ins Git) |
| Wo läuft es | **UI im Browser**, aber **Claude Code ist das Hirn** — kein Anthropic-API-Key im Backend |
| Prototyp | **Beides wählbar** pro Mail: keiner / Link im Text / Datei-Anhang |
| Architektur-Ansatz | **Ansatz 1**: Browser stellt Auftrag → Claude Code entwirft → Browser pollt Vorschau → SMTP |

## Rechtlicher Rahmen (UWG §7)

- Der Direktversand ist eine **bewusste Abweichung** von der bisher dokumentierten Regel
  („System bereitet vor, Shawn sendet manuell"). Diese Spec ersetzt die Regel für LeadGen.
- **Schutzmechanismus:** Pro-Mail-Freigabe („Ja, senden") ist Pflicht — es gibt **keinen
  Stapelversand**. Jede Mail wird einzeln in der Vorschau bestätigt.
- **Config-Schalter** `OUTREACH_SEND_MODE` (Default `draft`): Direktversand muss bewusst per
  `direct` aktiviert werden.
- Die Einwilligungs-/Kaltakquise-Frage („darf dieser Betrieb überhaupt kalt angemailt werden?")
  bleibt in der Verantwortung des Nutzers; das System trifft diese Entscheidung nicht.

## Nutzer-Flow

1. **Lead-Detail** (bestehender Drawer) zeigt oben einen **„Was fehlt"-Block**: leere
   Pflichtinfos (E-Mail, Website, Telefon, Prototyp, Angebot/UCP). Fehlende E-Mail rot.
2. **E-Mail-Feld** im Detail editierbar → speichert in `kontakt.email`.
3. Button **„✉ Lead anschreiben"** — deaktiviert ohne E-Mail (Tooltip „E-Mail zuerst eintragen").
4. Klick → **Wizard** (Modal), Felder vorbefüllt aus dem Lead (Schwäche, UCP, ROI, Prototyp):
   - Angebot/Leistung · Nutzen (ROI-These) · Prototyp (keiner / Link / Anhang) ·
     Ton (Sie förmlich … locker) · Call-to-Action · Betreff (auto-generiert, editierbar)
5. **„Entwurf erstellen"** → Wartephase („Claude Code schreibt…").
6. **Vorschau-Maske:** An / Betreff / Text / ggf. Anhang. Buttons **„Ja, senden"** / „Ändern" /
   „Abbrechen".
7. „Ja, senden" → **gesendet** (SMTP), Toast, Status → `kontaktiert`, Historie-Eintrag.

## Komponenten & Zuständigkeiten

| Komponente | Ort | Aufgabe |
|-----------|-----|---------|
| „Was fehlt"-Block + E-Mail-Feld + Button | `frontend/app.js` (Drawer), `style.css` | Anzeige, E-Mail speichern, Wizard öffnen |
| Outreach-Wizard + Vorschau-Maske | `frontend/app.js`, `style.css` | Fragen erfassen, Entwurf zeigen, freigeben |
| Outreach-API | `backend/app.py` | Auftrag annehmen, Zustand liefern, senden |
| Outreach-Zustand | `backend/outreach/<slug>.json` | `request` + `draft` + `status` (`pending`→`ready`→`sent`) |
| Mailer | `backend/mailer.py` (neu) | SMTP-Versand (Link im Text + optional MIME-Anhang), injizierbar |
| outreach-Skill | `.claude/skills/outreach/SKILL.md` (neu) | Claude Code liest Lead+Auftrag, entwirft, postet zurück |
| Lifecycle | `backend/leadtool.py` | nach Versand: `set_status(kontaktiert)` + Historie-Eintrag |

## Datenfluss (Brücke Browser ↔ Claude Code)

```
Browser Wizard
   │ POST /api/leads/<slug>/outreach/request  {angebot, nutzen, prototyp, ton, cta, betreff}
   ▼
outreach/<slug>.json  { status: "pending", request: {…} }
   │                         ▲ (2) Draft zurückschreiben
   │ (1) sieht offene        │ POST /api/leads/<slug>/outreach/draft  {betreff, text}
   ▼ Aufträge                │
Claude Code (outreach-Skill + Watch-Schleife)  ──entwirft Betreff+Text──┘
   │
outreach/<slug>.json  { status: "ready", request:{…}, draft:{betreff, text} }
   ▲ GET /api/leads/<slug>/outreach  (Browser pollt) → Vorschau
   │
Browser „Ja, senden"
   │ POST /api/leads/<slug>/outreach/send
   ▼
mailer.py → SMTP  →  status:"sent"  +  leadtool: kontaktiert + Historie
```

### API-Endpunkte

| Methode | Pfad | Zweck |
|---------|------|-------|
| `POST` | `/api/leads/<slug>/outreach/request` | Wizard-Antworten annehmen, `status=pending` |
| `GET` | `/api/outreach/pending` | Offene Aufträge (für Claude Code) |
| `POST` | `/api/leads/<slug>/outreach/draft` | Entwurf (Betreff/Text) zurückschreiben, `status=ready` |
| `GET` | `/api/leads/<slug>/outreach` | Aktuellen Zustand + Entwurf liefern (Browser pollt) |
| `POST` | `/api/leads/<slug>/outreach/send` | Per SMTP senden, `status=sent`, Lead `kontaktiert` + Historie |
| `POST` | `/api/leads/<slug>/email` | E-Mail-Feld (`kontakt.email`) setzen (aus dem Detail) |

### Watcher

Claude Code lässt während der Arbeit eine leichte Poll-Schleife (`/loop`) laufen, die offene
Aufträge sofort entwirft → Vorschau erscheint in Sekunden. Läuft Claude Code nicht, bleibt der
Auftrag `pending`; der Browser zeigt „Entwurf wird vorbereitet…".

## Fehlerbehandlung & Konfiguration

- **`.env`** (in `.gitignore`): `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`.
  Kein Anthropic-Key nötig.
- **`OUTREACH_SEND_MODE`** = `direct` | `draft` (Default `draft`). `draft` legt eine lokale
  `.eml`-Datei an statt zu senden — sicheres Testen/Fallback.
- **SMTP-Fehler** → Vorschau zeigt Fehler, Status bleibt `ready` (kein `kontaktiert`), erneut versuchbar.
- **Fehlende E-Mail** → Button deaktiviert.
- **Doppelversand** → bei `status=sent` zeigt der Button „bereits gesendet am <Datum>".
- **Pfad-/Eingabevalidierung** analog zu bestehenden Handlern (Traversal-Schutz für `<slug>`,
  Pflichtfelder → 400).

## Tests (Repo-Stil: injizierbar, deterministisch, tmp-Repo)

- `mailer.py` mit injiziertem SMTP-Client: korrekte MIME-Erzeugung (Text + Link; optional
  Datei-Anhang), kein echter Versand im Test.
- Outreach-Zustandsübergänge `pending → ready → sent`; Endpunkt-Validierung (fehlende Felder → 400).
- Nach `send`: Lead-Status = `kontaktiert`, `kontaktiert_am` gestempelt, Historie-Zeile vorhanden.
- `draft`-Modus schreibt `.eml` statt zu senden.
- E-Mail-Feld-Endpunkt setzt `kontakt.email` (warm) korrekt.

## Nicht in Scope (YAGNI)

- Kein Stapel-/Serienversand, keine Sequenzen/Follow-up-Automatik.
- Keine Empfänger-Recherche (E-Mail wird vom Nutzer eingetragen).
- Keine Server-seitige LLM-Integration (Claude Code ist das Hirn).
- Keine Tracking-Pixel / Öffnungsraten.

## Entscheidung: kalte vs. warme Leads

Nur **warme Leads** speichern `kontakt.email` (im Frontmatter). Kalte Leads (`pipeline.md`)
haben kein E-Mail-Feld — das bleibt so (YAGNI, keine neue Tabellenspalte).

**Festlegung:** „Lead anschreiben" ist für Leads mit E-Mail, also **warme Leads**, verfügbar.
Bei einem **kalten** Lead zeigt der „Was fehlt"-Block statt des E-Mail-Felds den Hinweis
**„Lead erst qualifizieren (Status ≥ in_klaerung), dann anschreiben"** — Graduierung legt das
`kontakt.email`-Feld an, das dann befüllt wird. Der `POST /api/leads/<slug>/email`-Endpunkt
wirkt entsprechend nur auf warme Leads (sonst 400 mit klarer Meldung).
