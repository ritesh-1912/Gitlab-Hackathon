"""
Pytest configuration and session-wide fixtures.
Ensures git author and committer identities are always configured for test runs.
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
