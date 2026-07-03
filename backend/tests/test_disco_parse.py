import discotool

SAMPLE = {"elements": [
    {"type": "node", "id": 1, "tags": {
        "name": "Zahnarzt A", "amenity": "dentist", "website": "https://a.de",
        "addr:street": "Osterstraße", "addr:housenumber": "1",
        "addr:postcode": "20259", "addr:city": "Hamburg"}},
    {"type": "node", "id": 2, "tags": {
        "name": "Zahnarzt B", "amenity": "dentist", "addr:street": "Wegastraße"}},
    {"type": "way", "id": 3, "tags": {"amenity": "dentist"}},  # kein name → skip
    {"type": "node", "id": 4, "tags": {
        "name": "Zahnarzt C", "contact:website": "https://c.de", "contact:phone": "040123"}},
]}


def test_parse_skips_nameless_and_extracts_fields():
    cands = discotool.parse_elements(SAMPLE)
    assert [c["firma"] for c in cands] == ["Zahnarzt A", "Zahnarzt B", "Zahnarzt C"]
    a = cands[0]
    assert a["website"] == "https://a.de"
    assert a["adresse"] == "Osterstraße 1, 20259 Hamburg"
    assert a["osm_id"] == "node/1"


def test_parse_reads_contact_website_fallback():
    cands = discotool.parse_elements(SAMPLE)
    c = cands[2]
    assert c["website"] == "https://c.de"
    assert c["telefon"] == "040123"


def test_parse_empty():
    assert discotool.parse_elements({"elements": []}) == []
