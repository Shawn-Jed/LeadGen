# Discovery A3 (Tier 3) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tier-3-Discovery — qualitatives Claude-Urteil (Design, UX, Mobile, Professionalität) per Playwright-MCP auf der besten Shortlist aus dem A2-Analyse-Lauf. Die Python-Seite (discotool.py / discover.py) wächst minimal: nur Datenpersistierung und CLI. Der Wert liegt im SKILL.

**Architecture:** `set_tier3` und `shortlist` werden an `discotool.py` angehängt. Zwei neue CLI-Subcommands (`shortlist`, `bewerten`) werden an `discover.py` angehängt. Der `discover`-Skill bekommt einen Tier-3-Abschnitt, der den Playwright-MCP-Loop orchestriert. Kein Playwright im Test-Code — Playwright ist ein Laufzeit-Skill-Werkzeug, keine Python-Bibliothek.

**Tech Stack:** Python 3.11+ (stdlib only), pytest. Baut auf den fertigen Funktionen aus A1 (`new_run`, `save_run`, `load_run`, `set_status`) und A2 (`analyse_site`, `score_tier2`, `analyse_run`, `analyse`-CLI-Subcommand) auf. Keine neuen Python-Abhängigkeiten.

**Daten-Shape-Vertrag:** A3 fügt NUR den `"tier3"`-Schlüssel zum Kandidaten-Dict hinzu. Es berührt NIEMALS `score`, `tier2`, `new_run`-Struktur oder `score_tier1`. Der Score bleibt ausschließlich deterministisch — A3-Qualitätsurteile sind qualitativ und werden nicht automatisch in den Opportunity-Score eingerechnet (das bleibt einem späteren Score-Upgrade-Schritt vorbehalten).

---

## Voraussetzungen (A2-API-Kontrakt)

A3 baut auf A2 auf. Die folgenden Symbole müssen in `discotool.py` bereits existieren, bevor dieser Plan ausgeführt wird:

| Symbol | Signatur | Beschreibung |
|---|---|---|
| `analyse_site` | `(url: str, *, fetch_fn) -> dict` | Lädt HTML, extrahiert Tier-2-Heuristiken |
| `score_tier2` | `(cand: dict) -> int` | Berechnet Aufschläge auf Basis der `tier2`-Keys |
| `analyse_run` | `(run: dict, *, fetch_fn) -> None` | Iteriert über `hat_website`-Kandidaten, setzt `status="analysiert"`, `tier2={...}`, erhöht `score` |
| `analyse` | CLI-Subcommand in `discover.py` | `analyse <run>` — ruft `analyse_run`, speichert Run |

Kandidaten-Dict nach A2 (Basis für A3):

```python
{
    "id": int,
    "firma": str,
    "adresse": str,
    "website": str,
    "telefon": str,
    "osm_id": str,
    "status": "analysiert",          # nach analyse_run gesetzt
    "gefundene_url": str,
    "score": int,                    # Tier1 + Tier2-Aufschläge
    "befund": str,
    "lead_angelegt": bool,
    "tier2": {                       # von A2 gesetzt
        "kein_https": bool,
        "kein_viewport": bool,
        "kein_impressum": bool,
        "kein_kontakt": bool,
        "veraltet": bool,
    },
    # "tier3" fehlt noch — A3 fügt ihn hinzu
}
```

---

## File Structure

```
Leads/
├── discotool.py              # APPEND: set_tier3, shortlist
├── discover.py               # APPEND: shortlist + bewerten subcommands
├── tests/
│   ├── test_a3_tier3.py          # Task 1: set_tier3 + shortlist unit tests
│   └── test_a3_cli.py            # Task 2: CLI shortlist + bewerten integration
└── .claude/skills/discover/SKILL.md   # Task 3: Tier-3-Abschnitt hinzufügen
```

Keine neuen Top-Level-Dateien. Kein `conftest.py`-Änderung nötig (Fixture `repo` aus Subsystem B bereits vorhanden).

---

## Task 1: `set_tier3` + `shortlist` (discotool.py)

**Files:** Modify `discotool.py` (append), Create `tests/test_a3_tier3.py`

### Step 1: Failing Test

```python
# tests/test_a3_tier3.py
import pytest
from datetime import date
import discotool


def _make_run() -> dict:
    """Minimal run mit 3 Kandidaten: 2 analysiert (unterschiedliche Scores), 1 website_unklar."""
    cands = [
        {"firma": "Alpha GmbH",   "website": "https://alpha.de",  "adresse": "", "telefon": "", "osm_id": "node/1"},
        {"firma": "Beta KG",      "website": "https://beta.de",   "adresse": "", "telefon": "", "osm_id": "node/2"},
        {"firma": "Gamma e.K.",   "website": "",                  "adresse": "", "telefon": "", "osm_id": "node/3"},
    ]
    run = discotool.new_run("Zahnärzte", "Eimsbüttel", cands, date(2026, 6, 28))
    # Alpha: analysiert, Score 25
    run["kandidaten"][0]["status"] = "analysiert"
    run["kandidaten"][0]["score"]  = 25
    # Beta: analysiert, Score 70
    run["kandidaten"][1]["status"] = "analysiert"
    run["kandidaten"][1]["score"]  = 70
    # Gamma bleibt website_unklar (Score 60 from tier1)
    return run


# --- set_tier3 ---

def test_set_tier3_stores_dict():
    run = _make_run()
    discotool.set_tier3(run, 1, urteil="Veraltetes Design, kein Responsive", empfehlung="lohnt")
    assert run["kandidaten"][0]["tier3"] == {
        "urteil": "Veraltetes Design, kein Responsive",
        "empfehlung": "lohnt",
    }


def test_set_tier3_all_valid_empfehlungen():
    for emp in ("lohnt", "lohnt_nicht", "unklar"):
        run = _make_run()
        discotool.set_tier3(run, 1, urteil="x", empfehlung=emp)
        assert run["kandidaten"][0]["tier3"]["empfehlung"] == emp


def test_set_tier3_invalid_empfehlung_raises():
    run = _make_run()
    with pytest.raises(ValueError, match="empfehlung"):
        discotool.set_tier3(run, 1, urteil="x", empfehlung="gut")


def test_set_tier3_unknown_id_raises():
    run = _make_run()
    with pytest.raises(ValueError, match="99"):
        discotool.set_tier3(run, 99, urteil="x", empfehlung="lohnt")


def test_set_tier3_does_not_touch_score():
    run = _make_run()
    score_before = run["kandidaten"][0]["score"]
    discotool.set_tier3(run, 1, urteil="schöne Seite", empfehlung="lohnt_nicht")
    assert run["kandidaten"][0]["score"] == score_before


def test_set_tier3_does_not_touch_tier2():
    run = _make_run()
    run["kandidaten"][0]["tier2"] = {"kein_https": True}
    discotool.set_tier3(run, 1, urteil="x", empfehlung="unklar")
    assert run["kandidaten"][0]["tier2"] == {"kein_https": True}


# --- shortlist ---

def test_shortlist_returns_only_analysiert():
    run = _make_run()
    sl = discotool.shortlist(run)
    firmen = [c["firma"] for c in sl]
    assert "Gamma e.K." not in firmen   # website_unklar → ausgeschlossen
    assert "Alpha GmbH" in firmen
    assert "Beta KG" in firmen


def test_shortlist_sorted_by_score_desc():
    run = _make_run()
    sl = discotool.shortlist(run)
    scores = [c["score"] for c in sl]
    assert scores == sorted(scores, reverse=True)


def test_shortlist_top_cap():
    """top=1 → nur der Kandidat mit höchstem Score."""
    run = _make_run()
    sl = discotool.shortlist(run, top=1)
    assert len(sl) == 1
    assert sl[0]["firma"] == "Beta KG"   # Score 70 > 25


def test_shortlist_default_top_ten():
    """Mit < 10 analysierten Kandidaten: alle zurückgegeben."""
    run = _make_run()
    sl = discotool.shortlist(run)
    assert len(sl) == 2   # nur 2 analysiert


def test_shortlist_empty_when_none_analysiert():
    cands = [{"firma": "Nur Unklar", "website": "", "adresse": "", "telefon": "", "osm_id": ""}]
    run = discotool.new_run("X", None, cands, date(2026, 6, 28))
    assert discotool.shortlist(run) == []
```

### Step 2: Run → FAIL

```
python -m pytest tests/test_a3_tier3.py -v
```

Expected: FAIL (`has no attribute 'set_tier3'` / `has no attribute 'shortlist'`)

### Step 3: Implement (append to `discotool.py`)

```python
# ---------------------------------------------------------------------------
# A3 — Tier-3-Qualitätsurteil (qualitativ, kein Score-Einfluss)
# ---------------------------------------------------------------------------

_EMPFEHLUNGEN = {"lohnt", "lohnt_nicht", "unklar"}


def set_tier3(run: dict, cand_id: int, *, urteil: str, empfehlung: str) -> None:
    """Speichert das Tier-3-Urteil am Kandidaten.

    Daten-Shape-Kontrakt: setzt NUR candidate["tier3"]. Berührt score, tier2,
    lead_angelegt, status oder andere Keys NICHT.

    Args:
        run:         Run-Dict (mutiert in-place).
        cand_id:     id des Kandidaten (int).
        urteil:      Freitext-Begründung (z.B. "Veraltetes Design, kein Responsive").
        empfehlung:  Einer von: "lohnt" | "lohnt_nicht" | "unklar".

    Raises:
        ValueError: empfehlung nicht im erlaubten Set oder cand_id unbekannt.
    """
    if empfehlung not in _EMPFEHLUNGEN:
        raise ValueError(
            f"Ungültige empfehlung '{empfehlung}'. Erlaubt: {sorted(_EMPFEHLUNGEN)}"
        )
    for c in run["kandidaten"]:
        if c["id"] == cand_id:
            c["tier3"] = {"urteil": urteil, "empfehlung": empfehlung}
            return
    raise ValueError(f"Kandidat id={cand_id} nicht gefunden")


def shortlist(run: dict, *, top: int = 10) -> list[dict]:
    """Gibt die top-N analysierten Kandidaten sortiert nach Score (desc) zurück.

    Nur Kandidaten mit status == "analysiert" werden berücksichtigt.
    Wird vom Skill verwendet, um zu wissen, welche Sites per Playwright beurteilt
    werden sollen.

    Args:
        run: Run-Dict.
        top: Maximale Anzahl Kandidaten (default 10).

    Returns:
        Liste von Kandidaten-Dicts (Referenzen auf das Original, nicht kopiert).
    """
    analysiert = [c for c in run["kandidaten"] if c["status"] == "analysiert"]
    analysiert.sort(key=lambda c: c["score"], reverse=True)
    return analysiert[:top]
```

### Step 4: Run → PASS

```
python -m pytest tests/test_a3_tier3.py -v
```

Expected: 11 passed

### Step 5: Volle Suite (kein Regressionstest gebrochen)

```
python -m pytest -q
```

Expected: alle bisherigen Tests grün + 11 neue.

### Step 6: Commit

```bash
git add discotool.py tests/test_a3_tier3.py
git commit -m "feat(disco): set_tier3 + shortlist (A3 Tier-3-Datenpersistierung)"
```

---

## Task 2: CLI `shortlist` + `bewerten` (discover.py)

**Files:** Modify `discover.py` (append subcommands), Create `tests/test_a3_cli.py`

### Step 1: Failing Test

```python
# tests/test_a3_cli.py
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import discover   # noqa: E402
import discotool  # noqa: E402


def _build_run_with_analysiert(repo: Path) -> Path:
    """Erstellt einen gespeicherten Run mit 3 Kandidaten (2 analysiert, 1 unklar)."""
    cands = [
        {"firma": "Alpha GmbH",  "website": "https://alpha.de", "adresse": "Weg 1", "telefon": "", "osm_id": "node/1"},
        {"firma": "Beta KG",     "website": "https://beta.de",  "adresse": "Weg 2", "telefon": "", "osm_id": "node/2"},
        {"firma": "Gamma e.K.",  "website": "",                 "adresse": "Weg 3", "telefon": "", "osm_id": "node/3"},
    ]
    run = discotool.new_run("Zahnärzte", "Eimsbüttel", cands, date(2026, 6, 28))
    run["kandidaten"][0]["status"] = "analysiert"
    run["kandidaten"][0]["score"]  = 25
    run["kandidaten"][1]["status"] = "analysiert"
    run["kandidaten"][1]["score"]  = 70
    path = discotool.run_path(repo, "Zahnärzte", "Eimsbüttel", date(2026, 6, 28))
    discotool.save_run(path, run)
    return path


# --- shortlist CLI ---

def test_cli_shortlist_prints_analysiert_sorted(repo, capsys, monkeypatch):
    monkeypatch.chdir(repo)
    path = _build_run_with_analysiert(repo)

    rc = discover.main(["shortlist", str(path)])
    assert rc == 0

    out = capsys.readouterr().out
    # Beta KG (Score 70) muss vor Alpha GmbH (Score 25) erscheinen
    assert out.index("Beta KG") < out.index("Alpha GmbH")
    # Gamma (website_unklar) darf nicht erscheinen
    assert "Gamma" not in out


def test_cli_shortlist_top_flag(repo, capsys, monkeypatch):
    monkeypatch.chdir(repo)
    path = _build_run_with_analysiert(repo)

    rc = discover.main(["shortlist", str(path), "--top", "1"])
    assert rc == 0

    out = capsys.readouterr().out
    assert "Beta KG" in out
    assert "Alpha GmbH" not in out


def test_cli_shortlist_missing_run_returns_error(repo, capsys, monkeypatch):
    monkeypatch.chdir(repo)
    rc = discover.main(["shortlist", str(repo / "discovery" / "nonexistent.json")])
    assert rc == 1


# --- bewerten CLI ---

def test_cli_bewerten_stores_tier3(repo, capsys, monkeypatch):
    monkeypatch.chdir(repo)
    path = _build_run_with_analysiert(repo)

    rc = discover.main([
        "bewerten", str(path), "2", "lohnt",
        "Veraltetes Design, kein responsives Layout"
    ])
    assert rc == 0

    run = discotool.load_run(path)
    beta = next(c for c in run["kandidaten"] if c["id"] == 2)
    assert beta["tier3"]["empfehlung"] == "lohnt"
    assert beta["tier3"]["urteil"] == "Veraltetes Design, kein responsives Layout"


def test_cli_bewerten_does_not_change_score(repo, monkeypatch):
    monkeypatch.chdir(repo)
    path = _build_run_with_analysiert(repo)
    run_before = discotool.load_run(path)
    score_before = next(c["score"] for c in run_before["kandidaten"] if c["id"] == 2)

    discover.main([
        "bewerten", str(path), "2", "lohnt_nicht", "Modernes, sauberes Design"
    ])

    run_after = discotool.load_run(path)
    score_after = next(c["score"] for c in run_after["kandidaten"] if c["id"] == 2)
    assert score_after == score_before


def test_cli_bewerten_bad_empfehlung_returns_rc1(repo, capsys, monkeypatch):
    monkeypatch.chdir(repo)
    path = _build_run_with_analysiert(repo)

    rc = discover.main(["bewerten", str(path), "1", "super", "tolles Design"])
    assert rc == 1


def test_cli_bewerten_unknown_id_returns_rc1(repo, capsys, monkeypatch):
    monkeypatch.chdir(repo)
    path = _build_run_with_analysiert(repo)

    rc = discover.main(["bewerten", str(path), "99", "lohnt", "egal"])
    assert rc == 1


def test_cli_bewerten_prints_confirmation(repo, capsys, monkeypatch):
    monkeypatch.chdir(repo)
    path = _build_run_with_analysiert(repo)

    discover.main(["bewerten", str(path), "1", "unklar", "Gemischter Eindruck"])
    out = capsys.readouterr().out
    assert "Alpha GmbH" in out or "1" in out   # Bestätigung enthält id oder Firmenname
```

### Step 2: Run → FAIL

```
python -m pytest tests/test_a3_cli.py -v
```

Expected: FAIL (`error: argument cmd: invalid choice: 'shortlist'`)

### Step 3: Implement (append subparsers + handlers to `discover.py`)

In `discover.py` — füge die neuen Subparser im `main`-Body nach dem `uebernehmen`-Parser ein, und die Handler im `try`-Block:

**Subparser-Ergänzung** (nach dem `pu`-Block, vor `args = p.parse_args(argv)`):

```python
    psl = sub.add_parser("shortlist", help="Top-N analysierte Kandidaten für Tier-3-Bewertung")
    psl.add_argument("run")
    psl.add_argument("--top", type=int, default=10)
    psl.add_argument("--today", default=None)

    pbw = sub.add_parser("bewerten", help="Tier-3-Urteil per Playwright eintragen")
    pbw.add_argument("run")
    pbw.add_argument("id", type=int)
    pbw.add_argument("empfehlung", choices=["lohnt", "lohnt_nicht", "unklar"])
    pbw.add_argument("urteil")
    pbw.add_argument("--today", default=None)
```

**Handler-Ergänzung** (im `try`-Block, nach dem `uebernehmen`-Branch):

```python
        elif args.cmd == "shortlist":
            run = discotool.load_run(Path(args.run))
            sl = discotool.shortlist(run, top=args.top)
            if not sl:
                print("Keine analysierten Kandidaten in diesem Run.")
            else:
                print(f"Shortlist ({len(sl)} Kandidaten, sortiert nach Score desc):")
                for c in sl:
                    url = c.get("gefundene_url") or c.get("website") or "—"
                    t3 = "✓bewertet" if "tier3" in c else ""
                    print(f"  [{c['id']}] {c['firma']}  Score={c['score']}  {url}  {t3}")
        elif args.cmd == "bewerten":
            path = Path(args.run)
            run = discotool.load_run(path)
            discotool.set_tier3(run, args.id, urteil=args.urteil, empfehlung=args.empfehlung)
            discotool.save_run(path, run)
            cand = next(c for c in run["kandidaten"] if c["id"] == args.id)
            print(f"Tier-3 gespeichert: [{args.id}] {cand['firma']} → {args.empfehlung}")
```

**Wichtig:** Die `choices`-Einschränkung im `bewerten`-Subparser fängt ungültige `empfehlung`-Werte schon beim Parsen ab (argparse gibt rc 2 zurück). `set_tier3` wirft zusätzlich `ValueError` für Konsistenz. Beide Fehler fallen in den bestehenden `except (ValueError, FileNotFoundError)` — aber argparse bricht früher ab. Der Test `test_cli_bewerten_bad_empfehlung_returns_rc1` erwartet `rc == 1`; argparse liefert bei `SystemExit(2)`. Lösung: `parse_args` in `try/except SystemExit` wrappen:

```python
    try:
        args = p.parse_args(argv)
    except SystemExit as e:
        return int(e.code) if e.code is not None else 1
```

Ersetze die bestehende Zeile `args = p.parse_args(argv)` durch diesen Block.

### Step 4: Run → PASS

```
python -m pytest tests/test_a3_cli.py -v
```

Expected: 8 passed

### Step 5: Volle Suite

```
python -m pytest -q
```

Expected: alle bisherigen Tests grün + 8 neue.

### Step 6: Commit

```bash
git add discover.py tests/test_a3_cli.py
git commit -m "feat(disco): CLI shortlist + bewerten (Tier-3-Subcommands)"
```

---

## Task 3: `discover`-Skill — Tier-3-Abschnitt

**Files:** Modify `.claude/skills/discover/SKILL.md`

Kein Test möglich (Skill-Dokumentation, nicht deterministischer Code). Kein `- [ ] Step 2: Run → FAIL`.

### Step 1: Extend `.claude/skills/discover/SKILL.md`

Füge nach dem bestehenden Abschnitt `## Integration` den folgenden Block ein:

````markdown
---

## Tier 3 — Qualitätsurteil per Playwright (A3)

Bewerte die vielversprechendsten analysierten Kandidaten qualitativ. Tier 3 läuft NACH A2
(`analyse`-Subcommand). Playwright wird direkt als MCP-Tool im Skill benutzt —
kein Python-Code für den Browser-Aufruf.

### Ablauf

1. **Shortlist holen:**
   ```
   python discover.py shortlist <run-datei>
   ```
   Gibt die top-10 analysierten Kandidaten sortiert nach Score (desc) aus.
   Optional: `--top 5` für eine engere Auswahl.
   Kandidaten ohne Status `analysiert` tauchen hier nie auf.

2. **Für jeden Kandidaten — Browser-Urteil:**
   Für jede Website auf der Shortlist:
   - `browser_navigate` zur URL des Kandidaten.
   - `browser_take_screenshot` — visueller Ersteindruck.
   - Optional `browser_snapshot` für DOM-Struktur (z.B. bei unklarer Responsiveness).
   Beurteile nach diesen Dimensionen:
   - **Design-Qualität:** Farben, Typografie, Layout — wirkt es professionell oder veraltet?
   - **Mobile / Responsiveness:** Navigiere auf 375 px Breite (`browser_resize`), prüfe ob
     Layout bricht. Fehlt Viewport-Meta (aus A2 bekannt) → wahrscheinlich nicht responsiv.
   - **UX / Klarheit:** Ist das Angebot sofort verständlich? Gibt es CTA/Kontakt-Weg?
   - **Professionalität:** Passt die Seite zur Branche? Wirkt sie vertrauenswürdig?

3. **Urteil eintragen:**
   ```
   python discover.py bewerten <run-datei> <id> <lohnt|lohnt_nicht|unklar> "<kurzes Urteil>"
   ```
   Beispiele:
   ```
   python discover.py bewerten discovery/2026-06-28-zahnaerzte-eimsbuettel.json 3 lohnt \
     "Veraltetes Design, kein Responsive, kein CTA — klare Schwäche"
   python discover.py bewerten discovery/2026-06-28-zahnaerzte-eimsbuettel.json 7 lohnt_nicht \
     "Modernes, responsives Design — kein offensichtlicher Bedarf"
   python discover.py bewerten discovery/2026-06-28-zahnaerzte-eimsbuettel.json 5 unklar \
     "Design veraltet, aber Praxis-Typ unklar — nochmal prüfen"
   ```

4. **Entscheidung:** Nach der Tier-3-Runde:
   - `lohnt`-Kandidaten mit ausreichendem Score → `python discover.py uebernehmen <run> <id,id,...>`
   - `lohnt_nicht`-Kandidaten → nicht übernehmen (bleiben im Run als Archiv).
   - `unklar`-Kandidaten → nochmals kurz recherchieren oder mit niedrigerer Priorität übernehmen.

### Faustregeln fürs Urteilen

- **Fokus auf Geschäftsschaden:** Nicht jede hässliche Seite ist ein Lead. Frag dich:
  würde der Betrieb mit einer besseren Seite mehr Kunden gewinnen?
- **Score als Orientierung, nicht als Wahrheit:** Ein hoher Tier-2-Score (kein HTTPS, kein
  Viewport, kein Impressum) bedeutet strukturell viele Mängel — Tier 3 prüft, ob es sich
  visuell/inhaltlich bestätigt.
- **Sei fair:** Nicht jeder Klempner braucht eine Hochglanz-Site. Urteile branchenrelativ.
- **Branchenportal ≠ eigene Website:** Auch hier gilt: wer nur auf meinestadt.de oder
  gelbeseiten.de zu finden ist, hat keine eigene Website.

### Ehrliche Grenzen

- Playwright ist langsam und manuell — beurteile die **Shortlist**, nicht alle Kandidaten.
  Standardmäßig top-10; bei großen Runs ggf. `--top 5`.
- Screenshots zeigen den aktuellen Stand — einige Seiten laden dynamisch und sehen
  im Screenshot anders aus als im Browser. Im Zweifel: `browser_snapshot` für DOM-Analyse.
- Das Tier-3-Urteil wird **nicht** automatisch in den Opportunity-Score eingerechnet
  (Score bleibt deterministisch aus Tier 1 + Tier 2). Das Urteil ist ein qualitativer
  Hinweis, keine harte Metrik.

### Integration mit `uebernehmen`

Tier 3 ergänzt die Entscheidung für `uebernehmen` — Kandidaten mit `tier3.empfehlung == "lohnt"`
sind gute Übernahmekandidaten, auch wenn ihr Score nicht automatisch hoch genug für
`uebernehmen auto` wäre. Explizit übernehmen mit: `python discover.py uebernehmen <run> <ids>`.
````

### Step 2: Commit

```bash
git add .claude/skills/discover/SKILL.md
git commit -m "docs(disco): discover-Skill Tier-3-Abschnitt (A3 Playwright-Loop)"
```

---

## Self-Review (vom Plan-Autor)

**Spec-Abdeckung (A3):**

| Anforderung | Task |
|---|---|
| `set_tier3(run, cand_id, *, urteil, empfehlung)` — speichert `tier3`-Dict | Task 1 ✓ |
| Validierung `empfehlung` in `{"lohnt", "lohnt_nicht", "unklar"}` → ValueError | Task 1 ✓ |
| ValueError bei unbekannter `cand_id` | Task 1 ✓ |
| `set_tier3` berührt `score` NICHT | Task 1 ✓ (expliziter Test) |
| `shortlist(run, *, top=10)` — nur `analysiert`, sortiert desc | Task 1 ✓ |
| `shortlist` respektiert `top`-Cap | Task 1 ✓ |
| CLI `shortlist <run> [--top N]` | Task 2 ✓ |
| CLI `bewerten <run> <id> <empfehlung> <urteil>` | Task 2 ✓ |
| Schlechte `empfehlung` → rc 1 | Task 2 ✓ |
| Unbekannte `id` → rc 1 | Task 2 ✓ |
| Run-JSON bekommt nach `bewerten` korrekt `tier3`-Dict | Task 2 ✓ |
| `bewerten` ändert Score nicht (gespeicherte Datei) | Task 2 ✓ |
| SKILL.md Tier-3-Loop (browser_navigate / screenshot / bewerten) | Task 3 ✓ |
| SKILL.md ehrliche Grenzen (Playwright langsam, Score unverändert) | Task 3 ✓ |
| Kein Playwright im Test-Code | alle Tasks ✓ |
| Kein Netz-Call im Test | alle Tasks ✓ |

**Daten-Shape-Kontrakt:**
A3 fügt NUR `candidate["tier3"] = {"urteil": str, "empfehlung": str}` hinzu.
`score`, `tier2`, `status`, `lead_angelegt`, `new_run`-Struktur: unberührt. ✓

**Platzhalter-Scan:** keine TODO/TBD; jeder Code-Step vollständig. ✓

**Typ-/Namens-Konsistenz:**
- `set_tier3(run, cand_id, *, urteil, empfehlung)` — Keyword-only urteil/empfehlung verhindert Reihenfolge-Fehler. ✓
- `shortlist(run, *, top=10) -> list[dict]` — gibt Referenzen zurück (kein deepcopy nötig, da nur lesend genutzt vom Skill). ✓
- CLI: `empfehlung` als positionales Argument vor `urteil` (spiegelt `set_tier3`-Signatur). ✓
- `--top`/`top` konsistent zwischen CLI und Funktion. ✓

**argparse-`SystemExit`-Falle:**
`choices`-Validierung in argparse wirft `SystemExit(2)`, nicht `ValueError`. Der Plan löst das
explizit durch `try/except SystemExit` um `parse_args` — dadurch landen schlechte `empfehlung`-Werte
korrekt bei rc 1 statt rc 2, was die Tests erwarten. ✓

**Offene Punkte (bewusst A3-Scope):**
- Score-Upgrade auf Basis von `tier3.empfehlung` bleibt einem späteren Schritt vorbehalten
  (eigener Plan `score_tier3`). A3 ist explizit qualitativ ohne Score-Wirkung.
- `shortlist` liefert Referenzen auf Original-Dicts — Mutationen während des Skills
  (z.B. via `set_tier3`) wirken direkt. Das ist gewollt: kein Roundtrip über Datei nötig
  für den interaktiven Skill-Loop; `save_run` bleibt explizit am Ende.
