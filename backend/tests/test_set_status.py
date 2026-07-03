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
