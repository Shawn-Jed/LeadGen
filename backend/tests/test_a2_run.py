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
        return HTML_BAD  # irrelevant — sollte nicht aufgerufen werden

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
