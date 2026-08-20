# Prototypen — Demo-One-Pager (lokal + live)

Ein Ordner pro Lead, benannt nach dem Lead-**Slug** (identisch zum Backend:
`backend/prototyp/<slug>.json` und Pipeline/CRM). Jeder Ordner enthält:

- `index.html` — die fertige Demo (self-contained, im Browser öffenbar)
- `info.md` — Infos zum Lead + **Live-Link** zur GitHub-Pages-Fassung

**GitHub-Pages-Hosting ist Standard:** Jede freigegebene Demo wird direkt ins Pages-Repo
deployt (`shawn-jed.github.io/prototyp/<slug>/`) und der lokale Ordner hier mit HTML-Kopie +
`info.md` (inkl. Live-Link) angelegt. Der Ordner entsteht automatisch beim `publish`
(Backend-Handler `/api/leads/<slug>/prototyp/publish`).

## Übersicht

| Slug (Ordner) | Firma | Branche | Ort | Live |
|---|---|---|---|---|
| `minnemann-elektrotechnik` | Minnemann Elektrotechnik | Elektrotechnik | Kranichweg 11, 22305 HH | [live](https://shawn-jed.github.io/prototyp/minnemann-elektrotechnik/) · [lokal](minnemann-elektrotechnik/index.html) |
| `ambulanter-betreuungsdienst` | Ambulanter Betreuungsdienst Düwel | Pflegedienst | Krohnskamp 13, 22301 HH | [live](https://shawn-jed.github.io/prototyp/ambulanter-betreuungsdienst/) · [lokal](ambulanter-betreuungsdienst/index.html) |

## Namens-Konvention

- Ordnername = Lead-Slug (kleingeschrieben, Bindestriche), z. B. `minnemann-elektrotechnik`.
- Dateien immer `index.html` + `info.md` im Slug-Ordner.
- Neuer Prototyp → Ordner + `info.md` entstehen beim `publish`; Zeile hier oben ergänzen.
