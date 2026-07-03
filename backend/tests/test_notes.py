import leadtool
from datetime import date


def test_note_on_cold_lead_appends_to_notiz_column(repo):
    leadtool.add_lead(repo, "Müller Sanitär", today=date(2026, 6, 18))
    leadtool.add_note(repo, "mueller-sanitaer", "Telefon klingelt nicht", today=date(2026, 6, 19))
    row = leadtool.read_pipeline(repo)[0]
    assert "Telefon klingelt nicht" in row["notiz"]


def test_note_on_warm_lead_appends_to_notizen_section(repo):
    leadtool.add_lead(repo, "Müller Sanitär", today=date(2026, 6, 18))
    leadtool.set_status(repo, "mueller-sanitaer", "in_klaerung", today=date(2026, 6, 25))
    leadtool.add_note(repo, "mueller-sanitaer", "will Festpreis bis Ende Juli", today=date(2026, 6, 26))
    _, body = leadtool.read_lead(repo, "mueller-sanitaer")
    assert "2026-06-26" in body
    assert "will Festpreis bis Ende Juli" in body


def test_note_warm_multiple_newest_first(repo):
    """Mehrfache Notizen auf warmem Lead: neueste steht oben, Reihenfolge konsistent."""
    leadtool.add_lead(repo, "Müller Sanitär", today=date(2026, 6, 18))
    leadtool.set_status(repo, "mueller-sanitaer", "in_klaerung", today=date(2026, 6, 25))
    leadtool.add_note(repo, "mueller-sanitaer", "erste Notiz", today=date(2026, 6, 26))
    leadtool.add_note(repo, "mueller-sanitaer", "zweite Notiz", today=date(2026, 6, 27))
    _, body = leadtool.read_lead(repo, "mueller-sanitaer")
    notizen = body.split("## Notizen", 1)[1]
    assert notizen.index("zweite Notiz") < notizen.index("erste Notiz")
    assert "erste Notiz" in notizen and "zweite Notiz" in notizen
