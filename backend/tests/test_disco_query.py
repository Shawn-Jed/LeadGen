import discotool


def test_query_hamburg_wide_without_stadtteil():
    q = discotool.build_overpass_query(["amenity=dentist"], None)
    assert "[out:json]" in q
    assert '"name"="Hamburg"' in q
    assert 'node["amenity"="dentist"](area.searchArea);' in q
    assert 'way["amenity"="dentist"](area.searchArea);' in q
    assert "out center tags;" in q


def test_query_with_stadtteil_uses_named_area():
    q = discotool.build_overpass_query(["office=lawyer"], "Eimsbüttel")
    assert '"name"="Eimsbüttel"' in q
    assert 'node["office"="lawyer"](area.searchArea);' in q
