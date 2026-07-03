---
name: outreach
description: Use when drafting acquisition emails for leads in LeadGen — offene Outreach-Aufträge aus dem Cockpit abgreifen, personalisierte Mail entwerfen, zur Vorschau zurückschreiben. Trigger: "Outreach-Aufträge", "Lead anschreiben entwerfen", "outreach draften".
---

# Outreach — Mail-Entwurf (Subsystem D)

Das Cockpit legt bei „Lead anschreiben" einen Auftrag ab. **Du** (Claude Code) entwirfst die
Mail. Der Versand passiert erst nach Bildschirm-Freigabe durch den Nutzer im Cockpit.

## Voraussetzung
Backend läuft (`cd backend && python app.py`). Basis-URL `http://127.0.0.1:8723`.

## Ablauf
1. **Offene Aufträge holen:** `GET /api/outreach/pending` → Liste mit `slug` + `request`.
2. **Für jeden Auftrag Lead-Kontext lesen:** Lead-Detail aus `GET /api/state` (Feld `leads`,
   passenden `slug`): `firma`, `schwaeche`, `ucp`, `roi_these`, `prototyp`, `branche`, `ort`.
3. **Mail entwerfen** aus Lead-Kontext + `request` (angebot, nutzen, ton, cta, prototyp, betreff):
   - Betreff: knapp, konkret, kein Clickbait. Falls `request.betreff` gesetzt: übernehmen/verfeinern.
   - Text: persönliche Anrede, Bezug auf die konkrete Schwäche des Betriebs, das Angebot, den
     Nutzen, ein klarer Call-to-Action. Ton laut `request.ton`.
   - Prototyp: bei `request.prototyp.mode == "link"` die URL natürlich einbetten. Bei `"anhang"`
     im Text auf den Anhang verweisen (das Backend hängt die Datei an). Bei `"keiner"` weglassen.
   - Kein erfundener Fakt. Keine Versprechen, die nicht im `request` stehen.
4. **Entwurf zurückschreiben:** `POST /api/leads/<slug>/outreach/draft` mit `{"betreff","text"}`.
   Danach ist der Auftrag `ready` und erscheint im Cockpit als Vorschau.

## Watch-Modus (nahtlos)
Für sofortige Entwürfe: mit dem `/loop`-Skill diese Anleitung in kurzem Intervall laufen lassen
(offene Aufträge abgreifen → entwerfen → zurückschreiben). Ohne laufendes Claude Code bleibt der
Auftrag `pending`; das Cockpit zeigt „Entwurf wird vorbereitet…".

## Grenzen
- Du sendest nie selbst — Versand nur über die Cockpit-Freigabe (`/send`).
- Recht (UWG §7): der Nutzer verantwortet, ob der Betrieb kalt angemailt werden darf.
