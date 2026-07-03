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
