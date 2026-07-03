import leadtool


def test_frontmatter_roundtrip():
    meta = {"firma": "Müller Sanitär", "slug": "mueller-sanitaer", "status": "in_klaerung",
            "schwaeche": ["keine mobile Ansicht", "kein Kontaktformular"]}
    body = "## Historie\n- 2026-06-25 Antwort\n\n## Notizen\n"
    text = leadtool.dump_frontmatter(meta, body)
    assert text.startswith("---\n")
    meta2, body2 = leadtool.parse_frontmatter(text)
    assert meta2 == meta
    assert body2 == body


def test_dump_preserves_key_order_and_umlauts():
    text = leadtool.dump_frontmatter({"firma": "Café", "status": "gewonnen"}, "")
    assert text.index("firma") < text.index("status")
    assert "Café" in text  # allow_unicode
