import deploy


def test_deploy_writes_html_and_builds_url(tmp_path):
    calls = []
    url = deploy.deploy(
        "schnittwerk", "<html><body>Demo</body></html>",
        repo_path=tmp_path,
        pages_base="https://shawn-jed.github.io/prototyp",
        pusher=lambda repo, slug: calls.append((repo, slug)),
    )
    written = (tmp_path / "schnittwerk" / "index.html").read_text(encoding="utf-8")
    assert written == "<html><body>Demo</body></html>"
    assert url == "https://shawn-jed.github.io/prototyp/schnittwerk"
    assert calls == [(tmp_path, "schnittwerk")]


def test_deploy_strips_trailing_slash_from_base(tmp_path):
    url = deploy.deploy(
        "x", "<html></html>",
        repo_path=tmp_path,
        pages_base="https://shawn-jed.github.io/prototyp/",
        pusher=lambda repo, slug: None,
    )
    assert url == "https://shawn-jed.github.io/prototyp/x"
