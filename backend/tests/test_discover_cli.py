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
