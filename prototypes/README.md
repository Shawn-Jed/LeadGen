# Prototypen — lokale Demo-One-Pager

Ein Ordner pro Lead, benannt nach dem Lead-**Slug** (identisch zum Backend:
`backend/prototyp/<slug>.json` und Pipeline/CRM). Jeder Ordner enthält die fertige
`index.html` — einfach im Browser öffnen.

**Kein GitHub-Pages-Deploy** — bewusst rein lokal. Zum Zeigen: HTML-Datei direkt
per Doppelklick / `file://` öffnen.

## Übersicht

| Slug (Ordner) | Firma | Branche | Ort | Stand | Öffnen |
|---|---|---|---|---|---|
| `minnemann-elektrotechnik` | Minnemann Elektrotechnik | Elektrotechnik | Kranichweg 11, 22305 HH | erstellt | [index.html](minnemann-elektrotechnik/index.html) |

## Namens-Konvention

- Ordnername = Lead-Slug (kleingeschrieben, Bindestriche), z. B. `minnemann-elektrotechnik`.
- Datei immer `index.html` im Slug-Ordner.
- Neuer Prototyp → neuer Slug-Ordner + Zeile in der Tabelle oben.
