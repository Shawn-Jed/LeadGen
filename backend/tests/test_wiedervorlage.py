import leadtool
from datetime import date


def test_wiedervorlage_on_cold_lead_sets_pipeline_and_report_flags(repo):
    leadtool.add_lead(repo, "Kalt GmbH", today=date(2026, 6, 1))
    leadtool.set_wiedervorlage(repo, "kalt-gmbh", "2026-06-28")
    assert leadtool.read_pipeline(repo)[0]["wiedervorlage"] == "2026-06-28"
    rep = leadtool.report(repo, today=date(2026, 6, 28))
    assert any(c["slug"] == "kalt-gmbh" for c in rep["wiedervorlage_faellig"])


def test_wiedervorlage_on_warm_lead_sets_frontmatter(repo):
    leadtool.add_lead(repo, "Warm GmbH", today=date(2026, 6, 1))
    leadtool.set_status(repo, "warm-gmbh", "in_klaerung", today=date(2026, 6, 10))
    leadtool.set_wiedervorlage(repo, "warm-gmbh", "2026-07-05")
    meta, _ = leadtool.read_lead(repo, "warm-gmbh")
    assert meta["wiedervorlage"] == "2026-07-05"


def test_wiedervorlage_invalid_date_raises(repo):
    leadtool.add_lead(repo, "Kalt GmbH", today=date(2026, 6, 1))
    try:
        leadtool.set_wiedervorlage(repo, "kalt-gmbh", "5. Juli")
        assert False
    except ValueError:
        pass


def test_wiedervorlage_unknown_slug_raises(repo):
    try:
        leadtool.set_wiedervorlage(repo, "gibtsnicht", "2026-07-05")
        assert False
    except ValueError:
        pass
