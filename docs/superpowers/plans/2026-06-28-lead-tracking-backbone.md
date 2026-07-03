# Lead-Tracking-Rückgrat Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ein datei-basiertes Lead-CRM, das Claude über eine getestete Python-CLI bedient — Leads anlegen, durch die Status-Pipeline führen, bei `in_klaerung` automatisch in eine eigene Datei graduieren, und fällige/überfällige Follow-ups reporten.

**Architecture:** Source-of-Truth sind Markdown-Dateien (`pipeline.md` Tabelle für kalte Leads, `leads/<slug>.md` mit YAML-Frontmatter für warme). Eine dünne CLI (`lead.py`) ruft Funktionen aus `leadtool.py`, das alles deterministisch macht (Parsen, Status-Übergänge, Graduierung, Datums-Report). `SKILL.md` dokumentiert nur, *wann* Claude welches Kommando ruft. Alle Datumslogik bekommt `today` injiziert → testbar.

**Tech Stack:** Python 3.11+ (stdlib + PyYAML), pytest. Windows (PowerShell). Git-versioniert.

**Abweichung von Spec (bewusst, im Brainstorming bestätigt):** Spec sagte „Claude pflegt die Dateien". Wir setzen stattdessen eine getestete Python-CLI dazwischen (Coding-Lernwert + Zuverlässigkeit). Das Datei-Modell der Spec bleibt 1:1.

---

## File Structure

```
Leads/
├── lead.py                       # CLI-Dispatch (argparse) → ruft leadtool
├── leadtool.py                   # ALLE Logik: parse/render, add, status, graduate, note, report
├── requirements-dev.txt          # pyyaml, pytest
├── pytest.ini                    # pytest-Konfig
├── pipeline.md                   # Sammeldatei (von `lead init` erzeugt)
├── templates/lead.md             # Body-Skelett für warme Leads (von `lead init` erzeugt)
├── leads/.gitkeep                # warme Lead-Dateien landen hier
├── prototypes/.gitkeep           # Subsystem C (reserviert)
├── tests/
│   ├── conftest.py               # tmp-Repo-Fixture via leadtool.init_repo
│   ├── test_pipeline_table.py    # Task 1
│   ├── test_add_lead.py          # Task 2
│   ├── test_frontmatter.py       # Task 3
│   ├── test_graduate.py          # Task 4
│   ├── test_set_status.py        # Task 5
│   ├── test_report.py            # Task 6
│   ├── test_notes.py             # Task 7
│   └── test_cli.py               # Task 8
├── .gitignore
├── CLAUDE.md                     # Repo-Router (Task 9)
└── .claude/skills/lead/SKILL.md  # Skill-Wrapper (Task 9)
```

**Verantwortlichkeiten:**
- `leadtool.py` — reine Funktionen, kein I/O außer Datei-Lesen/-Schreiben unter `root: Path`. Kein `date.today()` intern (immer injiziert).
- `lead.py` — übersetzt argv → Funktionsaufruf, setzt `today = date.today()`, formatiert Ausgabe.
- `tests/` — pytest, jede Funktion isoliert gegen ein tmp-Repo.

---

## Task 0: Projekt-Scaffold + Tooling

**Files:**
- Create: `requirements-dev.txt`, `pytest.ini`, `.gitignore`, `leads/.gitkeep`, `prototypes/.gitkeep`, `leadtool.py` (Stub mit Konstanten + `init_repo`), `tests/conftest.py`

- [ ] **Step 1: `.gitignore`**

```gitignore
__pycache__/
*.pyc
.pytest_cache/
.venv/
venv/
```

- [ ] **Step 2: `requirements-dev.txt`**

```
pyyaml>=6.0
pytest>=8.0
```

- [ ] **Step 3: `pytest.ini`**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
```

- [ ] **Step 4: `leads/.gitkeep` und `prototypes/.gitkeep`** (leere Dateien)

- [ ] **Step 5: `leadtool.py` — Konstanten + `init_repo`**

```python
"""Lead-Tracking-Kern: parse/render, Status, Graduierung, Report. Reine Logik, today wird injiziert."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml

# Spalten der Sammeltabelle (interne Keys, Reihenfolge = Spaltenreihenfolge)
PIPELINE_COLUMNS = ["slug", "firma", "status", "schwaeche", "kontaktiert_am", "wiedervorlage", "notiz"]
# Anzeige-Header (Spaltenüberschriften in pipeline.md)
PIPELINE_HEADERS = ["slug", "Firma", "Status", "Schwäche", "kontaktiert_am", "Wiedervorlage", "Notiz"]

COLD_STATUSES = {"identifiziert", "analysiert", "prototyp_erstellt", "kontaktiert", "keine_antwort", "verloren", "zurückgestellt"}
WARM_STATUSES = {"in_klaerung", "termin_vereinbart", "angebot_raus", "gewonnen"}
ALL_STATUSES = COLD_STATUSES | WARM_STATUSES

NO_ANSWER_DAYS = 14
EMPTY_CELL = "—"

PIPELINE_TITLE = "# Lead-Pipeline (kalt/früh)\n\nEine Zeile pro Lead. Warme Leads (ab `in_klaerung`) wandern nach `leads/<slug>.md`.\n\n"
BODY_SKELETON = "## Historie\n\n## Absprachen\n\n## Notizen\n"
LEAD_TEMPLATE = "---\n# Frontmatter wird von lead.py beim Graduieren gefüllt\n---\n" + BODY_SKELETON


def init_repo(root: Path) -> None:
    """Erzeugt pipeline.md, templates/lead.md, leads/, prototypes/ falls fehlend."""
    (root / "leads").mkdir(exist_ok=True)
    (root / "prototypes").mkdir(exist_ok=True)
    (root / "templates").mkdir(exist_ok=True)
    tmpl = root / "templates" / "lead.md"
    if not tmpl.exists():
        tmpl.write_text(LEAD_TEMPLATE, encoding="utf-8")
    pipeline = root / "pipeline.md"
    if not pipeline.exists():
        pipeline.write_text(PIPELINE_TITLE + render_pipeline_table([]), encoding="utf-8")
```

- [ ] **Step 6: `tests/conftest.py`**

```python
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import leadtool  # noqa: E402


@pytest.fixture
def repo(tmp_path):
    """Frisches tmp-Repo mit pipeline.md + templates/lead.md."""
    leadtool.init_repo(tmp_path)
    return tmp_path
```

- [ ] **Step 7: Dependencies installieren**

Run: `python -m pip install -r requirements-dev.txt`
Expected: pyyaml + pytest installiert (oder „already satisfied").

> **Hinweis:** `init_repo` ruft `render_pipeline_table`, das erst in Task 1 entsteht. Bis dahin nicht ausführen — nur Dateien anlegen. Erster Lauf erfolgt am Ende von Task 1.

- [ ] **Step 8: Commit**

```bash
git add .gitignore requirements-dev.txt pytest.ini leadtool.py tests/conftest.py leads/.gitkeep prototypes/.gitkeep
git commit -m "chore: Scaffold Lead-CRM (Tooling + leadtool-Stub)"
```

---

## Task 1: Pipeline-Tabelle parsen & rendern (Round-Trip)

**Files:**
- Modify: `leadtool.py` (Funktionen ergänzen)
- Test: `tests/test_pipeline_table.py`

- [ ] **Step 1: Failing Test**

```python
import leadtool


def test_render_then_parse_roundtrip():
    rows = [
        {"slug": "mueller-sanitaer", "firma": "Müller Sanitär", "status": "kontaktiert",
         "schwaeche": "keine Mobil-Ansicht", "kontaktiert_am": "2026-06-20",
         "wiedervorlage": "2026-07-05", "notiz": ""},
    ]
    text = leadtool.render_pipeline_table(rows)
    assert leadtool.parse_pipeline_table(text) == rows


def test_parse_empty_table_returns_no_rows():
    text = leadtool.render_pipeline_table([])
    assert leadtool.parse_pipeline_table(text) == []


def test_render_sanitizes_pipe_and_blank_cells():
    rows = [{"slug": "x", "firma": "A|B", "status": "identifiziert",
             "schwaeche": "", "kontaktiert_am": "", "wiedervorlage": "", "notiz": ""}]
    text = leadtool.render_pipeline_table(rows)
    assert "A/B" in text          # Pipe ersetzt
    assert "| — |" in text         # leere Zelle als —
    parsed = leadtool.parse_pipeline_table(text)
    assert parsed[0]["schwaeche"] == ""   # — wird beim Parsen wieder zu ""
```

- [ ] **Step 2: Run → FAIL**

Run: `python -m pytest tests/test_pipeline_table.py -v`
Expected: FAIL (`AttributeError: module 'leadtool' has no attribute 'render_pipeline_table'`)

- [ ] **Step 3: Implementieren (an `leadtool.py` anhängen)**

```python
def _cell(value: str) -> str:
    value = (value or "").replace("|", "/").strip()
    return value if value else EMPTY_CELL


def render_pipeline_table(rows: list[dict]) -> str:
    lines = ["| " + " | ".join(PIPELINE_HEADERS) + " |",
             "|" + "|".join(["---"] * len(PIPELINE_HEADERS)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(_cell(row.get(k, "")) for k in PIPELINE_COLUMNS) + " |")
    return "\n".join(lines) + "\n"


def parse_pipeline_table(text: str) -> list[dict]:
    table_lines = [ln for ln in text.splitlines() if ln.lstrip().startswith("|")]
    rows: list[dict] = []
    for ln in table_lines[2:]:  # [0]=Header, [1]=Separator
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) != len(PIPELINE_COLUMNS):
            continue
        values = ["" if c == EMPTY_CELL else c for c in cells]
        rows.append(dict(zip(PIPELINE_COLUMNS, values)))
    return rows
```

- [ ] **Step 4: Run → PASS**

Run: `python -m pytest tests/test_pipeline_table.py -v`
Expected: 3 passed

- [ ] **Step 5: `init_repo` jetzt lauffähig — Seed erzeugen**

Run: `python -c "import leadtool, pathlib; leadtool.init_repo(pathlib.Path('.'))"`
Expected: `pipeline.md` + `templates/lead.md` existieren. `pipeline.md` enthält Titel + leere Tabelle.

- [ ] **Step 6: Commit**

```bash
git add leadtool.py tests/test_pipeline_table.py pipeline.md templates/lead.md
git commit -m "feat: Pipeline-Tabelle parse/render + Repo-Seed"
```

---

## Task 2: slugify + add_lead

**Files:**
- Modify: `leadtool.py`
- Test: `tests/test_add_lead.py`

- [ ] **Step 1: Failing Test**

```python
import leadtool
from datetime import date


def test_slugify_normalizes_umlauts_and_spaces():
    assert leadtool.slugify("Müller Sanitär GmbH") == "mueller-sanitaer-gmbh"
    assert leadtool.slugify("Café & Co.") == "cafe-co"


def test_add_lead_appends_row(repo):
    slug = leadtool.add_lead(repo, "Müller Sanitär GmbH", schwaeche="keine Mobil-Ansicht",
                             today=date(2026, 6, 18))
    assert slug == "mueller-sanitaer-gmbh"
    rows = leadtool.read_pipeline(repo)
    assert len(rows) == 1
    assert rows[0]["firma"] == "Müller Sanitär GmbH"
    assert rows[0]["status"] == "identifiziert"
    assert rows[0]["schwaeche"] == "keine Mobil-Ansicht"


def test_add_lead_duplicate_slug_raises(repo):
    leadtool.add_lead(repo, "Müller Sanitär", today=date(2026, 6, 18))
    try:
        leadtool.add_lead(repo, "Müller Sanitär", today=date(2026, 6, 18))
        assert False, "erwartete ValueError"
    except ValueError:
        pass
```

- [ ] **Step 2: Run → FAIL**

Run: `python -m pytest tests/test_add_lead.py -v`
Expected: FAIL (`has no attribute 'slugify'`)

- [ ] **Step 3: Implementieren (an `leadtool.py` anhängen)**

```python
import re
import unicodedata

# Nach .lower() reichen Kleinbuchstaben-Keys.
_UMLAUTS = {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}


def slugify(name: str) -> str:
    s = name.strip().lower()
    for k, v in _UMLAUTS.items():
        s = s.replace(k, v)
    # restliche Akzente (é, à, ç, ...) generisch zu ASCII entfernen
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def read_pipeline(root: Path) -> list[dict]:
    return parse_pipeline_table((root / "pipeline.md").read_text(encoding="utf-8"))


def write_pipeline(root: Path, rows: list[dict]) -> None:
    (root / "pipeline.md").write_text(PIPELINE_TITLE + render_pipeline_table(rows), encoding="utf-8")


def add_lead(root: Path, firma: str, *, schwaeche: str = "", status: str = "identifiziert",
             today: date) -> str:
    slug = slugify(firma)
    rows = read_pipeline(root)
    if any(r["slug"] == slug for r in rows) or lead_path(root, slug).exists():
        raise ValueError(f"Lead '{slug}' existiert bereits")
    rows.append({"slug": slug, "firma": firma, "status": status, "schwaeche": schwaeche,
                 "kontaktiert_am": "", "wiedervorlage": "", "notiz": ""})
    write_pipeline(root, rows)
    return slug


def lead_path(root: Path, slug: str) -> Path:
    return root / "leads" / f"{slug}.md"
```

- [ ] **Step 4: Run → PASS**

Run: `python -m pytest tests/test_add_lead.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add leadtool.py tests/test_add_lead.py
git commit -m "feat: slugify + add_lead + pipeline read/write"
```

---

## Task 3: Frontmatter parsen & dumpen

**Files:**
- Modify: `leadtool.py`
- Test: `tests/test_frontmatter.py`

- [ ] **Step 1: Failing Test**

```python
import leadtool


def test_frontmatter_roundtrip():
    meta = {"firma": "Müller Sanitär", "slug": "mueller-sanitaer", "status": "in_klaerung",
            "schwaeche": ["keine mobile Ansicht", "kein Kontaktformular"]}
    body = "## Historie\n- 2026-06-25 Antwort\n\n## Notizen\n"
    text = leadtool.dump_frontmatter(meta, body)
    assert text.startswith("---\n")
    meta2, body2 = leadtool.parse_frontmatter(text)
    assert meta2 == meta
    assert body2 == body


def test_dump_preserves_key_order_and_umlauts():
    text = leadtool.dump_frontmatter({"firma": "Café", "status": "gewonnen"}, "")
    assert text.index("firma") < text.index("status")
    assert "Café" in text  # allow_unicode
```

- [ ] **Step 2: Run → FAIL**

Run: `python -m pytest tests/test_frontmatter.py -v`
Expected: FAIL (`has no attribute 'dump_frontmatter'`)

- [ ] **Step 3: Implementieren (an `leadtool.py` anhängen)**

```python
def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta = yaml.safe_load(parts[1]) or {}
    body = parts[2].lstrip("\n")
    return meta, body


def dump_frontmatter(meta: dict, body: str) -> str:
    fm = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True, default_flow_style=False)
    return f"---\n{fm}---\n{body}"
```

- [ ] **Step 4: Run → PASS**

Run: `python -m pytest tests/test_frontmatter.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add leadtool.py tests/test_frontmatter.py
git commit -m "feat: YAML-Frontmatter parse/dump"
```

---

## Task 4: Graduierung (pipeline-Zeile → eigene Datei)

**Files:**
- Modify: `leadtool.py`
- Test: `tests/test_graduate.py`

- [ ] **Step 1: Failing Test**

```python
import leadtool
from datetime import date


def test_graduate_creates_file_and_removes_row(repo):
    leadtool.add_lead(repo, "Müller Sanitär", schwaeche="keine Mobil-Ansicht; kein Formular",
                      today=date(2026, 6, 18))
    leadtool.graduate(repo, "mueller-sanitaer", status="in_klaerung", today=date(2026, 6, 25))

    # Zeile aus pipeline entfernt
    assert leadtool.read_pipeline(repo) == []
    # Datei existiert mit korrektem Frontmatter
    path = leadtool.lead_path(repo, "mueller-sanitaer")
    assert path.exists()
    meta, body = leadtool.parse_frontmatter(path.read_text(encoding="utf-8"))
    assert meta["status"] == "in_klaerung"
    assert meta["firma"] == "Müller Sanitär"
    assert meta["schwaeche"] == ["keine Mobil-Ansicht", "kein Formular"]
    assert meta["angelegt"] == "2026-06-25"
    assert "## Absprachen" in body


def test_graduate_unknown_slug_raises(repo):
    try:
        leadtool.graduate(repo, "gibtsnicht", status="in_klaerung", today=date(2026, 6, 25))
        assert False
    except ValueError:
        pass
```

- [ ] **Step 2: Run → FAIL**

Run: `python -m pytest tests/test_graduate.py -v`
Expected: FAIL (`has no attribute 'graduate'`)

- [ ] **Step 3: Implementieren (an `leadtool.py` anhängen)**

```python
def _split_schwaeche(raw: str) -> list[str]:
    parts = re.split(r"[;,]", raw or "")
    return [p.strip() for p in parts if p.strip()]


def _template_body(root: Path) -> str:
    tmpl = root / "templates" / "lead.md"
    if tmpl.exists():
        _, body = parse_frontmatter(tmpl.read_text(encoding="utf-8"))
        if body.strip():
            return body
    return BODY_SKELETON


def graduate(root: Path, slug: str, *, status: str, today: date) -> Path:
    rows = read_pipeline(root)
    row = next((r for r in rows if r["slug"] == slug), None)
    if row is None:
        raise ValueError(f"Lead '{slug}' nicht in pipeline.md")
    meta = {
        "firma": row["firma"], "slug": slug, "status": status,
        "prioritaet": "mittel", "ort": "", "branche": "", "website": "",
        "schwaeche": _split_schwaeche(row["schwaeche"]),
        "ucp": "", "roi_these": "", "prototyp": "",
        "kontakt": {"name": "", "rolle": "", "email": "", "quelle": ""},
        "kontaktiert_am": row["kontaktiert_am"], "wiedervorlage": row["wiedervorlage"],
        "angelegt": today.isoformat(),
    }
    path = lead_path(root, slug)
    path.write_text(dump_frontmatter(meta, _template_body(root)), encoding="utf-8")
    write_pipeline(root, [r for r in rows if r["slug"] != slug])
    return path
```

- [ ] **Step 4: Run → PASS**

Run: `python -m pytest tests/test_graduate.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add leadtool.py tests/test_graduate.py
git commit -m "feat: Graduierung kalt -> warm"
```

---

## Task 5: set_status (cold↔cold, cold→warm, warm-update)

**Files:**
- Modify: `leadtool.py`
- Test: `tests/test_set_status.py`

- [ ] **Step 1: Failing Test**

```python
import leadtool
from datetime import date


def test_status_cold_stamps_kontaktiert_am(repo):
    leadtool.add_lead(repo, "Müller Sanitär", today=date(2026, 6, 18))
    leadtool.set_status(repo, "mueller-sanitaer", "kontaktiert", today=date(2026, 6, 20))
    row = leadtool.read_pipeline(repo)[0]
    assert row["status"] == "kontaktiert"
    assert row["kontaktiert_am"] == "2026-06-20"


def test_status_to_warm_triggers_graduation(repo):
    leadtool.add_lead(repo, "Müller Sanitär", today=date(2026, 6, 18))
    leadtool.set_status(repo, "mueller-sanitaer", "in_klaerung", today=date(2026, 6, 25))
    assert leadtool.read_pipeline(repo) == []
    assert leadtool.lead_path(repo, "mueller-sanitaer").exists()


def test_status_warm_update_changes_frontmatter(repo):
    leadtool.add_lead(repo, "Müller Sanitär", today=date(2026, 6, 18))
    leadtool.set_status(repo, "mueller-sanitaer", "in_klaerung", today=date(2026, 6, 25))
    leadtool.set_status(repo, "mueller-sanitaer", "angebot_raus", today=date(2026, 6, 28))
    meta, _ = leadtool.parse_frontmatter(leadtool.lead_path(repo, "mueller-sanitaer").read_text(encoding="utf-8"))
    assert meta["status"] == "angebot_raus"


def test_status_invalid_raises(repo):
    leadtool.add_lead(repo, "Müller Sanitär", today=date(2026, 6, 18))
    try:
        leadtool.set_status(repo, "mueller-sanitaer", "quatsch", today=date(2026, 6, 20))
        assert False
    except ValueError:
        pass
```

- [ ] **Step 2: Run → FAIL**

Run: `python -m pytest tests/test_set_status.py -v`
Expected: FAIL (`has no attribute 'set_status'`)

- [ ] **Step 3: Implementieren (an `leadtool.py` anhängen)**

```python
def read_lead(root: Path, slug: str) -> tuple[dict, str]:
    return parse_frontmatter(lead_path(root, slug).read_text(encoding="utf-8"))


def write_lead(root: Path, slug: str, meta: dict, body: str) -> None:
    lead_path(root, slug).write_text(dump_frontmatter(meta, body), encoding="utf-8")


def set_status(root: Path, slug: str, status: str, *, today: date) -> None:
    if status not in ALL_STATUSES:
        raise ValueError(f"Unbekannter Status '{status}'. Erlaubt: {sorted(ALL_STATUSES)}")

    if lead_path(root, slug).exists():          # bereits warm → Frontmatter aktualisieren
        meta, body = read_lead(root, slug)
        meta["status"] = status
        write_lead(root, slug, meta, body)
        return

    rows = read_pipeline(root)
    row = next((r for r in rows if r["slug"] == slug), None)
    if row is None:
        raise ValueError(f"Lead '{slug}' nicht gefunden")

    if status in WARM_STATUSES:                 # kalt → warm: graduieren
        graduate(root, slug, status=status, today=today)
        return

    row["status"] = status                      # kalt → kalt
    if status == "kontaktiert" and not row["kontaktiert_am"]:
        row["kontaktiert_am"] = today.isoformat()
    write_pipeline(root, rows)
```

- [ ] **Step 4: Run → PASS**

Run: `python -m pytest tests/test_set_status.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add leadtool.py tests/test_set_status.py
git commit -m "feat: set_status mit Auto-Graduierung + kontaktiert_am-Stempel"
```

---

## Task 6: report (Wiedervorlage fällig + 14-Tage-keine-Antwort)

**Files:**
- Modify: `leadtool.py`
- Test: `tests/test_report.py`

- [ ] **Step 1: Failing Test**

```python
import leadtool
from datetime import date


def test_report_flags_overdue_no_answer(repo):
    leadtool.add_lead(repo, "Alt GmbH", today=date(2026, 6, 1))
    leadtool.set_status(repo, "alt-gmbh", "kontaktiert", today=date(2026, 6, 1))
    # 27 Tage später, keine Antwort
    rep = leadtool.report(repo, today=date(2026, 6, 28))
    slugs = [c["slug"] for c in rep["keine_antwort"]]
    assert "alt-gmbh" in slugs
    assert rep["keine_antwort"][0]["tage"] == 27


def test_report_ignores_recent_contact(repo):
    leadtool.add_lead(repo, "Neu GmbH", today=date(2026, 6, 20))
    leadtool.set_status(repo, "neu-gmbh", "kontaktiert", today=date(2026, 6, 20))
    rep = leadtool.report(repo, today=date(2026, 6, 28))  # erst 8 Tage
    assert rep["keine_antwort"] == []


def test_report_flags_due_wiedervorlage_for_warm_lead(repo):
    leadtool.add_lead(repo, "Warm GmbH", today=date(2026, 6, 1))
    leadtool.set_status(repo, "warm-gmbh", "in_klaerung", today=date(2026, 6, 10))
    meta, body = leadtool.read_lead(repo, "warm-gmbh")
    meta["wiedervorlage"] = "2026-06-28"
    leadtool.write_lead(repo, "warm-gmbh", meta, body)
    rep = leadtool.report(repo, today=date(2026, 6, 28))
    assert any(c["slug"] == "warm-gmbh" for c in rep["wiedervorlage_faellig"])
```

- [ ] **Step 2: Run → FAIL**

Run: `python -m pytest tests/test_report.py -v`
Expected: FAIL (`has no attribute 'report'`)

- [ ] **Step 3: Implementieren (an `leadtool.py` anhängen)**

```python
def _all_leads(root: Path) -> list[dict]:
    """Vereinheitlichte Sicht: kalte Zeilen + warme Frontmatter, je als dict mit slug/firma/status/kontaktiert_am/wiedervorlage."""
    out: list[dict] = []
    for r in read_pipeline(root):
        out.append({"slug": r["slug"], "firma": r["firma"], "status": r["status"],
                    "kontaktiert_am": r["kontaktiert_am"], "wiedervorlage": r["wiedervorlage"]})
    for f in sorted((root / "leads").glob("*.md")):
        meta, _ = parse_frontmatter(f.read_text(encoding="utf-8"))
        out.append({"slug": meta.get("slug", f.stem), "firma": meta.get("firma", ""),
                    "status": meta.get("status", ""), "kontaktiert_am": meta.get("kontaktiert_am") or "",
                    "wiedervorlage": meta.get("wiedervorlage") or ""})
    return out


def report(root: Path, *, today: date) -> dict:
    keine_antwort, wiedervorlage_faellig = [], []
    for lead in _all_leads(root):
        if lead["status"] == "kontaktiert" and lead["kontaktiert_am"]:
            tage = (today - date.fromisoformat(lead["kontaktiert_am"])).days
            if tage > NO_ANSWER_DAYS:
                keine_antwort.append({**lead, "tage": tage})
        if lead["wiedervorlage"] and date.fromisoformat(lead["wiedervorlage"]) <= today:
            wiedervorlage_faellig.append(lead)
    return {"keine_antwort": keine_antwort, "wiedervorlage_faellig": wiedervorlage_faellig}
```

- [ ] **Step 4: Run → PASS**

Run: `python -m pytest tests/test_report.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add leadtool.py tests/test_report.py
git commit -m "feat: report (Wiedervorlage faellig + 14-Tage-keine-Antwort)"
```

---

## Task 7: add_note

**Files:**
- Modify: `leadtool.py`
- Test: `tests/test_notes.py`

- [ ] **Step 1: Failing Test**

```python
import leadtool
from datetime import date


def test_note_on_cold_lead_appends_to_notiz_column(repo):
    leadtool.add_lead(repo, "Müller Sanitär", today=date(2026, 6, 18))
    leadtool.add_note(repo, "mueller-sanitaer", "Telefon klingelt nicht", today=date(2026, 6, 19))
    row = leadtool.read_pipeline(repo)[0]
    assert "Telefon klingelt nicht" in row["notiz"]


def test_note_on_warm_lead_appends_to_notizen_section(repo):
    leadtool.add_lead(repo, "Müller Sanitär", today=date(2026, 6, 18))
    leadtool.set_status(repo, "mueller-sanitaer", "in_klaerung", today=date(2026, 6, 25))
    leadtool.add_note(repo, "mueller-sanitaer", "will Festpreis bis Ende Juli", today=date(2026, 6, 26))
    _, body = leadtool.read_lead(repo, "mueller-sanitaer")
    assert "2026-06-26" in body
    assert "will Festpreis bis Ende Juli" in body
```

- [ ] **Step 2: Run → FAIL**

Run: `python -m pytest tests/test_notes.py -v`
Expected: FAIL (`has no attribute 'add_note'`)

- [ ] **Step 3: Implementieren (an `leadtool.py` anhängen)**

```python
def add_note(root: Path, slug: str, text: str, *, today: date) -> None:
    stamp = today.isoformat()
    if lead_path(root, slug).exists():
        meta, body = read_lead(root, slug)
        line = f"- {stamp}: {text}\n"
        if "## Notizen" in body:
            head, _, tail = body.partition("## Notizen\n")
            body = head + "## Notizen\n" + line + tail
        else:
            body = body.rstrip("\n") + f"\n\n## Notizen\n{line}"
        write_lead(root, slug, meta, body)
        return
    rows = read_pipeline(root)
    row = next((r for r in rows if r["slug"] == slug), None)
    if row is None:
        raise ValueError(f"Lead '{slug}' nicht gefunden")
    existing = row["notiz"]
    row["notiz"] = f"{existing}; {text}" if existing else text
    write_pipeline(root, rows)
```

- [ ] **Step 4: Run → PASS**

Run: `python -m pytest tests/test_notes.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add leadtool.py tests/test_notes.py
git commit -m "feat: add_note (kalt: Spalte, warm: Notizen-Abschnitt)"
```

---

## Task 8: CLI `lead.py`

**Files:**
- Create: `lead.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Failing Test**

```python
import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import lead  # noqa: E402
import leadtool  # noqa: E402


def test_cli_neu_then_report(repo, capsys, monkeypatch):
    monkeypatch.chdir(repo)
    assert lead.main(["neu", "Müller Sanitär", "--schwaeche", "keine Mobil-Ansicht",
                      "--today", "2026-06-18"]) == 0
    assert lead.main(["status", "mueller-sanitaer", "kontaktiert", "--today", "2026-06-18"]) == 0
    assert lead.main(["report", "--today", "2026-07-10"]) == 0
    out = capsys.readouterr().out
    assert "mueller-sanitaer" in out
    assert "keine Antwort" in out.lower() or "keine_antwort" in out.lower()


def test_cli_unknown_status_returns_error(repo, capsys, monkeypatch):
    monkeypatch.chdir(repo)
    lead.main(["neu", "Test GmbH", "--today", "2026-06-18"])
    rc = lead.main(["status", "test-gmbh", "quatsch", "--today", "2026-06-18"])
    assert rc == 1
```

- [ ] **Step 2: Run → FAIL**

Run: `python -m pytest tests/test_cli.py -v`
Expected: FAIL (`No module named 'lead'`)

- [ ] **Step 3: Implementieren — `lead.py`**

```python
"""CLI für das Lead-CRM. Bedient leadtool gegen das aktuelle Verzeichnis (root=.)."""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import leadtool


def _today(args) -> date:
    return date.fromisoformat(args.today) if args.today else date.today()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="lead", description="Lead-Tracking-CRM")
    p.add_argument("--today", help="ISO-Datum überschreiben (Tests/Debug)", default=None)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="Repo-Dateien anlegen")

    p_neu = sub.add_parser("neu", help="Lead anlegen")
    p_neu.add_argument("firma")
    p_neu.add_argument("--schwaeche", default="")

    p_st = sub.add_parser("status", help="Status setzen (graduiert bei warm)")
    p_st.add_argument("slug")
    p_st.add_argument("status")

    p_no = sub.add_parser("notiz", help="Notiz anhängen")
    p_no.add_argument("slug")
    p_no.add_argument("text")

    sub.add_parser("report", help="Fällige Wiedervorlagen + überfällige Kontakte")

    args = p.parse_args(argv)
    root = Path(".")

    try:
        if args.cmd == "init":
            leadtool.init_repo(root)
            print("Repo initialisiert.")
        elif args.cmd == "neu":
            slug = leadtool.add_lead(root, args.firma, schwaeche=args.schwaeche, today=_today(args))
            print(f"Lead angelegt: {slug}")
        elif args.cmd == "status":
            leadtool.set_status(root, args.slug, args.status, today=_today(args))
            print(f"{args.slug} → {args.status}")
        elif args.cmd == "notiz":
            leadtool.add_note(root, args.slug, args.text, today=_today(args))
            print(f"Notiz an {args.slug} angehängt.")
        elif args.cmd == "report":
            _print_report(leadtool.report(root, today=_today(args)))
    except (ValueError, FileNotFoundError) as e:
        print(f"Fehler: {e}")
        return 1
    return 0


def _print_report(rep: dict) -> None:
    print("=== Fällige Wiedervorlagen ===")
    for c in rep["wiedervorlage_faellig"]:
        print(f"  [{c['slug']}] {c['firma']} — Wiedervorlage {c['wiedervorlage']} (Status {c['status']})")
    if not rep["wiedervorlage_faellig"]:
        print("  keine")
    print("=== >14 Tage keine Antwort (→ Status 'keine_antwort' erwägen) ===")
    for c in rep["keine_antwort"]:
        print(f"  [{c['slug']}] {c['firma']} — kontaktiert {c['kontaktiert_am']} ({c['tage']} Tage her)")
    if not rep["keine_antwort"]:
        print("  keine")


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run → PASS**

Run: `python -m pytest tests/test_cli.py -v`
Expected: 2 passed

- [ ] **Step 5: Volle Suite grün**

Run: `python -m pytest -v`
Expected: alle Tests passed (Tasks 1–8)

- [ ] **Step 6: Commit**

```bash
git add lead.py tests/test_cli.py
git commit -m "feat: CLI lead.py (init/neu/status/notiz/report)"
```

---

## Task 9: SKILL.md + CLAUDE.md (Repo-Router)

**Files:**
- Create: `.claude/skills/lead/SKILL.md`, `CLAUDE.md`

- [ ] **Step 1: `.claude/skills/lead/SKILL.md`**

````markdown
---
name: lead
description: Use when tracking sales leads in this Leads-Repo — Lead anlegen, Status setzen, Notizen, oder das Follow-up-Cockpit (report). Trigger: "neuer Lead", "Status auf X", "wer ist fällig", "lead report".
---

# Lead-Tracking (CRM)

Bediene das datei-basierte Lead-CRM **ausschließlich über die CLI** `python lead.py …`
(Arbeitsverzeichnis = Repo-Root). Editiere `pipeline.md` / `leads/*.md` nicht von Hand —
die CLI hält Tabelle, Frontmatter und Graduierung konsistent.

## Kommandos

| Aufgabe | Kommando |
|---------|----------|
| Lead anlegen | `python lead.py neu "Firma GmbH" --schwaeche "keine Mobil-Ansicht"` |
| Status setzen | `python lead.py status <slug> <status>` |
| Notiz anhängen | `python lead.py notiz <slug> "Text"` |
| Follow-up-Report | `python lead.py report` |
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
5. **Wiedervorlage:** Datum im Frontmatter `wiedervorlage:` pflegen; `report` zeigt fällige.

## Routine
Bei Session-Start oder auf Wunsch: `python lead.py report` laufen lassen und offene Follow-ups melden.

## Integration (spätere Subsysteme)
- Discovery (A) ruft `neu` mit vorbefüllter Schwäche.
- Prototyp (C) schreibt nach `prototypes/<slug>/`, setzt Frontmatter `prototyp:`.
- Outreach (D) liest `ucp`/`roi_these`/`prototyp`, entwirft Mail, setzt nach manuellem Versand `status kontaktiert`.
````

- [ ] **Step 2: `CLAUDE.md` (Repo-Router)**

```markdown
# Leads — Festpreis-Akquise Hamburg (Repo-Router)

Selfwork-Projekt von Shawn: Festpreis-Projekte in Hamburg akquirieren. 5 Subsysteme
(A Discovery · **B Tracking** · C Prototyp · D Outreach · E Portfolio). Aktuell gebaut: **B**.

## Tracking bedienen
Nutze den `lead`-Skill (`.claude/skills/lead/SKILL.md`). Alles läuft über `python lead.py …`.
Nie `pipeline.md` / `leads/*.md` von Hand editieren.

## Recht (wichtig für D, noch nicht gebaut)
Kein vollautomatischer Mailversand — UWG §7. System bereitet Mail vor, Shawn sendet manuell.

## Specs & Pläne
- Spec B: `docs/superpowers/specs/2026-06-28-lead-tracking-backbone-design.md`
- Plan B: `docs/superpowers/plans/2026-06-28-lead-tracking-backbone.md`
```

- [ ] **Step 3: Smoke-Test der CLI end-to-end (echtes Repo)**

Run:
```bash
python lead.py neu "Test Smoke GmbH" --schwaeche "veraltete Website" --today 2026-06-28
python lead.py status test-smoke-gmbh kontaktiert --today 2026-06-28
python lead.py status test-smoke-gmbh in_klaerung --today 2026-06-29
python lead.py report --today 2026-06-29
```
Expected: Lead angelegt → kontaktiert → `leads/test-smoke-gmbh.md` entsteht, Zeile aus `pipeline.md` weg, report läuft fehlerfrei.

- [ ] **Step 4: Smoke-Test-Artefakte zurückrollen** (Testlead nicht committen)

Run:
```bash
rm -f leads/test-smoke-gmbh.md
python lead.py init   # falls nötig pipeline.md neu seeden
git checkout -- pipeline.md 2>/dev/null || python lead.py init
```
Expected: `pipeline.md` leer, kein Test-Lead in `leads/`.

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/lead/SKILL.md CLAUDE.md
git commit -m "docs: lead-Skill + Repo-Router CLAUDE.md"
```

---

## Self-Review (vom Plan-Autor durchgeführt)

**Spec-Abdeckung:**
- Repo-Struktur → Task 0/9 ✓
- Sammeldatei `pipeline.md` (Tabelle) → Task 1 ✓
- Warme Lead-Datei + Frontmatter → Task 3/4 ✓
- Status-Pipeline (alle 11 Status) → Task 5 (`ALL_STATUSES`) ✓
- Graduierung bei `in_klaerung` → Task 4/5 ✓
- 14-Tage-keine-Antwort (abgeleitet, kein Cron) → Task 6 ✓
- Skill-Operationen neu/status/report/notiz/gewonnen → Task 8 (gewonnen = `status … gewonnen`) ✓
- Integrationsfelder A/C/D reserviert (`schwaeche`, `prototyp`, `ucp`, `roi_these`, `kontakt`) → Task 4 (Frontmatter) ✓
- UWG-§7-Hinweis dokumentiert → Task 9 CLAUDE.md ✓

**Platzhalter-Scan:** keine TODO/TBD; jeder Code-Step enthält vollständigen Code. ✓

**Typ-/Namens-Konsistenz:** `slug`, `today` (date, injiziert), `read_pipeline/write_pipeline`,
`lead_path`, `read_lead/write_lead`, `graduate(status=…)`, `set_status`, `report`-Keys
(`keine_antwort`, `wiedervorlage_faellig`) durchgängig identisch verwendet. ✓

**Offene Mini-Punkte (bewusst):** `gewonnen` als eigenes CLI-Kommando weggelassen (= `status … gewonnen`,
Absprachen-Pflicht über SKILL.md-Regel 4). `prioritaet` default „mittel", manuell anpassbar.
```
