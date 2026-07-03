import outreach


def test_save_request_creates_pending(tmp_path):
    data = outreach.save_request(tmp_path, "lead-x", {"angebot": "Website-Relaunch"})
    assert data["status"] == "pending"
    assert data["request"]["angebot"] == "Website-Relaunch"
    assert data["draft"] is None
    assert outreach.load(tmp_path, "lead-x")["status"] == "pending"


def test_set_draft_moves_to_ready(tmp_path):
    outreach.save_request(tmp_path, "lead-x", {"angebot": "X"})
    data = outreach.set_draft(tmp_path, "lead-x", "Betreff", "Text")
    assert data["status"] == "ready"
    assert data["draft"] == {"betreff": "Betreff", "text": "Text"}


def test_mark_sent(tmp_path):
    outreach.save_request(tmp_path, "lead-x", {"angebot": "X"})
    outreach.set_draft(tmp_path, "lead-x", "B", "T")
    assert outreach.mark_sent(tmp_path, "lead-x")["status"] == "sent"


def test_list_pending_only_pending(tmp_path):
    outreach.save_request(tmp_path, "a", {"angebot": "1"})
    outreach.save_request(tmp_path, "b", {"angebot": "2"})
    outreach.set_draft(tmp_path, "b", "B", "T")  # b -> ready
    pending = outreach.list_pending(tmp_path)
    assert [p["slug"] for p in pending] == ["a"]


def test_set_draft_without_request_raises(tmp_path):
    import pytest
    with pytest.raises(ValueError):
        outreach.set_draft(tmp_path, "ghost", "B", "T")
