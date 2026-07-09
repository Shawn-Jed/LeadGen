import leadtool


def test_render_then_parse_roundtrip():
    rows = [
        {"slug": "mueller-sanitaer", "firma": "Müller Sanitär", "adresse": "Hauptstr. 1, Hamburg",
         "website": "mueller-sanitaer.de", "status": "kontaktiert", "schwaeche": "keine Mobil-Ansicht",
         "kontaktiert_am": "2026-06-20", "wiedervorlage": "2026-07-05", "notiz": ""},
    ]
    text = leadtool.render_pipeline_table(rows)
    assert leadtool.parse_pipeline_table(text) == rows


def test_parse_empty_table_returns_no_rows():
    text = leadtool.render_pipeline_table([])
    assert leadtool.parse_pipeline_table(text) == []


def test_parse_migrates_v2_schema_without_website():
    # Alt-Schema v2 (8 Spalten: mit Adresse, ohne Website) → Website leer nachgezogen.
    text = (
        "| slug | Firma | Adresse | Status | Schwäche | kontaktiert_am | Wiedervorlage | Notiz |\n"
        "|---|---|---|---|---|---|---|---|\n"
        "| a-b | A B | Weg 1 | identifiziert | keine Website | — | — | — |\n"
    )
    rows = leadtool.parse_pipeline_table(text)
    assert len(rows) == 1
    assert rows[0]["adresse"] == "Weg 1"
    assert rows[0]["website"] == ""
    assert rows[0]["status"] == "identifiziert"


def test_parse_migrates_v1_schema_without_adresse_and_website():
    # Alt-Schema v1 (7 Spalten: weder Adresse noch Website) → beide leer nachgezogen.
    text = (
        "| slug | Firma | Status | Schwäche | kontaktiert_am | Wiedervorlage | Notiz |\n"
        "|---|---|---|---|---|---|---|\n"
        "| a-b | A B | kontaktiert | keine Website | 2026-06-20 | — | — |\n"
    )
    rows = leadtool.parse_pipeline_table(text)
    assert len(rows) == 1
    assert rows[0]["adresse"] == ""
    assert rows[0]["website"] == ""
    assert rows[0]["status"] == "kontaktiert"
    assert rows[0]["kontaktiert_am"] == "2026-06-20"


def test_render_sanitizes_pipe_and_blank_cells():
    rows = [{"slug": "x", "firma": "A|B", "status": "identifiziert",
             "schwaeche": "", "kontaktiert_am": "", "wiedervorlage": "", "notiz": ""}]
    text = leadtool.render_pipeline_table(rows)
    assert "A/B" in text          # Pipe ersetzt
    assert "| — |" in text         # leere Zelle als —
    parsed = leadtool.parse_pipeline_table(text)
    assert parsed[0]["schwaeche"] == ""   # — wird beim Parsen wieder zu ""
