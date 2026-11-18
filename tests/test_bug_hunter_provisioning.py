import pytest

from app.bug_hunter_provisioning import validate_github_url, workspace_for_agent


@pytest.mark.parametrize("url,owner,repo", [
    ("https://github.com/octocat/Hello-World", "octocat", "Hello-World"),
    ("https://github.com/octocat/Hello-World.git", "octocat", "Hello-World"),
])
def test_validate_github_url_accepts_canonical_repo_urls(url, owner, repo):
    identity = validate_github_url(url)
    assert identity.owner == owner
    assert identity.name == repo
    assert identity.url == f"https://github.com/{owner}/{repo}.git"


@pytest.mark.parametrize("url", [
    "http://github.com/owner/repo",
    "https://evil.example/owner/repo",
    "https://user:pass@github.com/owner/repo",
    "https://github.com/owner/repo/tree/main",
    "https://github.com/owner/repo?query=1",
    "https://github.com/owner/repo#fragment",
    "https://github.com/owner",
    "https://github.com/owner/repo/extra",
    "https://github.com:444/owner/repo",
    "",
])
def test_validate_github_url_rejects_non_repo_urls(url):
    with pytest.raises(ValueError):
        validate_github_url(url)


@pytest.mark.parametrize("agent_id", ["../escape", "a/b", ".", "", "x" * 81])
def test_workspace_rejects_path_traversal_and_invalid_ids(agent_id):
    with pytest.raises(ValueError):
        workspace_for_agent(agent_id)


def test_workspace_is_agent_scoped():
    assert workspace_for_agent("hunter_1") != workspace_for_agent("hunter_2")
