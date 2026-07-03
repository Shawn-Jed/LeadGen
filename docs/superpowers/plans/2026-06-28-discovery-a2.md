# Discovery A2 (Tier 2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tier-2-Website-Analyse — für Kandidaten mit bekannter Website HTML laden, Schwächen-Signale detektieren (kein HTTPS, kein Viewport, veraltet, kein Impressum, kein Kontaktformular), Opportunity-Score erhöhen, und Status auf `analysiert` setzen.

**Architecture:** Neue reine Funktionen in `discotool.py` (anhängen, kein Umbau). `http_get` ist der reale Netz-Call; `analyse_run` erhält `fetch_html_fn` als Injectable → Tests laufen ohne Netz. `beautifulsoup4` nur für HTML-Parsing (kommt in `requirements-dev.txt`). Neues Subkommando `analyse <run>` in `discover.py`. Data-Shape-Kontrakt: A2 fügt nur `tier2`-Key hinzu und erhöht `score`; alle existierenden Keys bleiben unberührt; `tier3`-Key reserviert für A3.

**Tech Stack:** Python 3.11+ (stdlib `urllib`, `re`, `datetime`), `beautifulsoup4` (HTML-Parsing), pytest. Keine weitere neue Abhängigkeit.

---

## File Structure

```
Leads/
├── discotool.py              # Ergänzt: http_get, analyse_site, score_tier2, analyse_run
├── discover.py               # Ergänzt: Subcommand `analyse <run>`
├── requirements-dev.txt      # beautifulsoup4 hinzufügen
├── tests/
│   ├── test_a2_analyse.py        # Task 1 + 2: analyse_site + score_tier2 (reine HTML-Fixtures)
│   ├── test_a2_run.py            # Task 3: analyse_run mit inject. fetch_html_fn
│   └── test_a2_cli.py            # Task 4: CLI `analyse <run>`
└── .claude/skills/discover/SKILL.md   # Task 5: analyse-Schritt einfügen
```

`discotool.py` importiert `bs4` (BeautifulSoup) — kein Zyklus zu leadtool. Tests benötigen die
`repo`-Fixture aus `tests/conftest.py` (Subsystem B) für Task 3+4.

**Data-Shape-Kontrakt (A3 verlässt sich darauf):**
A2 DARF NUR:
- `candidate["tier2"]` = signals-dict (neu)
- `candidate["score"]` += score_tier2-Wert (bestehender Key)
- `candidate["befund"]` überschreiben (bestehender Key)
- `candidate["status"]` auf `"analysiert"` setzen (bestehender Key)

A2 DARF NICHT:
- `tier3`-Key anfassen (reserviert A3)
- `score_tier1`-Wert zurücksetzen
- `new_run`, `lead_angelegt`, `gefundene_url`, `osm_id`, `firma`, `adresse`, `website`, `telefon`, `id` anfassen

---

## Task 1: `analyse_site` (reine HTML-Parsing-Funktion)

**Files:** `tests/test_a2_analyse.py` (neu), `discotool.py` (anhängen)

### Step 1: Failing Test

```python
# tests/test_a2_analyse.py
import discotool

HTML_MOBILE = """<html><head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Test</title></head>
<body><p>Copyright 2024 Muster GmbH</p>
<a href="/impressum">Impressum</a>
<form action="/kontakt"><input name="email"/><button>Senden</button></form>
</body></html>"""

HTML_LEGACY = """<html><head><title>Old Site</title></head>
<body><p>Alle Rechte vorbehalten &copy; 2009 Altbau GmbH</p>
<p>Kontakt: info@altbau.de</p>
</body></html>"""

HTML_KONTAKT_LINK = """<html><head><title>Kontakt</title></head>
<body><a href="/kontakt">Kontakt aufnehmen</a></body></html>"""

HTML_MINIMAL = """<html><body><p>Hallo Welt</p></body></html>"""


def test_analyse_site_https_detected():
    sig = discotool.analyse_site(HTML_MINIMAL, "https://example.de", jahr=2026)
    assert sig["https"] is True

    sig2 = discotool.analyse_site(HTML_MINIMAL, "http://example.de", jahr=2026)
    assert sig2["https"] is False


def test_analyse_site_viewport_present():
    sig = discotool.analyse_site(HTML_MOBILE, "https://example.de", jahr=2026)
    assert sig["viewport"] is True


def test_analyse_site_viewport_absent():
    sig = discotool.analyse_site(HTML_LEGACY, "http://example.de", jahr=2026)
    assert sig["viewport"] is False


def test_analyse_site_copyright_jahr_extracted():
    sig = discotool.analyse_site(HTML_LEGACY, "http://example.de", jahr=2026)
    assert sig["copyright_jahr"] == 2009


def test_analyse_site_copyright_jahr_none_when_absent():
    sig = discotool.analyse_site(HTML_MINIMAL, "https://example.de", jahr=2026)
    assert sig["copyright_jahr"] is None


def test_analyse_site_veraltet_old_copyright():
    # 2009 < 2026 - 2 = 2024 → veraltet
    sig = discotool.analyse_site(HTML_LEGACY, "http://example.de", jahr=2026)
    assert sig["veraltet"] is True


def test_analyse_site_veraltet_recent_copyright():
    # 2024 == 2026 - 2 → nicht veraltet (grenze: < today_year - 2)
    sig = discotool.analyse_site(HTML_MOBILE, "https://example.de", jahr=2026)
    assert sig["veraltet"] is False


def test_analyse_site_veraltet_false_when_no_copyright():
    sig = discotool.analyse_site(HTML_MINIMAL, "https://example.de", jahr=2026)
    assert sig["veraltet"] is False


def test_analyse_site_impressum_present():
    sig = discotool.analyse_site(HTML_MOBILE, "https://example.de", jahr=2026)
    assert sig["impressum"] is True


def test_analyse_site_impressum_absent():
    sig = discotool.analyse_site(HTML_LEGACY, "http://example.de", jahr=2026)
    assert sig["impressum"] is False


def test_analyse_site_kontaktformular_via_form():
    sig = discotool.analyse_site(HTML_MOBILE, "https://example.de", jahr=2026)
    assert sig["kontaktformular"] is True


def test_analyse_site_kontaktformular_via_link():
    sig = discotool.analyse_site(HTML_KONTAKT_LINK, "https://example.de", jahr=2026)
    assert sig["kontaktformular"] is True


def test_analyse_site_kontaktformular_absent():
    sig = discotool.analyse_site(HTML_LEGACY, "http://example.de", jahr=2026)
    assert sig["kontaktformular"] is False


def test_analyse_site_returns_all_keys():
    sig = discotool.analyse_site(HTML_MINIMAL, "https://example.de", jahr=2026)
    assert set(sig.keys()) == {"https", "viewport", "copyright_jahr", "veraltet", "impressum", "kontaktformular"}
```

### Step 2: Run → FAIL

```
python -m pytest tests/test_a2_analyse.py -v
```
Expected: FAIL (`has no attribute 'analyse_site'`)

### Step 3: Add `beautifulsoup4` to `requirements-dev.txt`

Read `requirements-dev.txt` first (oder erstelle es falls fehlend), dann anhängen:

```
beautifulsoup4>=4.12
```

Install: `pip install beautifulsoup4`

### Step 4: Implement — append to `discotool.py`

```python
import re as _re

from bs4 import BeautifulSoup as _BS


def analyse_site(html: str, url: str, *, jahr: int) -> dict:
    """Reine Funktion: HTML-String + URL → Tier-2-Signale.

    Parameters
    ----------
    html : str
        Rohes HTML der Seite.
    url : str
        Effektive URL der Seite (für https-Erkennung).
    jahr : int
        Heutiges Jahr (injiziert für testbarkeit, z.B. 2026).
    """
    soup = _BS(html, "html.parser")

    # --- https ---
    has_https = url.lower().startswith("https://")

    # --- viewport ---
    vp_tag = soup.find("meta", attrs={"name": lambda v: v and v.lower() == "viewport"})
    has_viewport = vp_tag is not None

    # --- copyright_jahr ---
    text = soup.get_text(" ", strip=True)
    jahre = [int(m) for m in _re.findall(r"\b(19\d{2}|20\d{2})\b", text)]
    copyright_jahr = max(jahre) if jahre else None

    # --- veraltet ---
    veraltet = (copyright_jahr is not None) and (copyright_jahr < jahr - 2)

    # --- impressum ---
    imp_link = soup.find(lambda tag: tag.name in ("a", "span", "p", "li", "div")
                         and "impressum" in (tag.get_text() or "").lower())
    has_impressum = imp_link is not None

    # --- kontaktformular ---
    has_form = soup.find("form") is not None
    kontakt_link = soup.find(lambda tag: tag.name in ("a", "span", "p", "li", "button")
                              and "kontakt" in (tag.get_text() or "").lower())
    has_kontakt = has_form or (kontakt_link is not None)

    return {
        "https": has_https,
        "viewport": has_viewport,
        "copyright_jahr": copyright_jahr,
        "veraltet": veraltet,
        "impressum": has_impressum,
        "kontaktformular": has_kontakt,
    }
```

### Step 5: Run → PASS

```
python -m pytest tests/test_a2_analyse.py -v
```
Expected: alle 14 Tests grün.

### Step 6: Commit

```bash
git add discotool.py requirements-dev.txt tests/test_a2_analyse.py
git commit -m "feat(disco): analyse_site (Tier-2-HTML-Signale, rein/testbar)"
```

---

## Task 2: `score_tier2`

**Files:** `tests/test_a2_analyse.py` (erweitern), `discotool.py` (anhängen)

### Step 1: Failing Test — append to `tests/test_a2_analyse.py`

```python
# --- score_tier2 ---

def test_score_tier2_all_ok():
    signals = {"https": True, "viewport": True, "veraltet": False,
               "impressum": True, "kontaktformular": True}
    assert discotool.score_tier2(signals) == 0


def test_score_tier2_no_https():
    signals = {"https": False, "viewport": True, "veraltet": False,
               "impressum": True, "kontaktformular": True}
    assert discotool.score_tier2(signals) == 15


def test_score_tier2_no_viewport():
    signals = {"https": True, "viewport": False, "veraltet": False,
               "impressum": True, "kontaktformular": True}
    assert discotool.score_tier2(signals) == 20


def test_score_tier2_veraltet():
    signals = {"https": True, "viewport": True, "veraltet": True,
               "impressum": True, "kontaktformular": True}
    assert discotool.score_tier2(signals) == 15


def test_score_tier2_no_impressum():
    signals = {"https": True, "viewport": True, "veraltet": False,
               "impressum": False, "kontaktformular": True}
    assert discotool.score_tier2(signals) == 10


def test_score_tier2_no_kontakt():
    signals = {"https": True, "viewport": True, "veraltet": False,
               "impressum": True, "kontaktformular": False}
    assert discotool.score_tier2(signals) == 10


def test_score_tier2_all_bad():
    signals = {"https": False, "viewport": False, "veraltet": True,
               "impressum": False, "kontaktformular": False}
    assert discotool.score_tier2(signals) == 70  # 15+20+15+10+10


def test_score_tier2_partial():
    # kein https + kein viewport + kein impressum
    signals = {"https": False, "viewport": False, "veraltet": False,
               "impressum": False, "kontaktformular": True}
    assert discotool.score_tier2(signals) == 45  # 15+20+10
```

### Step 2: Run → FAIL

```
python -m pytest tests/test_a2_analyse.py -v -k "score_tier2"
```
Expected: FAIL (`has no attribute 'score_tier2'`)

### Step 3: Implement — append to `discotool.py`

```python
def score_tier2(signals: dict) -> int:
    """Additive Aufschläge auf Basis der Tier-2-Signale.

    Aufschläge:
    - kein HTTPS       → +15
    - kein Viewport    → +20
    - veraltet         → +15
    - kein Impressum   → +10
    - kein Kontakt     → +10
    """
    score = 0
    if not signals.get("https"):
        score += 15
    if not signals.get("viewport"):
        score += 20
    if signals.get("veraltet"):
        score += 15
    if not signals.get("impressum"):
        score += 10
    if not signals.get("kontaktformular"):
        score += 10
    return score
```

### Step 4: Run → PASS

```
python -m pytest tests/test_a2_analyse.py -v
```
Expected: alle Tests (analyse_site + score_tier2) grün.

### Step 5: Commit

```bash
git add discotool.py tests/test_a2_analyse.py
git commit -m "feat(disco): score_tier2 (additive Aufschläge Tier 2)"
```

---

## Task 3: `http_get` + `analyse_run`

**Files:** `tests/test_a2_run.py` (neu), `discotool.py` (anhängen)

### Step 1: Failing Test

```python
# tests/test_a2_run.py
from datetime import date
from pathlib import Path

import discotool

# --- HTML-Fixtures ---

HTML_OK = """<html><head>
<meta name="viewport" content="width=device-width">
<title>Gut</title></head>
<body><p>Copyright 2025</p>
<a href="/impressum">Impressum</a>
<form><input name="email"/></form>
</body></html>"""

HTML_BAD = """<html><head><title>Alt</title></head>
<body><p>Copyright 2009</p></body></html>"""


def _run_with_website(url: str = "https://gut.de"):
    """Erzeugt einen Minimal-Run mit einem Kandidaten mit Website."""
    cands = [{"firma": "Gut GmbH", "website": url,
              "adresse": "Hauptstr. 1", "telefon": "", "osm_id": "node/1"}]
    run = discotool.new_run("Zahnärzte", "Eimsbüttel", cands, date(2026, 6, 28))
    # Status manuell auf hat_website setzen (new_run tut das schon weil website != "")
    assert run["kandidaten"][0]["status"] == "hat_website"
    return run


def _run_with_gefundene_url():
    """Kandidat hat kein OSM-website, aber gefundene_url (gesetzt durch A1-WebSearch)."""
    cands = [{"firma": "Friseur Y", "website": "",
              "adresse": "Nebenstr. 2", "telefon": "", "osm_id": "node/2"}]
    run = discotool.new_run("Friseure", None, cands, date(2026, 6, 28))
    discotool.set_status(run, 1, "hat_website", "https://friseur-y.de")
    return run


def _run_without_url():
    """Kandidat ohne URL — wird übersprungen."""
    cands = [{"firma": "Kein Web", "website": "",
              "adresse": "Irgendwo", "telefon": "", "osm_id": "node/3"}]
    run = discotool.new_run("Kfz", None, cands, date(2026, 6, 28))
    # status bleibt website_unklar → kein analyse
    return run


# --- Tests ---

def test_analyse_run_stores_tier2_and_bumps_score():
    run = _run_with_website("https://gut.de")
    fetch_calls = []

    def fake_fetch(url):
        fetch_calls.append(url)
        return HTML_OK

    summary = discotool.analyse_run(
        Path("."), run, fetch_html_fn=fake_fetch, jahr=2026
    )

    c = run["kandidaten"][0]
    assert c["status"] == "analysiert"
    assert "tier2" in c
    assert isinstance(c["tier2"], dict)
    # HTML_OK hat viewport+impressum+form, https=True, nicht veraltet → score_tier2 = 0
    assert c["score"] == 0 + 0  # score_tier1 war 0 (hatte website), tier2-Aufschlag 0
    assert fetch_calls == ["https://gut.de"]
    assert summary["analysiert"] == 1
    assert summary["fehler"] == []


def test_analyse_run_bumps_score_for_bad_site():
    run = _run_with_website("http://alt.de")  # http → kein HTTPS
    def fake_fetch(url):
        return HTML_BAD  # alt, kein viewport, kein impressum, kein kontakt

    discotool.analyse_run(Path("."), run, fetch_html_fn=fake_fetch, jahr=2026)

    c = run["kandidaten"][0]
    assert c["status"] == "analysiert"
    t2 = c["tier2"]
    assert t2["https"] is False
    assert t2["viewport"] is False
    assert t2["veraltet"] is True  # 2009 < 2024
    assert t2["impressum"] is False
    assert t2["kontaktformular"] is False
    assert c["score"] == 0 + 70  # tier2-Aufschlag 15+20+15+10+10


def test_analyse_run_uses_gefundene_url_when_no_osm_website():
    run = _run_with_gefundene_url()
    fetched = []
    def fake_fetch(url):
        fetched.append(url)
        return HTML_OK

    discotool.analyse_run(Path("."), run, fetch_html_fn=fake_fetch, jahr=2026)

    assert fetched == ["https://friseur-y.de"]
    assert run["kandidaten"][0]["status"] == "analysiert"


def test_analyse_run_skips_candidate_without_url():
    run = _run_without_url()
    fetch_calls = []
    def fake_fetch(url):
        fetch_calls.append(url)
        return HTML_MINIMAL  # irrelevant — sollte nicht aufgerufen werden

    summary = discotool.analyse_run(Path("."), run, fetch_html_fn=fake_fetch, jahr=2026)

    assert fetch_calls == []
    assert run["kandidaten"][0]["status"] == "website_unklar"  # unverändert
    assert "tier2" not in run["kandidaten"][0]
    assert summary["analysiert"] == 0


def test_analyse_run_fetch_error_records_befund_and_continues():
    """Fetch-Fehler → befund gesetzt, status bleibt hat_website, kein Crash."""
    run = _run_with_website("https://kaputtsite.de")

    def fake_fetch_error(url):
        raise OSError("connection refused")

    summary = discotool.analyse_run(Path("."), run, fetch_html_fn=fake_fetch_error, jahr=2026)

    c = run["kandidaten"][0]
    assert "Seite nicht erreichbar" in c["befund"]
    assert c["status"] == "hat_website"  # unverändert — kein analysiert
    assert "tier2" not in c
    assert len(summary["fehler"]) == 1
    assert "kaputtsite.de" in summary["fehler"][0]


def test_analyse_run_does_not_touch_tier3_key():
    """A2 darf tier3 nicht setzen — reserviert für A3."""
    run = _run_with_website("https://gut.de")
    run["kandidaten"][0]["tier3"] = {"placeholder": True}  # simuliere späteres A3

    def fake_fetch(url):
        return HTML_OK

    discotool.analyse_run(Path("."), run, fetch_html_fn=fake_fetch, jahr=2026)

    assert run["kandidaten"][0]["tier3"] == {"placeholder": True}  # unberührt


def test_analyse_run_does_not_overwrite_lead_angelegt():
    """lead_angelegt darf A2 nicht anfassen."""
    run = _run_with_website("https://gut.de")
    run["kandidaten"][0]["lead_angelegt"] = True  # bereits gesetzt

    def fake_fetch(url):
        return HTML_OK

    discotool.analyse_run(Path("."), run, fetch_html_fn=fake_fetch, jahr=2026)

    assert run["kandidaten"][0]["lead_angelegt"] is True


def test_http_get_is_callable():
    """Existenz + Signatur prüfen — KEIN echter Netz-Call."""
    assert callable(discotool.http_get)
```

### Step 2: Run → FAIL

```
python -m pytest tests/test_a2_run.py -v
```
Expected: FAIL (`has no attribute 'http_get'`)

### Step 3: Implement — append to `discotool.py`

```python
def http_get(url: str) -> str:
    """Realer HTTP-GET einer Website-URL; gibt HTML-String zurück.

    Timeout 20 s. User-Agent konsistent mit http_overpass.
    Raises OSError / urllib.error.URLError bei Netz- oder HTTP-Fehlern.
    NICHT direkt unit-getestet — analyse_run erhält fetch_html_fn-Injektion.
    """
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "SelfworkLeads/0.1 (Hamburg lead discovery; shje@delta-sport.com)"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


def _effective_url(cand: dict) -> str:
    """Gibt die effektive URL eines Kandidaten zurück: website-Tag oder gefundene_url."""
    return cand.get("website") or cand.get("gefundene_url") or ""


def analyse_run(
    root,  # Path — unused in A2 but mirrors API of create_leads for symmetry
    run: dict,
    *,
    fetch_html_fn=None,
    jahr: int,
) -> dict:
    """Analysiert alle hat_website-Kandidaten eines Runs mit Tier-2-Heuristiken.

    Für jeden Kandidaten mit Status ``hat_website`` und nicht-leerer URL:
    - HTML holen (via fetch_html_fn oder http_get)
    - analyse_site ausführen
    - candidate["tier2"] = signals setzen
    - candidate["score"] += score_tier2(signals)
    - candidate["befund"] aktualisieren
    - candidate["status"] = "analysiert"

    Bei Fetch-Fehler: befund = "Seite nicht erreichbar: <exc>"; Status unverändert.

    A2-Kontrakt: nur tier2, score, befund, status werden mutiert.
    tier3, lead_angelegt, gefundene_url, osm_id etc. bleiben unberührt.

    Parameters
    ----------
    root : Path
        Repo-Root (Konventions-Parameter; in A2 ungenutzt).
    run : dict
        Run-dict (mutiert in-place).
    fetch_html_fn : callable | None
        Injizierbarer HTTP-Getter (url -> str). Fällt auf http_get zurück.
        In Tests immer angeben — kein echter Netz-Call.
    jahr : int
        Heutiges Jahr (für veraltet-Erkennung injiziert).

    Returns
    -------
    dict mit Keys:
        ``analysiert`` (int): Anzahl erfolgreich analysierter Kandidaten.
        ``fehler`` (list[str]): Fehlermeldungen je fehlgeschlagenem Fetch.
    """
    fetch_fn = fetch_html_fn if fetch_html_fn is not None else http_get
    analysiert_count = 0
    fehler_list: list[str] = []

    for cand in run["kandidaten"]:
        if cand.get("status") != "hat_website":
            continue
        url = _effective_url(cand)
        if not url:
            continue
        try:
            html = fetch_fn(url)
        except Exception as exc:
            cand["befund"] = f"Seite nicht erreichbar: {exc}"
            fehler_list.append(f"{url}: {exc}")
            continue

        signals = analyse_site(html, url, jahr=jahr)
        t2_score = score_tier2(signals)

        cand["tier2"] = signals
        cand["score"] = cand.get("score", 0) + t2_score
        # Befund: kompakte Mängelliste
        maengel = []
        if not signals["https"]:
            maengel.append("kein HTTPS")
        if not signals["viewport"]:
            maengel.append("nicht mobil")
        if signals["veraltet"]:
            maengel.append(f"veraltet ({signals['copyright_jahr']})")
        if not signals["impressum"]:
            maengel.append("kein Impressum")
        if not signals["kontaktformular"]:
            maengel.append("kein Kontaktformular")
        cand["befund"] = ("Tier-2-Mängel: " + ", ".join(maengel)) if maengel else "Tier-2: keine groben Mängel"
        cand["status"] = "analysiert"
        analysiert_count += 1

    return {"analysiert": analysiert_count, "fehler": fehler_list}
```

### Step 4: Run → PASS

```
python -m pytest tests/test_a2_run.py -v
```
Expected: alle 8 Tests grün.

### Step 5: Volle Suite (Tasks 1–3)

```
python -m pytest tests/test_a2_analyse.py tests/test_a2_run.py -v
```
Expected: alle ~22 Tests grün.

### Step 6: Commit

```bash
git add discotool.py tests/test_a2_run.py
git commit -m "feat(disco): http_get + analyse_run (Tier-2-Website-Analyse, inject. fetch)"
```

---

## Task 4: CLI-Subkommando `analyse <run>`

**Files:** `discover.py` (erweitern), `tests/test_a2_cli.py` (neu)

### Step 1: Failing Test

```python
# tests/test_a2_cli.py
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import discover   # noqa: E402
import discotool  # noqa: E402

HTML_MIXED = """<html><head>
<meta name="viewport" content="width=device-width">
<title>Praxis</title></head>
<body><p>Copyright 2009 Alte Praxis</p>
<a href="/impressum">Impressum</a>
</body></html>"""


def test_cli_analyse_updates_candidate(repo, capsys, monkeypatch):
    """Kompletter Durchlauf: scan (gemockt) → analyse (gemockt) → Kandidat aktualisiert."""
    monkeypatch.chdir(repo)

    # Schritt 1: Run erzeugen via scan (Overpass gemockt)
    SAMPLE = {"elements": [
        {"type": "node", "id": 10, "tags": {
            "name": "Zahnarzt Web", "amenity": "dentist", "website": "https://zahnarzt-web.de"}},
        {"type": "node", "id": 11, "tags": {
            "name": "Zahnarzt Kein Web", "amenity": "dentist"}},
    ]}
    monkeypatch.setattr(discotool, "http_overpass", lambda q: SAMPLE)
    assert discover.main(["scan", "Zahnärzte", "Eimsbüttel", "--today", "2026-06-28"]) == 0

    runs = list((repo / "discovery").glob("*.json"))
    assert len(runs) == 1
    run_arg = str(runs[0])

    # Schritt 2: analyse — http_get mit HTML-Fixture ersetzen
    monkeypatch.setattr(discotool, "http_get", lambda url: HTML_MIXED)
    rc = discover.main(["analyse", run_arg, "--today", "2026-06-28"])
    assert rc == 0

    # Run nachladen und prüfen
    run = discotool.load_run(Path(run_arg))
    cands_by_id = {c["id"]: c for c in run["kandidaten"]}

    # Zahnarzt Web (id 1) hatte hat_website → muss analysiert sein
    analysiert = cands_by_id[1]
    assert analysiert["status"] == "analysiert"
    assert "tier2" in analysiert
    # HTML_MIXED: https=True(url), viewport=True, veraltet=True(2009), impressum=True, kontakt=False
    # → score_tier2 = 15 (veraltet) + 10 (kein kontakt) = 25
    assert analysiert["tier2"]["veraltet"] is True
    assert analysiert["tier2"]["kontaktformular"] is False
    assert analysiert["score"] == 25  # tier1 war 0 (hatte website) + tier2 25

    # Zahnarzt Kein Web (id 2) hatte website_unklar → unberührt
    unklar = cands_by_id[2]
    assert unklar["status"] == "website_unklar"
    assert "tier2" not in unklar


def test_cli_analyse_missing_run_returns_error(repo, capsys, monkeypatch):
    monkeypatch.chdir(repo)
    rc = discover.main(["analyse", "discovery/does-not-exist.json", "--today", "2026-06-28"])
    assert rc == 1
    out = capsys.readouterr().out
    assert "Fehler" in out


def test_cli_analyse_prints_summary(repo, capsys, monkeypatch):
    """Smoke: summary-Ausgabe enthält analysiert-Count."""
    monkeypatch.chdir(repo)

    SAMPLE = {"elements": [
        {"type": "node", "id": 20, "tags": {
            "name": "Praxis Z", "amenity": "dentist", "website": "https://praxis-z.de"}},
    ]}
    monkeypatch.setattr(discotool, "http_overpass", lambda q: SAMPLE)
    assert discover.main(["scan", "Zahnärzte", "Altona", "--today", "2026-06-28"]) == 0
    runs = list((repo / "discovery").glob("*.json"))
    run_arg = str(runs[0])

    monkeypatch.setattr(discotool, "http_get", lambda url: HTML_MIXED)
    discover.main(["analyse", run_arg, "--today", "2026-06-28"])

    out = capsys.readouterr().out
    assert "analysiert" in out.lower()
```

### Step 2: Run → FAIL

```
python -m pytest tests/test_a2_cli.py -v
```
Expected: FAIL (`argument cmd: invalid choice: 'analyse'`)

### Step 3: Implement — erweitere `discover.py`

Zwei Stellen in `discover.py` ändern:

**Stelle A: Subparser registrieren** — nach dem `pu`-Block (vor `args = p.parse_args(argv)`):

```python
    pa = sub.add_parser("analyse", help="Tier-2-HTML-Analyse für hat_website-Kandidaten")
    pa.add_argument("run")
    pa.add_argument("--today", default=None)
```

**Stelle B: Handler einfügen** — in der `try`-Block-if-elif-Kette, nach dem `uebernehmen`-Zweig:

```python
        elif args.cmd == "analyse":
            from datetime import date as _date
            path = Path(args.run)
            run = discotool.load_run(path)
            today_val = _today(args)
            summary = discotool.analyse_run(root, run, jahr=today_val.year)
            discotool.save_run(path, run)
            print(f"Analyse: {summary['analysiert']} Kandidaten analysiert.")
            if summary["fehler"]:
                print(f"  Fehler ({len(summary['fehler'])}):")
                for f in summary["fehler"]:
                    print(f"    {f}")
```

### Step 4: Run → PASS

```
python -m pytest tests/test_a2_cli.py -v
```
Expected: 3 Tests grün.

### Step 5: Volle Suite

```
python -m pytest -q
```
Expected: alle Tests grün (Subsystem B + A1 + A2, ~40+ Tests).

### Step 6: Commit

```bash
git add discover.py tests/test_a2_cli.py
git commit -m "feat(disco): CLI-Subkommando analyse (Tier-2, discover.py)"
```

---

## Task 5: `SKILL.md` — `analyse`-Schritt einfügen

**Files:** `.claude/skills/discover/SKILL.md` (ändern)

### Step 1: Lesen + Prüfen

Lese `.claude/skills/discover/SKILL.md`. Lokalisiere den Abschnitt `## Ablauf (Tier 1)`.

### Step 2: Ablauf-Abschnitt ersetzen

Ersetze den kompletten `## Ablauf (Tier 1)`-Block durch:

````markdown
## Ablauf (Tier 1 + Tier 2)

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

4. **Tier-2-Analyse** (für alle `hat_website`-Kandidaten):
   `python discover.py analyse <run-datei>`
   Lädt HTML, prüft: HTTPS, Viewport-Meta, Copyright-Jahr (veraltet?), Impressum, Kontaktformular.
   Speichert `tier2`-Signale + erhöht Score. Status wird `analysiert`.
   Anschließend `show` aufrufen, um Tier-2-Befunde zu sehen.

5. **Übernehmen:** `python discover.py uebernehmen <run> auto`
   Legt für alle als `keine_website` bestätigten Funde automatisch Leads an (Schwäche:
   „keine auffindbare Website"). Tier-2-analysierte Kandidaten mit hohem Score können
   separat mit expliziten IDs übernommen werden: `uebernehmen <run> 1,3,5`.
   Duplikate werden übersprungen.

## Tier-2-Mängel im Befund

Analysierte Kandidaten erhalten im Feld `befund` eine Mängelliste, z.B.:
`Tier-2-Mängel: kein HTTPS, nicht mobil, veraltet (2009), kein Impressum`

Score-Aufschläge: kein HTTPS +15 / nicht mobil +20 / veraltet +15 / kein Impressum +10 / kein Kontaktformular +10.
````

Außerdem: Kopfzeile des Skills anpassen — ersetze `description`-Wert um `analyse` zu erwähnen:

```yaml
description: Use when looking for new leads in Hamburg — Betriebe einer Branche finden + Website-Schwächen prüfen (Tier 1+2). Trigger: "finde Leads", "scan Branche X in Stadtteil Y", "discovery", "neue Kandidaten", "website analysieren", "tier 2".
```

Und im `## Ehrliche Grenzen`-Abschnitt ergänzen:

```
Tier-2-HTML-Fetch: manche Seiten blocken Bots (403/timeout) → Fehler werden protokolliert,
kein Crash. Seite dann ggf. manuell prüfen.
```

### Step 3: Commit

```bash
git add .claude/skills/discover/SKILL.md
git commit -m "docs(disco): SKILL.md — analyse-Schritt + Tier-2-Beschreibung"
```

---

## Self-Review (vom Plan-Autor)

**Spec-Abdeckung (A2):**
- `http_get` (urllib GET, User-Agent, Timeout) → Task 3 ✓
- `analyse_site` (https, viewport, copyright_jahr, veraltet, impressum, kontaktformular) → Task 1 ✓
- `analyse_site` Signatur `(html, url, *, jahr)` — year-param injizierbar → Task 1 ✓
- `score_tier2` mit allen 5 Aufschlägen (15+20+15+10+10) → Task 2 ✓
- `analyse_run(root, run, *, fetch_html_fn, jahr)` → Task 3 ✓
  - hat_website-Filter ✓
  - effective_url (website ODER gefundene_url) ✓
  - tier2 + score + befund + status setzen ✓
  - Fetch-Fehler: befund, kein Crash ✓
  - Data-Shape-Kontrakt: tier3 unberührt ✓
- CLI `analyse <run>` → Task 4 ✓
- `beautifulsoup4` in requirements-dev.txt → Task 1 ✓
- SKILL.md analyse-Schritt → Task 5 ✓
- „kein echter Netz-Call im Test" → fetch_html_fn-Injektion in Tasks 3+4 ✓

**Platzhalter-Scan:** keine TODO/TBD in Code-Blöcken; alle Implementierungen vollständig. ✓

**Data-Shape-Kontrakt:**
- A2 schreibt nur: `tier2` (neu), `score` (+=), `befund` (update), `status` (→ analysiert). ✓
- A2 liest `tier3` nicht und schreibt ihn nicht. ✓
- `new_run`, `score_tier1`, `lead_angelegt`, `gefundene_url`, `osm_id`, `firma`, `adresse`,
  `website`, `telefon`, `id` werden von A2 nicht mutiert. ✓

**Typ-/Namens-Konsistenz:**
- `analyse_site(html, url, *, jahr)` — identisch in discotool.py, Tests, SKILL.md. ✓
- `score_tier2(signals)` — durchgängig. ✓
- `analyse_run(root, run, *, fetch_html_fn, jahr)` — identisch in discotool.py und CLI-Handler. ✓
- `http_get(url) -> str` — identisch; monkeypatched in CLI-Test. ✓
- Kandidaten-Status `"analysiert"` — in STATUSES (A1, Task 4) bereits enthalten. ✓
- `summary = {"analysiert": int, "fehler": list[str]}` — konsistent Task 3 + Task 4. ✓
- Commit-Präfixe `feat(disco):` / `docs(disco):` — wie A1. ✓

**Offene Mini-Punkte (bewusst):**
- BeautifulSoup mit `html.parser` (stdlib, kein lxml nötig) — reicht für strukturelle Checks. ✓
- copyright_jahr = max aller gefundenen Jahrzahlen — robust, aber nicht DSGVO-kritisch,
  da nur Jahreszahlen aus öffentlicher Website extrahiert. ✓
- `_effective_url` priorisiert `website` über `gefundene_url` — konsistent mit A1-Semantik. ✓
- A3-Anbindungspunkt: `tier3`-Key reserviert, `status == "analysiert"` als Startbedingung. ✓
