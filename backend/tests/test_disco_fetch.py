import discotool


def test_fetch_overpass_uses_injected_fn():
    captured = {}
    def fake(query):
        captured["q"] = query
        return {"elements": [{"type": "node", "id": 1, "tags": {"name": "X"}}]}
    data = discotool.fetch_overpass("QUERY", fetch_fn=fake)
    assert captured["q"] == "QUERY"
    assert data["elements"][0]["tags"]["name"] == "X"


def test_http_overpass_is_callable_default():
    # Default fetch_fn ist http_overpass (echter Call) — hier nur Existenz/Signatur prüfen, NICHT aufrufen.
    assert callable(discotool.http_overpass)
