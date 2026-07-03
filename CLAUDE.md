# LeadGen — Festpreis-Akquise Hamburg (Repo-Router)

Selfwork-Projekt von Shawn: Festpreis-Projekte in Hamburg akquirieren. 5 Subsysteme
(**A Discovery** · **B Tracking** · C Prototyp · D Outreach · E Portfolio). Aktuell gebaut: **A, B, Cockpit**.

## Struktur (Frontend/Backend getrennt)
```
LeadGen/
├─ backend/      Python: JSON-API (app.py) + CLIs + Logik + Daten + Tests
│  ├─ app.py         HTTP-Server / JSON-API (CORS, --api-only)
│  ├─ lead.py        CRM-CLI            → aus backend/ ausführen
│  ├─ discover.py    Discovery-CLI      → aus backend/ ausführen
│  ├─ leadtool.py / discotool.py   Kernlogik (von app.py + CLIs genutzt)
│  ├─ discovery/*.json   Discovery-Runs (Daten)
│  ├─ leads/*.md         warme Leads (Daten)
│  ├─ pipeline.md        kalte Leads (Daten)
│  ├─ templates/         Lead-Vorlage
│  └─ tests/             pytest
├─ frontend/     Vanilla JS/HTML/CSS (kein Build-Step)
│  ├─ index.html · app.js · style.css
│  └─ config.js      window.LEADGEN_API_BASE = Backend-URL
├─ docs/         Specs, Pläne, Screenshots
└─ .claude/      Skills (lead, discover) + Agents
```

**Wichtig:** CLIs (`lead.py`, `discover.py`) nutzen das aktuelle Verzeichnis als Root —
immer aus `backend/` ausführen: `cd backend && python lead.py …`.

## Lokal starten
- Alles in einem: `cd backend && python app.py` → http://127.0.0.1:8723 (liefert auch das Frontend).
- Entkoppelt: `cd backend && python app.py --api-only` + Frontend separat (`npx serve frontend`),
  API-URL in `frontend/config.js` setzen.

## Discovery (Leads finden)
`discover`-Skill (`.claude/skills/discover/SKILL.md`): `cd backend && python discover.py scan "<Branche>" "<Stadtteil>"`,
dann website_unklar-Kandidaten per WebSearch gegenprüfen (`setstatus`), dann `uebernehmen auto`.

## Tracking bedienen
`lead`-Skill (`.claude/skills/lead/SKILL.md`). Alles über `cd backend && python lead.py …`.
Nie `pipeline.md` / `leads/*.md` von Hand editieren.

## Recht (wichtig für D, noch nicht gebaut)
Kein vollautomatischer Mailversand — UWG §7. System bereitet Mail vor, Shawn sendet manuell.

## Specs & Pläne
- Spec B: `docs/superpowers/specs/2026-06-28-lead-tracking-backbone-design.md`
- Plan B: `docs/superpowers/plans/2026-06-28-lead-tracking-backbone.md`
