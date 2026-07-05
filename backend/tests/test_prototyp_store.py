import pytest

import prototyp


def test_save_request_creates_pending(tmp_path):
    data = prototyp.save_request(tmp_path, "lead-x")
    assert data["status"] == "pending"
    assert data["url"] is None
    assert prototyp.load(tmp_path, "lead-x")["status"] == "pending"


def test_mark_ready_sets_url(tmp_path):
    prototyp.save_request(tmp_path, "lead-x")
    data = prototyp.mark_ready(tmp_path, "lead-x", "https://x.github.io/prototyp/lead-x")
    assert data["status"] == "ready"
    assert data["url"] == "https://x.github.io/prototyp/lead-x"


def test_mark_ready_without_request_raises(tmp_path):
    with pytest.raises(ValueError):
        prototyp.mark_ready(tmp_path, "ghost", "https://x")


def test_list_pending_only_pending(tmp_path):
    prototyp.save_request(tmp_path, "a")
    prototyp.save_request(tmp_path, "b")
    prototyp.mark_ready(tmp_path, "b", "https://x/b")
    pending = prototyp.list_pending(tmp_path)
    assert [p["slug"] for p in pending] == ["a"]


def test_load_missing_returns_none(tmp_path):
    assert prototyp.load(tmp_path, "nope") is None
