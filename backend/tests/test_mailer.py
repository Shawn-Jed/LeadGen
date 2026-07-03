import mailer


def test_build_message_plain():
    msg = mailer.build_message(from_addr="me@x.de", to_addr="lead@y.de",
                               subject="Betreff", body="Hallo\nLink: https://p")
    assert msg["From"] == "me@x.de"
    assert msg["To"] == "lead@y.de"
    assert msg["Subject"] == "Betreff"
    assert "Link: https://p" in msg.get_content()


def test_build_message_with_attachment():
    att = {"filename": "proto.pdf", "data": b"%PDF-1.4", "maintype": "application", "subtype": "pdf"}
    msg = mailer.build_message(from_addr="a@x.de", to_addr="b@y.de",
                               subject="S", body="B", attachment=att)
    names = [p.get_filename() for p in msg.iter_attachments()]
    assert "proto.pdf" in names


def test_deliver_draft_writes_eml(tmp_path):
    msg = mailer.build_message(from_addr="a@x.de", to_addr="b@y.de", subject="S", body="B")
    eml = tmp_path / "outreach" / "lead.eml"
    res = mailer.deliver(msg, mode="draft", cfg={}, eml_path=eml)
    assert res["mode"] == "draft"
    assert eml.exists() and b"Subject: S" in eml.read_bytes()


def test_deliver_direct_calls_smtp(tmp_path):
    sent = {}

    class FakeSMTP:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def starttls(self): sent["tls"] = True
        def login(self, u, p): sent["login"] = (u, p)
        def send_message(self, m): sent["msg"] = m

    msg = mailer.build_message(from_addr="a@x.de", to_addr="b@y.de", subject="S", body="B")
    cfg = {"host": "h", "port": 587, "user": "u", "password": "pw", "from_addr": "a@x.de"}
    res = mailer.deliver(msg, mode="direct", cfg=cfg, eml_path=tmp_path / "x.eml",
                         smtp_factory=lambda: FakeSMTP())
    assert res["mode"] == "direct"
    assert sent["login"] == ("u", "pw")
    assert sent["msg"] is msg
