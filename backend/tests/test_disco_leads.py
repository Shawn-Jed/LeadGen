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


def test_create_leads_single_applies_website_and_note(repo):
    run = _run_with("Praxis A")
    discotool.set_status(run, 1, "keine_website")
    discotool.create_leads(repo, run, [1], date(2026, 6, 28),
                           website="praxis-a.de", notiz="starke Bewertungen, kein Web-Auftritt")
    row = leadtool.read_pipeline(repo)[0]
    assert row["website"] == "praxis-a.de"
    assert "starke Bewertungen" in row["notiz"]


def test_create_leads_bulk_ignores_website(repo):
    # website/notiz nur bei Einzel-Übernahme — Bulk darf sie nicht auf alle schmieren.
    run = _run_with("Praxis A", "Praxis B")
    discotool.set_status(run, 1, "keine_website")
    discotool.set_status(run, 2, "keine_website")
    discotool.create_leads(repo, run, "auto", date(2026, 6, 28), website="x.de", notiz="Grund")
    assert all(r["website"] == "" for r in leadtool.read_pipeline(repo))
