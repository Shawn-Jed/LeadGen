import leadtool


def test_render_then_parse_roundtrip():
    rows = [
        {"slug": "mueller-sanitaer", "firma": "Müller Sanitär", "adresse": "Hauptstr. 1, Hamburg",
         "status": "kontaktiert", "schwaeche": "keine Mobil-Ansicht", "kontaktiert_am": "2026-06-20",
         "wiedervorlage": "2026-07-05", "notiz": ""},
    ]
    text = leadtool.render_pipeline_table(rows)
    assert leadtool.parse_pipeline_table(text) == rows


def test_parse_empty_table_returns_no_rows():
    text = leadtool.render_pipeline_table([])
    assert leadtool.parse_pipeline_table(text) == []


def test_render_sanitizes_pipe_and_blank_cells():
    rows = [{"slug": "x", "firma": "A|B", "status": "identifiziert",
             "schwaeche": "", "kontaktiert_am": "", "wiedervorlage": "", "notiz": ""}]
    text = leadtool.render_pipeline_table(rows)
    assert "A/B" in text          # Pipe ersetzt
    assert "| — |" in text         # leere Zelle als —
    parsed = leadtool.parse_pipeline_table(text)
    assert parsed[0]["schwaeche"] == ""   # — wird beim Parsen wieder zu ""
