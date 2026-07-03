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


def test_cli_report_prints_umlaut_firma_without_crash(repo, capsys, monkeypatch):
    monkeypatch.chdir(repo)
    lead.main(["neu", "Müller Sanitär GmbH", "--today", "2026-06-01"])
    lead.main(["status", "mueller-sanitaer-gmbh", "kontaktiert", "--today", "2026-06-01"])
    rc = lead.main(["report", "--today", "2026-07-10"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Müller Sanitär GmbH" in out


def test_cli_unknown_status_returns_error(repo, capsys, monkeypatch):
    monkeypatch.chdir(repo)
    lead.main(["neu", "Test GmbH", "--today", "2026-06-18"])
    rc = lead.main(["status", "test-gmbh", "quatsch", "--today", "2026-06-18"])
    assert rc == 1


def test_cli_wiedervorlage(repo, capsys, monkeypatch):
    monkeypatch.chdir(repo)
    lead.main(["neu", "Kalt GmbH", "--today", "2026-06-01"])
    rc = lead.main(["wiedervorlage", "kalt-gmbh", "2026-06-28"])
    assert rc == 0
    assert leadtool.read_pipeline(repo)[0]["wiedervorlage"] == "2026-06-28"
    rc_bad = lead.main(["wiedervorlage", "kalt-gmbh", "kaputt"])
    assert rc_bad == 1
