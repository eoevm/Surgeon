"""Tests for PR creation module."""

import os
from reposurgeon.pr import build_pr_body, PRMetadata


def test_build_pr_body():
    """Builds a PR description from metadata."""
    meta = PRMetadata(
        title="refactor: Rename UserService to AccountService",
        summary="Renamed UserService class to AccountService across the codebase.",
        affected_files=["src/models.py", "src/services.py", "tests/test_models.py"],
        estimated_risk="low",
        steps_count=3,
        steps_completed=3,
    )

    body = build_pr_body(meta)
    assert "Renamed UserService" in body
    assert "src/models.py" in body
    assert "AccountService" in body
    assert "Low" in body  # Risk is capitalized
    assert "3 / 3" in body


def test_pr_metadata_model():
    """PRMetadata model works."""
    meta = PRMetadata(
        title="refactor: Migrate to async",
        summary="Full async migration",
        affected_files=["a.py", "b.py"],
        estimated_risk="high",
        steps_count=10,
        steps_completed=8,
    )

    assert meta.title.startswith("refactor:")
    assert meta.estimated_risk == "high"
    assert meta.steps_completed < meta.steps_count
