import leadtool
from datetime import date


def test_graduate_creates_file_and_removes_row(repo):
    leadtool.add_lead(repo, "Müller Sanitär", schwaeche="keine Mobil-Ansicht; kein Formular",
                      today=date(2026, 6, 18))
    leadtool.graduate(repo, "mueller-sanitaer", status="in_klaerung", today=date(2026, 6, 25))

    # Zeile aus pipeline entfernt
    assert leadtool.read_pipeline(repo) == []
    # Datei existiert mit korrektem Frontmatter
    path = leadtool.lead_path(repo, "mueller-sanitaer")
    assert path.exists()
    meta, body = leadtool.parse_frontmatter(path.read_text(encoding="utf-8"))
    assert meta["status"] == "in_klaerung"
    assert meta["firma"] == "Müller Sanitär"
    assert meta["schwaeche"] == ["keine Mobil-Ansicht", "kein Formular"]
    assert meta["angelegt"] == "2026-06-25"
    assert "## Absprachen" in body


def test_graduate_unknown_slug_raises(repo):
    try:
        leadtool.graduate(repo, "gibtsnicht", status="in_klaerung", today=date(2026, 6, 25))
        assert False
    except ValueError:
        pass
