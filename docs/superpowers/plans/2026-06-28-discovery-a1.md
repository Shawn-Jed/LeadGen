# Discovery A1 (Tier 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tier-1-Discovery — Hamburger Betriebe einer Branche per Overpass holen, „keine Website"-Kandidaten markieren, und nach WebSearch-Bestätigung (Claude) automatisch als Leads in Subsystem B anlegen.

**Architecture:** Deterministische Mechanik in `discotool.py` (Overpass-Query, Parsing, Score, Run-Dateien, Lead-Anlage über `import leadtool`), CLI `discover.py`, Orchestrierung der Urteils-Schritte im `discover`-Skill. Overpass-HTTP ist injizierbar (`fetch_fn`) → Tests laufen ohne Netz. Keine neuen Python-Abhängigkeiten (stdlib `urllib`/`json`).

**Tech Stack:** Python 3.11+ (stdlib only), pytest. Dockt an das fertige `leadtool` (Subsystem B) an.

---

## File Structure

```
Leads/
├── discotool.py              # Kern: branche_to_tags, build_overpass_query, fetch_overpass,
│                             #        parse_elements, score_tier1, new_run, run io, set_status, create_leads
├── discover.py               # CLI: scan / show / setstatus / uebernehmen
├── discovery/.gitkeep        # Run-Dateien landen hier
├── tests/
│   ├── test_disco_branche.py     # Task 1
│   ├── test_disco_query.py       # Task 2
│   ├── test_disco_parse.py       # Task 3
│   ├── test_disco_run.py         # Task 4
│   ├── test_disco_leads.py       # Task 5
│   ├── test_disco_fetch.py       # Task 6
│   └── test_discover_cli.py      # Task 7
├── .claude/skills/discover/SKILL.md   # Task 8
└── CLAUDE.md                          # Task 8 (Hinweis auf discover-Skill ergänzen)
```

`discotool.py` importiert `leadtool` (kein Zyklus — leadtool kennt discotool nicht).
Die `repo`-Fixture aus `tests/conftest.py` (Subsystem B) liefert ein lead-fähiges tmp-Repo;
`save_run` legt `discovery/` selbst an (`mkdir parents=True`), daher keine conftest-Änderung nötig.

---

## Task 1: branche_to_tags

**Files:** Create `discotool.py`, `tests/test_disco_branche.py`

- [ ] **Step 1: Failing Test**

```python
import discotool


def test_known_branche_returns_tags():
    assert discotool.branche_to_tags("Zahnärzte") == ["amenity=dentist"]
    assert discotool.branche_to_tags("friseur") == ["shop=hairdresser"]
    assert discotool.branche_to_tags("Kanzlei") == ["office=lawyer"]


def test_unknown_branche_raises_with_hint():
    try:
        discotool.branche_to_tags("Raumschiffbauer")
        assert False
    except ValueError as e:
        assert "Raumschiffbauer" in str(e)
```

- [ ] **Step 2: Run → FAIL**

Run: `python -m pytest tests/test_disco_branche.py -v`
Expected: FAIL (`No module named 'discotool'`)

- [ ] **Step 3: Implement — create `discotool.py`**

```python
"""Lead-Discovery-Kern (Tier 1): Overpass-Abfrage, Parsing, Score, Run-Dateien, Lead-Anlage.
Deterministisch; Overpass-HTTP ist injizierbar. today wird injiziert."""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import leadtool

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Deutsches Branchenwort (normalisiert) → OSM-Tags. Erweiterbar.
BRANCHE_TAGS: dict[str, list[str]] = {
    "zahnarzt": ["amenity=dentist"], "zahnaerzte": ["amenity=dentist"],
    "arzt": ["amenity=doctors"], "aerzte": ["amenity=doctors"], "hausarzt": ["amenity=doctors"],
    "friseur": ["shop=hairdresser"], "friseure": ["shop=hairdresser"],
    "baeckerei": ["shop=bakery"], "baecker": ["shop=bakery"],
    "restaurant": ["amenity=restaurant"], "gastronomie": ["amenity=restaurant"],
    "sanitaer": ["craft=plumber"], "klempner": ["craft=plumber"],
    "elektriker": ["craft=electrician"],
    "anwalt": ["office=lawyer"], "rechtsanwalt": ["office=lawyer"], "kanzlei": ["office=lawyer"],
    "tischler": ["craft=carpenter"], "schreiner": ["craft=carpenter"],
    "autowerkstatt": ["shop=car_repair"], "kfz": ["shop=car_repair"],
}


def _norm(s: str) -> str:
    s = s.strip().lower()
    for k, v in {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}.items():
        s = s.replace(k, v)
    return s


def branche_to_tags(branche: str) -> list[str]:
    key = _norm(branche)
    if key not in BRANCHE_TAGS:
        raise ValueError(
            f"Unbekannte Branche '{branche}'. Bekannt: {sorted(BRANCHE_TAGS)}"
        )
    return BRANCHE_TAGS[key]
```

- [ ] **Step 4: Run → PASS**

Run: `python -m pytest tests/test_disco_branche.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add discotool.py tests/test_disco_branche.py
git commit -m "feat(disco): branche_to_tags (OSM-Tag-Mapping)"
```

---

## Task 2: build_overpass_query

**Files:** Modify `discotool.py`, Test `tests/test_disco_query.py`

- [ ] **Step 1: Failing Test**

```python
import discotool


def test_query_hamburg_wide_without_stadtteil():
    q = discotool.build_overpass_query(["amenity=dentist"], None)
    assert "[out:json]" in q
    assert '"name"="Hamburg"' in q
    assert 'node["amenity"="dentist"](area.searchArea);' in q
    assert 'way["amenity"="dentist"](area.searchArea);' in q
    assert "out center tags;" in q


def test_query_with_stadtteil_uses_named_area():
    q = discotool.build_overpass_query(["office=lawyer"], "Eimsbüttel")
    assert '"name"="Eimsbüttel"' in q
    assert 'node["office"="lawyer"](area.searchArea);' in q
```

- [ ] **Step 2: Run → FAIL**

Run: `python -m pytest tests/test_disco_query.py -v`
Expected: FAIL (`has no attribute 'build_overpass_query'`)

- [ ] **Step 3: Implement (append to `discotool.py`)**

```python
def build_overpass_query(tags: list[str], stadtteil: str | None = None) -> str:
    if stadtteil:
        area = f'area["name"="{stadtteil}"]["boundary"="administrative"]->.searchArea;'
    else:
        area = 'area["name"="Hamburg"]["admin_level"="4"]->.searchArea;'
    parts = []
    for tag in tags:
        k, _, v = tag.partition("=")
        for typ in ("node", "way", "relation"):
            parts.append(f'  {typ}["{k}"="{v}"](area.searchArea);')
    body = "\n".join(parts)
    return f"[out:json][timeout:60];\n{area}\n(\n{body}\n);\nout center tags;"
```

- [ ] **Step 4: Run → PASS**

Run: `python -m pytest tests/test_disco_query.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add discotool.py tests/test_disco_query.py
git commit -m "feat(disco): build_overpass_query"
```

---

## Task 3: parse_elements

**Files:** Modify `discotool.py`, Test `tests/test_disco_parse.py`

- [ ] **Step 1: Failing Test**

```python
import discotool

SAMPLE = {"elements": [
    {"type": "node", "id": 1, "tags": {
        "name": "Zahnarzt A", "amenity": "dentist", "website": "https://a.de",
        "addr:street": "Osterstraße", "addr:housenumber": "1",
        "addr:postcode": "20259", "addr:city": "Hamburg"}},
    {"type": "node", "id": 2, "tags": {
        "name": "Zahnarzt B", "amenity": "dentist", "addr:street": "Wegastraße"}},
    {"type": "way", "id": 3, "tags": {"amenity": "dentist"}},  # kein name → skip
    {"type": "node", "id": 4, "tags": {
        "name": "Zahnarzt C", "contact:website": "https://c.de", "contact:phone": "040123"}},
]}


def test_parse_skips_nameless_and_extracts_fields():
    cands = discotool.parse_elements(SAMPLE)
    assert [c["firma"] for c in cands] == ["Zahnarzt A", "Zahnarzt B", "Zahnarzt C"]
    a = cands[0]
    assert a["website"] == "https://a.de"
    assert a["adresse"] == "Osterstraße 1, 20259 Hamburg"
    assert a["osm_id"] == "node/1"


def test_parse_reads_contact_website_fallback():
    cands = discotool.parse_elements(SAMPLE)
    c = cands[2]
    assert c["website"] == "https://c.de"
    assert c["telefon"] == "040123"


def test_parse_empty():
    assert discotool.parse_elements({"elements": []}) == []
```

- [ ] **Step 2: Run → FAIL**

Run: `python -m pytest tests/test_disco_parse.py -v`
Expected: FAIL (`has no attribute 'parse_elements'`)

- [ ] **Step 3: Implement (append to `discotool.py`)**

```python
def _adresse(tags: dict) -> str:
    line1 = " ".join(p for p in [tags.get("addr:street", ""), tags.get("addr:housenumber", "")] if p)
    line2 = " ".join(p for p in [tags.get("addr:postcode", ""), tags.get("addr:city", "")] if p)
    return ", ".join(p for p in [line1, line2] if p)


def parse_elements(data: dict) -> list[dict]:
    out = []
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        firma = tags.get("name")
        if not firma:
            continue
        out.append({
            "firma": firma,
            "adresse": _adresse(tags),
            "website": tags.get("website") or tags.get("contact:website") or "",
            "telefon": tags.get("phone") or tags.get("contact:phone") or "",
            "osm_id": f"{el.get('type', '')}/{el.get('id', '')}",
        })
    return out
```

- [ ] **Step 4: Run → PASS**

Run: `python -m pytest tests/test_disco_parse.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add discotool.py tests/test_disco_parse.py
git commit -m "feat(disco): parse_elements (Overpass-JSON → Kandidaten)"
```

---

## Task 4: score_tier1 + Run-Dateien + set_status

**Files:** Modify `discotool.py`, Test `tests/test_disco_run.py`

- [ ] **Step 1: Failing Test**

```python
import discotool
from datetime import date


def test_score_tier1():
    assert discotool.score_tier1({"website": ""}) == 60
    assert discotool.score_tier1({"website": "https://x.de"}) == 0


def test_new_run_assigns_ids_and_status():
    cands = [{"firma": "Mit Web", "website": "https://x.de", "adresse": "", "telefon": "", "osm_id": "node/1"},
             {"firma": "Ohne Web", "website": "", "adresse": "", "telefon": "", "osm_id": "node/2"}]
    run = discotool.new_run("Zahnärzte", "Eimsbüttel", cands, date(2026, 6, 28))
    assert run["branche"] == "Zahnärzte" and run["stadtteil"] == "Eimsbüttel"
    assert run["kandidaten"][0]["status"] == "hat_website"
    assert run["kandidaten"][1]["status"] == "website_unklar"
    assert run["kandidaten"][1]["score"] == 60
    assert run["kandidaten"][0]["id"] == 1 and run["kandidaten"][1]["id"] == 2


def test_run_save_load_roundtrip(tmp_path):
    run = discotool.new_run("Friseure", None, [], date(2026, 6, 28))
    path = discotool.run_path(tmp_path, "Friseure", None, date(2026, 6, 28))
    discotool.save_run(path, run)
    assert path.exists()
    assert discotool.load_run(path) == run


def test_set_status_updates_and_validates():
    run = discotool.new_run("X", None, [{"firma": "A", "website": "", "adresse": "", "telefon": "", "osm_id": ""}], date(2026, 6, 28))
    discotool.set_status(run, 1, "keine_website")
    assert run["kandidaten"][0]["status"] == "keine_website"
    discotool.set_status(run, 1, "hat_website", "https://found.de")
    assert run["kandidaten"][0]["gefundene_url"] == "https://found.de"
    try:
        discotool.set_status(run, 1, "quatsch")
        assert False
    except ValueError:
        pass
    try:
        discotool.set_status(run, 99, "keine_website")
        assert False
    except ValueError:
        pass
```

- [ ] **Step 2: Run → FAIL**

Run: `python -m pytest tests/test_disco_run.py -v`
Expected: FAIL (`has no attribute 'score_tier1'`)

- [ ] **Step 3: Implement (append to `discotool.py`)**

```python
STATUSES = {"neu", "website_unklar", "keine_website", "hat_website", "analysiert"}


def score_tier1(cand: dict) -> int:
    return 60 if not cand.get("website") else 0


def new_run(branche: str, stadtteil: str | None, candidates: list[dict], today: date) -> dict:
    kand = []
    for i, c in enumerate(candidates, start=1):
        hat_web = bool(c.get("website"))
        kand.append({
            "id": i,
            "firma": c["firma"],
            "adresse": c.get("adresse", ""),
            "website": c.get("website", ""),
            "telefon": c.get("telefon", ""),
            "osm_id": c.get("osm_id", ""),
            "status": "hat_website" if hat_web else "website_unklar",
            "gefundene_url": "",
            "score": score_tier1(c),
            "befund": "Website in OSM hinterlegt" if hat_web else "kein website-Tag in OSM",
            "lead_angelegt": False,
        })
    return {"branche": branche, "stadtteil": stadtteil or "Hamburg",
            "erstellt": today.isoformat(), "kandidaten": kand}


def run_path(root: Path, branche: str, stadtteil: str | None, today: date) -> Path:
    slug = _norm(branche).replace(" ", "-")
    area = _norm(stadtteil or "hamburg").replace(" ", "-")
    return root / "discovery" / f"{today.isoformat()}-{slug}-{area}.json"


def save_run(path: Path, run: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(run, ensure_ascii=False, indent=2), encoding="utf-8")


def load_run(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def set_status(run: dict, cand_id: int, status: str, url: str = "") -> None:
    if status not in STATUSES:
        raise ValueError(f"Unbekannter Status '{status}'. Erlaubt: {sorted(STATUSES)}")
    for c in run["kandidaten"]:
        if c["id"] == cand_id:
            c["status"] = status
            if url:
                c["gefundene_url"] = url
            return
    raise ValueError(f"Kandidat id={cand_id} nicht gefunden")
```

- [ ] **Step 4: Run → PASS**

Run: `python -m pytest tests/test_disco_run.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add discotool.py tests/test_disco_run.py
git commit -m "feat(disco): score_tier1 + Run-Dateien + set_status"
```

---

## Task 5: create_leads (Anbindung an Subsystem B + Dedup)

**Files:** Modify `discotool.py`, Test `tests/test_disco_leads.py`

- [ ] **Step 1: Failing Test**

```python
import discotool
import leadtool
from datetime import date


def _run_with(*firmen_ohne_web):
    cands = [{"firma": f, "website": "", "adresse": "", "telefon": "", "osm_id": ""} for f in firmen_ohne_web]
    return discotool.new_run("Zahnärzte", None, cands, date(2026, 6, 28))


def test_create_leads_auto_only_confirmed(repo):
    run = _run_with("Praxis A", "Praxis B")
    discotool.set_status(run, 1, "keine_website")   # nur A bestätigt
    res = discotool.create_leads(repo, run, "auto", date(2026, 6, 28))
    assert res["angelegt"] == ["praxis-a"]
    rows = leadtool.read_pipeline(repo)
    assert [r["firma"] for r in rows] == ["Praxis A"]
    assert run["kandidaten"][0]["lead_angelegt"] is True


def test_create_leads_dedup_skips_existing(repo):
    leadtool.add_lead(repo, "Praxis A", today=date(2026, 6, 1))  # existiert schon
    run = _run_with("Praxis A")
    discotool.set_status(run, 1, "keine_website")
    res = discotool.create_leads(repo, run, "auto", date(2026, 6, 28))
    assert res["angelegt"] == []
    assert res["uebersprungen"] == ["Praxis A"]


def test_create_leads_by_ids(repo):
    run = _run_with("Praxis A", "Praxis B")
    discotool.set_status(run, 1, "keine_website")
    discotool.set_status(run, 2, "keine_website")
    res = discotool.create_leads(repo, run, [2], date(2026, 6, 28))
    assert res["angelegt"] == ["praxis-b"]
```

- [ ] **Step 2: Run → FAIL**

Run: `python -m pytest tests/test_disco_leads.py -v`
Expected: FAIL (`has no attribute 'create_leads'`)

- [ ] **Step 3: Implement (append to `discotool.py`)**

```python
def create_leads(root: Path, run: dict, which, today: date) -> dict:
    if which == "auto":
        targets = [c for c in run["kandidaten"]
                   if c["status"] == "keine_website" and not c["lead_angelegt"]]
    else:
        ids = set(which)
        targets = [c for c in run["kandidaten"] if c["id"] in ids and not c["lead_angelegt"]]
    angelegt, uebersprungen = [], []
    for c in targets:
        try:
            slug = leadtool.add_lead(root, c["firma"], schwaeche="keine auffindbare Website", today=today)
            c["lead_angelegt"] = True
            angelegt.append(slug)
        except ValueError:
            uebersprungen.append(c["firma"])
    return {"angelegt": angelegt, "uebersprungen": uebersprungen}
```

- [ ] **Step 4: Run → PASS**

Run: `python -m pytest tests/test_disco_leads.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add discotool.py tests/test_disco_leads.py
git commit -m "feat(disco): create_leads (add_lead-Anbindung + Dedup)"
```

---

## Task 6: fetch_overpass (injizierbar) + realer HTTP-Call

**Files:** Modify `discotool.py`, Test `tests/test_disco_fetch.py`

- [ ] **Step 1: Failing Test**

```python
import discotool


def test_fetch_overpass_uses_injected_fn():
    captured = {}
    def fake(query):
        captured["q"] = query
        return {"elements": [{"type": "node", "id": 1, "tags": {"name": "X"}}]}
    data = discotool.fetch_overpass("QUERY", fetch_fn=fake)
    assert captured["q"] == "QUERY"
    assert data["elements"][0]["tags"]["name"] == "X"


def test_http_overpass_is_callable_default():
    # Default fetch_fn ist http_overpass (echter Call) — hier nur Existenz/Signatur prüfen, NICHT aufrufen.
    assert callable(discotool.http_overpass)
```

- [ ] **Step 2: Run → FAIL**

Run: `python -m pytest tests/test_disco_fetch.py -v`
Expected: FAIL (`has no attribute 'fetch_overpass'`)

- [ ] **Step 3: Implement (append to `discotool.py`)**

```python
def http_overpass(query: str) -> dict:
    data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    req = urllib.request.Request(
        OVERPASS_URL, data=data,
        headers={"User-Agent": "SelfworkLeads/0.1 (Hamburg lead discovery; shje@delta-sport.com)"},
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_overpass(query: str, *, fetch_fn=http_overpass) -> dict:
    return fetch_fn(query)
```

- [ ] **Step 4: Run → PASS**

Run: `python -m pytest tests/test_disco_fetch.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add discotool.py tests/test_disco_fetch.py
git commit -m "feat(disco): fetch_overpass (injizierbar) + http_overpass"
```

---

## Task 7: CLI `discover.py`

**Files:** Create `discover.py`, `discovery/.gitkeep`, Test `tests/test_discover_cli.py`

- [ ] **Step 1: Failing Test**

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import discover  # noqa: E402
import discotool  # noqa: E402
import leadtool  # noqa: E402

SAMPLE = {"elements": [
    {"type": "node", "id": 1, "tags": {"name": "Zahnarzt A", "amenity": "dentist", "website": "https://a.de"}},
    {"type": "node", "id": 2, "tags": {"name": "Zahnarzt B", "amenity": "dentist", "addr:street": "Wegastr"}},
]}


def test_cli_scan_then_confirm_then_uebernehmen(repo, capsys, monkeypatch):
    monkeypatch.chdir(repo)
    monkeypatch.setattr(discotool, "http_overpass", lambda q: SAMPLE)

    assert discover.main(["scan", "Zahnärzte", "Eimsbüttel", "--today", "2026-06-28"]) == 0
    runs = list((repo / "discovery").glob("*.json"))
    assert len(runs) == 1
    run_arg = str(runs[0])

    # Zahnarzt B (id 2) hat kein website-Tag → website_unklar; als keine_website bestätigen
    assert discover.main(["setstatus", run_arg, "2", "keine_website"]) == 0
    assert discover.main(["uebernehmen", run_arg, "auto", "--today", "2026-06-28"]) == 0

    rows = leadtool.read_pipeline(repo)
    assert any(r["firma"] == "Zahnarzt B" for r in rows)
    assert not any(r["firma"] == "Zahnarzt A" for r in rows)  # A hatte Website → kein Lead


def test_cli_unknown_branche_returns_error(repo, capsys, monkeypatch):
    monkeypatch.chdir(repo)
    rc = discover.main(["scan", "Raumschiffbauer", "--today", "2026-06-28"])
    assert rc == 1
```

- [ ] **Step 2: Run → FAIL**

Run: `python -m pytest tests/test_discover_cli.py -v`
Expected: FAIL (`No module named 'discover'`)

- [ ] **Step 3: Create `discovery/.gitkeep`** (leere Datei)

- [ ] **Step 4: Implement — create `discover.py`**

```python
"""CLI für Lead-Discovery (Tier 1). Bedient discotool gegen das aktuelle Verzeichnis."""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import discotool


def _today(args) -> date:
    return date.fromisoformat(args.today) if args.today else date.today()


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    p = argparse.ArgumentParser(prog="discover", description="Lead-Discovery Hamburg (Tier 1)")
    p.add_argument("--today", default=None)
    sub = p.add_subparsers(dest="cmd", required=True)

    ps = sub.add_parser("scan", help="Branche+Stadtteil scannen")
    ps.add_argument("branche")
    ps.add_argument("stadtteil", nargs="?", default=None)
    ps.add_argument("--today", default=None)

    psh = sub.add_parser("show", help="Run-Datei anzeigen")
    psh.add_argument("run")
    psh.add_argument("--today", default=None)

    pst = sub.add_parser("setstatus", help="Kandidaten-Status setzen")
    pst.add_argument("run")
    pst.add_argument("id", type=int)
    pst.add_argument("status")
    pst.add_argument("url", nargs="?", default="")
    pst.add_argument("--today", default=None)

    pu = sub.add_parser("uebernehmen", help="Funde als Leads anlegen (ids|auto)")
    pu.add_argument("run")
    pu.add_argument("ids")
    pu.add_argument("--today", default=None)

    args = p.parse_args(argv)
    root = Path(".")

    try:
        if args.cmd == "scan":
            tags = discotool.branche_to_tags(args.branche)
            query = discotool.build_overpass_query(tags, args.stadtteil)
            data = discotool.fetch_overpass(query)
            cands = discotool.parse_elements(data)
            run = discotool.new_run(args.branche, args.stadtteil, cands, _today(args))
            path = discotool.run_path(root, args.branche, args.stadtteil, _today(args))
            discotool.save_run(path, run)
            unklar = sum(1 for c in run["kandidaten"] if c["status"] == "website_unklar")
            print(f"Scan: {len(cands)} Kandidaten → {path}")
            print(f"  davon {unklar} ohne website-Tag (website_unklar → per WebSearch prüfen)")
        elif args.cmd == "show":
            _print_run(discotool.load_run(Path(args.run)))
        elif args.cmd == "setstatus":
            run = discotool.load_run(Path(args.run))
            discotool.set_status(run, args.id, args.status, args.url)
            discotool.save_run(Path(args.run), run)
            print(f"id {args.id} → {args.status}")
        elif args.cmd == "uebernehmen":
            path = Path(args.run)
            run = discotool.load_run(path)
            which = "auto" if args.ids == "auto" else [int(x) for x in args.ids.split(",")]
            res = discotool.create_leads(root, run, which, _today(args))
            discotool.save_run(path, run)
            print(f"Leads angelegt: {len(res['angelegt'])} {res['angelegt']}")
            if res["uebersprungen"]:
                print(f"Übersprungen (Duplikat): {res['uebersprungen']}")
    except (ValueError, FileNotFoundError) as e:
        print(f"Fehler: {e}")
        return 1
    return 0


def _print_run(run: dict) -> None:
    print(f"Run: {run['branche']} / {run['stadtteil']} ({run['erstellt']})")
    for c in run["kandidaten"]:
        mark = "✓Lead" if c["lead_angelegt"] else ""
        print(f"  [{c['id']}] {c['firma']} — {c['status']} (Score {c['score']}) {c['adresse']} {mark}")


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run → PASS**

Run: `python -m pytest tests/test_discover_cli.py -v`
Expected: 2 passed

- [ ] **Step 6: Volle Suite**

Run: `python -m pytest -q`
Expected: alle Tests grün (Subsystem B 29 + Discovery A1 ~16).

- [ ] **Step 7: Commit**

```bash
git add discover.py discovery/.gitkeep tests/test_discover_cli.py
git commit -m "feat(disco): CLI discover.py (scan/show/setstatus/uebernehmen)"
```

---

## Task 8: `discover`-Skill + CLAUDE.md

**Files:** Create `.claude/skills/discover/SKILL.md`, Modify `CLAUDE.md`

- [ ] **Step 1: Create `.claude/skills/discover/SKILL.md`**

````markdown
---
name: discover
description: Use when looking for new leads in Hamburg — Betriebe einer Branche finden + Website-Schwächen prüfen. Trigger: "finde Leads", "scan Branche X in Stadtteil Y", "discovery", "neue Kandidaten".
---

# Lead-Discovery (Hamburg, Tier 1)

Findet Hamburger Betriebe ohne auffindbare Website und legt bestätigte Funde als Leads an
(Subsystem B). Bedienung über `python discover.py …` (Arbeitsverzeichnis = Repo-Root).
Run-Dateien in `discovery/` nur über die CLI ändern, nicht von Hand.

## Ablauf (Tier 1)

1. **Scannen:**
   `python discover.py scan "<Branche>" "<Stadtteil>"`
   (Stadtteil optional → ganz Hamburg.) Erzeugt eine Run-Datei und meldet, wie viele Kandidaten
   `website_unklar` sind (kein website-Tag in OSM).

2. **Anzeigen:** `python discover.py show <run-datei>` — Liste mit ids/Status/Score.

3. **Gegenprüfen (dein Urteil):** Für JEDEN Kandidaten mit Status `website_unklar`:
   per **WebSearch** suchen (Firmenname + Adresse/„Hamburg"). 
   - Echte offizielle Website gefunden → `python discover.py setstatus <run> <id> hat_website <url>`
   - Keine Website auffindbar → `python discover.py setstatus <run> <id> keine_website`
   Sei ehrlich: Branchenportal-/Facebook-Einträge sind KEINE eigene Website.

4. **Übernehmen:** `python discover.py uebernehmen <run> auto`
   Legt für alle als `keine_website` bestätigten Funde automatisch Leads an (Schwäche:
   „keine auffindbare Website"). Duplikate werden übersprungen.
   Einzelne stattdessen: `uebernehmen <run> 1,3,5`.

## Bekannte Branchen
zahnarzt, arzt/hausarzt, friseur, bäckerei, restaurant/gastronomie, sanitär/klempner,
elektriker, anwalt/kanzlei, tischler/schreiner, autowerkstatt/kfz. Weitere → `BRANCHE_TAGS`
in `discotool.py` ergänzen.

## Ehrliche Grenzen
OSM-Abdeckung schwankt je Branche — Discovery ist ein Trichter, kein vollständiges Register.
Höflich abfragen (kein Massen-Loop). Nur öffentliche Firmendaten, keine Kontaktpersonen (DSGVO).

## Integration
Discovery → `leadtool.add_lead`. Danach lebt der Lead im normalen Tracking (`lead`-Skill):
Status setzen, kontaktieren, report. Prototyp (C) / Outreach (D) docken später an.
````

- [ ] **Step 2: Modify `CLAUDE.md`** — Discovery-Zeile ergänzen. Finde den Block „## Tracking bedienen" und füge davor ein:

```markdown
## Discovery (Leads finden)
Nutze den `discover`-Skill (`.claude/skills/discover/SKILL.md`): `python discover.py scan "<Branche>" "<Stadtteil>"`,
dann website_unklar-Kandidaten per WebSearch gegenprüfen (`setstatus`), dann `uebernehmen auto`.
Aktuell gebaut: **A1 (Tier 1 — keine Website)**.

```

Außerdem in der Subsystem-Statuszeile `A Discovery` als teilweise gebaut markieren:
ersetze `(A Discovery · **B Tracking** · ...)` durch `(**A Discovery (A1)** · **B Tracking** · C Prototyp · D Outreach · E Portfolio)`.

- [ ] **Step 3: Smoke-Test (echter Overpass-Call, klein)**

Run (ein echter Netz-Call, kleine Branche):
```bash
python discover.py scan "Zahnärzte" "Eimsbüttel"
python discover.py show discovery/$(ls discovery | grep zahn | head -1)
```
Expected: Run-Datei entsteht mit echten Hamburger Zahnarzt-Kandidaten; `show` listet sie.
Falls Overpass nicht erreichbar/Timeout: als bekannte Umweltbedingung notieren, NICHT als Code-Fehler.

- [ ] **Step 4: Smoke-Artefakte zurückrollen** (keine echten Run-Dateien committen)

```bash
rm -f discovery/*.json
git status --short   # nur die Doku-/Code-Dateien dürfen übrig sein
```

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/discover/SKILL.md CLAUDE.md
git commit -m "docs(disco): discover-Skill + CLAUDE.md Discovery-Block"
```

---

## Self-Review (vom Plan-Autor)

**Spec-Abdeckung (A1):**
- branche_to_tags → Task 1 ✓
- Overpass-Query → Task 2 ✓
- parse_elements (Overpass-JSON → Kandidaten, Fixture statt Netz) → Task 3 ✓
- score_tier1 + Run-Dateien (load/save/new) + set_status → Task 4 ✓
- create_leads (add_lead-Anbindung + Dedup) → Task 5 ✓
- fetch_overpass injizierbar + realer http_overpass → Task 6 ✓
- CLI scan/show/setstatus/uebernehmen → Task 7 ✓
- discover-Skill (orchestriert WebSearch-Schritt) + CLAUDE.md → Task 8 ✓
- „kein echter Overpass-Call im Test" → fetch_fn-/monkeypatch-Injektion in Tasks 6/7 ✓
- Integration B (add_lead, Dedup, reservierte Felder leer) → Task 5 ✓

**Platzhalter-Scan:** keine TODO/TBD; jeder Code-Step vollständig. ✓

**Typ-/Namens-Konsistenz:** `fetch_fn`, `http_overpass`, `run`-dict-Form (`branche/stadtteil/erstellt/kandidaten`),
Kandidaten-Keys (`id/firma/adresse/website/telefon/osm_id/status/gefundene_url/score/befund/lead_angelegt`),
Status-Set, `create_leads(root, run, which, today)` durchgängig identisch. ✓

**Offene Mini-Punkte (bewusst):** Stadtteil-Filter nutzt `area["name"=...]` — bei Namenskollisionen
(Bezirk vs. Stadtteil) ggf. unscharf; für A1 akzeptiert, in A2 verfeinerbar. `out center tags;`
liefert auch für ways/relations Koordinaten (für spätere Tier-Stufen vorgehalten, in A1 ungenutzt).
