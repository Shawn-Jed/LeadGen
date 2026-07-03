---
name: lead
description: Use when tracking sales leads in this Leads-Repo — Lead anlegen, Status setzen, Notizen, oder das Follow-up-Cockpit (report). Trigger: "neuer Lead", "Status auf X", "wer ist fällig", "lead report".
---

# Lead-Tracking (CRM)

Bediene das datei-basierte Lead-CRM **ausschließlich über die CLI** `python lead.py …`
— **immer aus `backend/` ausführen** (`cd backend`), da die CLI das aktuelle Verzeichnis
als Datenwurzel nutzt. Editiere `pipeline.md` / `leads/*.md` nicht von Hand —
die CLI hält Tabelle, Frontmatter und Graduierung konsistent.

## Kommandos

| Aufgabe | Kommando |
|---------|----------|
| Lead anlegen | `python lead.py neu "Firma GmbH" --schwaeche "keine Mobil-Ansicht"` |
| Status setzen | `python lead.py status <slug> <status>` |
| Notiz anhängen | `python lead.py notiz <slug> "Text"` |
| Follow-up-Report | `python lead.py report` |
| Wiedervorlage setzen | `python lead.py wiedervorlage <slug> <YYYY-MM-DD>` |
| Repo init | `python lead.py init` |

## Status-Pipeline

`identifiziert → analysiert → prototyp_erstellt → kontaktiert → keine_antwort
→ in_klaerung → termin_vereinbart → angebot_raus → gewonnen / verloren / zurückgestellt`

- **kalt** (`pipeline.md`): identifiziert, analysiert, prototyp_erstellt, kontaktiert, keine_antwort, verloren, zurückgestellt
- **warm** (`leads/<slug>.md`): in_klaerung, termin_vereinbart, angebot_raus, gewonnen

## Regeln (die CLI erzwingt sie, du musst sie kennen)

1. **Graduierung:** `status <slug> in_klaerung` (oder höher) legt automatisch `leads/<slug>.md` an
   und entfernt die Zeile aus `pipeline.md`. Ab da lebt der Lead in seiner Datei.
2. **kontaktiert_am-Stempel:** `status <slug> kontaktiert` setzt das heutige Datum als
   `kontaktiert_am` (Basis der 14-Tage-Regel).
3. **14-Tage-Regel:** `report` listet Leads mit `kontaktiert_am` > 14 Tage ohne Antwort →
   schlage dem Nutzer vor, sie auf `keine_antwort` zu setzen. **Setze es nie automatisch.**
4. **gewonnen:** Nach `status <slug> gewonnen` den `## Absprachen`-Abschnitt in `leads/<slug>.md`
   ausfüllen (Umfang, Festpreis, Deadline, Zusagen) — frag den Nutzer nach den Details.
5. **Wiedervorlage:** Datum per `python lead.py wiedervorlage <slug> <YYYY-MM-DD>` setzen — nie von Hand editieren. `report` zeigt fällige.
6. **Warme Leads bleiben warm:** Ein bereits graduierter Lead (eigene Datei) behält seine Datei auch wenn er `verloren` oder `zurückgestellt` wird — die Historie/Absprachen bleiben erhalten. `verloren`/`zurückgestellt` in der Sammeldatei gelten nur für Leads, die *vor* der Graduierung sterben. Wirf eine warme Datei nicht zurück in die Pipeline.

## Routine
Bei Session-Start oder auf Wunsch: `python lead.py report` laufen lassen und offene Follow-ups melden.

## Integration (spätere Subsysteme)
- Discovery (A) ruft `neu` mit vorbefüllter Schwäche.
- Prototyp (C) schreibt nach `prototypes/<slug>/`, setzt Frontmatter `prototyp:`.
- Outreach (D) liest `ucp`/`roi_these`/`prototyp`, entwirft Mail, setzt nach manuellem Versand `status kontaktiert`.
