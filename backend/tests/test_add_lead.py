import leadtool
from datetime import date


def test_slugify_normalizes_umlauts_and_spaces():
    assert leadtool.slugify("Müller Sanitär GmbH") == "mueller-sanitaer-gmbh"
    assert leadtool.slugify("Café & Co.") == "cafe-co"


def test_add_lead_appends_row(repo):
    slug = leadtool.add_lead(repo, "Müller Sanitär GmbH", schwaeche="keine Mobil-Ansicht",
                             today=date(2026, 6, 18))
    assert slug == "mueller-sanitaer-gmbh"
    rows = leadtool.read_pipeline(repo)
    assert len(rows) == 1
    assert rows[0]["firma"] == "Müller Sanitär GmbH"
    assert rows[0]["status"] == "identifiziert"
    assert rows[0]["schwaeche"] == "keine Mobil-Ansicht"


def test_add_lead_duplicate_slug_raises(repo):
    leadtool.add_lead(repo, "Müller Sanitär", today=date(2026, 6, 18))
    try:
        leadtool.add_lead(repo, "Müller Sanitär", today=date(2026, 6, 18))
        assert False, "erwartete ValueError"
    except ValueError:
        pass
