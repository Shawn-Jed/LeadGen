import config


def test_load_env_sets_missing_keys(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text(
        "SMTP_HOST=smtp.example.com\nSMTP_PORT=465\n# Kommentar\nSMTP_USER=me@x.de\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("SMTP_HOST", raising=False)
    config.load_env(tmp_path)
    assert __import__("os").environ["SMTP_HOST"] == "smtp.example.com"


def test_smtp_config_reads_env(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "h")
    monkeypatch.setenv("SMTP_PORT", "2525")
    monkeypatch.setenv("SMTP_USER", "u@x.de")
    monkeypatch.setenv("SMTP_PASS", "secret")
    monkeypatch.delenv("SMTP_FROM", raising=False)
    cfg = config.smtp_config()
    assert cfg["host"] == "h" and cfg["port"] == 2525
    assert cfg["from_addr"] == "u@x.de"  # fällt auf user zurück


def test_send_mode_default_draft(monkeypatch):
    monkeypatch.delenv("OUTREACH_SEND_MODE", raising=False)
    assert config.send_mode() == "draft"


def test_prototyp_config_reads_env(monkeypatch):
    import config
    monkeypatch.setenv("PROTOTYP_REPO_PATH", "/tmp/prototyp")
    monkeypatch.setenv("PROTOTYP_PAGES_BASE", "https://shawn-jed.github.io/prototyp")
    assert config.prototyp_repo_path() == "/tmp/prototyp"
    assert config.prototyp_pages_base() == "https://shawn-jed.github.io/prototyp"


def test_prototyp_config_defaults_empty(monkeypatch):
    import config
    monkeypatch.delenv("PROTOTYP_REPO_PATH", raising=False)
    monkeypatch.delenv("PROTOTYP_PAGES_BASE", raising=False)
    assert config.prototyp_repo_path() == ""
    assert config.prototyp_pages_base() == ""
