"""
Pytest configuration and session-wide fixtures.
Ensures git author and committer identities are configured, and provides environment isolation for CI.
"""
import os
import pytest


@pytest.fixture(autouse=True, scope="session")
def configure_git_environment():
    """Sets standard git author and committer environment variables."""
    os.environ["GIT_AUTHOR_NAME"] = "CI Test Runner"
    os.environ["GIT_AUTHOR_EMAIL"] = "ci@test.local"
    os.environ["GIT_COMMITTER_NAME"] = "CI Test Runner"
    os.environ["GIT_COMMITTER_EMAIL"] = "ci@test.local"


@pytest.fixture(autouse=True)
def clean_ci_environment(monkeypatch):
    """
    Isolates tests from CI runtime environment variables.
    Removes any variable starting with CI_ or GITLAB_, and ACCOUNTABILITY_BASELINE_SHA.
    Tests that specifically test these environment variables must set them explicitly.
    """
    for key in list(os.environ.keys()):
        if key.startswith("CI_") or key.startswith("GITLAB_") or key == "ACCOUNTABILITY_BASELINE_SHA":
            monkeypatch.delenv(key, raising=False)
