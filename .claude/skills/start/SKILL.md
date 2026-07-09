---
name: start
description: Use when starting/launching the LeadGen app locally — Backend + Cockpit-Frontend hochfahren und im Browser öffnen. Trigger: "starte", "start alles", "app starten", "cockpit auf", "leadgen hoch", "server an".
---

# LeadGen starten (Backend + Cockpit)

Fährt das komplette lokale Setup hoch: JSON-API + statisches Frontend aus **einem** Prozess.
`app.py` liefert unter derselben URL auch das Cockpit-Frontend aus — kein zweiter Server nötig.

## Standard-Start (alles in einem)

Aus dem Repo-Root:

```bash
cd backend && python app.py
```

- URL: **http://127.0.0.1:8723** (API **und** Cockpit).
- Läuft im Vordergrund → mit `Strg+C` stoppen.
- In Claude-Sessions als Hintergrundprozess starten (`run_in_background`), damit die Session
  weiterarbeiten kann.

## Nach dem Start prüfen

1. Health-Check: `GET http://127.0.0.1:8723/api/state` liefert 200 + JSON (Leads + Discovery-Runs).
   (`/api/leads` ist POST-only → 404 bei GET ist normal, kein Fehler.)
2. Browser: http://127.0.0.1:8723 öffnen → Cockpit lädt (liefert 200).

## Varianten

- **Anderer Port:** `python app.py --port 9000`
- **Nur API** (Frontend separat, z.B. für Frontend-Entwicklung mit Live-Reload):
  ```bash
  cd backend && python app.py --api-only
  npx serve ../frontend
  ```
  Dann in `frontend/config.js` `window.LEADGEN_API_BASE` auf die API-URL setzen.

## Stoppen

- Vordergrund: `Strg+C`.
- Hintergrund/Windows: Prozess auf Port 8723 beenden —
  `powershell "Get-NetTCPConnection -LocalPort 8723 | Select-Object -Expand OwningProcess | ForEach-Object { Stop-Process -Id $_ -Force }"`

## Wichtig

- **Immer aus `backend/` starten** — die CLIs/API nutzen das aktuelle Verzeichnis als Datenwurzel.
- Bei "Port belegt": Port 8723 ist noch von einem alten Lauf belegt → stoppen (s.o.) oder `--port` nutzen.
