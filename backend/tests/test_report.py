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


def test_report_no_answer_boundary_strictly_greater_than_14(repo):
    """'über 14 Tage' = strikt >14: Tag 14 feuert NICHT, Tag 15 schon."""
    leadtool.add_lead(repo, "Grenz GmbH", today=date(2026, 6, 1))
    leadtool.set_status(repo, "grenz-gmbh", "kontaktiert", today=date(2026, 6, 1))
    # genau 14 Tage später → NICHT geflaggt
    assert leadtool.report(repo, today=date(2026, 6, 15))["keine_antwort"] == []
    # 15 Tage später → geflaggt
    rep = leadtool.report(repo, today=date(2026, 6, 16))
    assert [c["slug"] for c in rep["keine_antwort"]] == ["grenz-gmbh"]
    assert rep["keine_antwort"][0]["tage"] == 15
