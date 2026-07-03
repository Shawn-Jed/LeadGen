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
