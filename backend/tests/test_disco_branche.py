import discotool


def test_known_branche_returns_tags():
    assert discotool.branche_to_tags("Zahnärzte") == ["amenity=dentist"]
    assert discotool.branche_to_tags("friseur") == ["shop=hairdresser"]
    assert discotool.branche_to_tags("Kanzlei") == ["office=lawyer"]


def test_unknown_branche_raises_with_hint():
    try:
        discotool.branche_to_tags("Raumschiffbauer")
        assert False
    except ValueError as e:
        assert "Raumschiffbauer" in str(e)
