"""Tests for the refactor planner."""

import os
from pathlib import Path
from reposurgeon.analyzer.base import CodeEntity, AnalysisResult
from reposurgeon.planner import PlanStep, RefactorPlan, create_refactor_plan


def test_plan_step_model():
    """PlanStep model works."""
    step = PlanStep(
        step=1,
        action="rename",
        target="UserService",
        file="src/services/user.py",
        description="Rename UserService to AccountService",
        old_code="class UserService:",
        new_code="class AccountService:",
    )

    assert step.step == 1
    assert step.action == "rename"
    assert step.file == "src/services/user.py"
    assert "UserService" in step.old_code
    assert "AccountService" in step.new_code


def test_refactor_plan_model():
    """RefactorPlan model works."""
    steps = [
        PlanStep(
            step=1, action="rename", target="UserService",
            file="src/a.py", description="Rename class",
            old_code="class UserService:", new_code="class AccountService:",
        ),
    ]
    plan = RefactorPlan(
        summary="Rename UserService to AccountService",
        steps=steps,
        affected_files=["src/a.py", "src/b.py"],
        estimated_risk="low",
    )

    assert len(plan.steps) == 1
    assert plan.summary == "Rename UserService to AccountService"
    assert plan.estimated_risk == "low"
    assert len(plan.affected_files) == 2


def test_create_refactor_plan_no_api_key():
    """create_refactor_plan returns a plan even without API key."""
    entities = [
        CodeEntity(name="UserService", kind="class",
                   file_path=Path("src/services.py"),
                   start_line=1, end_line=10),
    ]
    analysis = AnalysisResult(
        entities=entities, file_count=1, total_lines=100, languages=["python"],
    )

    # Ensure no API key is set
    old_key = os.environ.pop("OPENAI_API_KEY", None)
    try:
        plan = create_refactor_plan(
            description="Rename UserService to AccountService",
            analysis=analysis,
            repo_path=Path("/tmp/test-repo"),
        )
        assert isinstance(plan, RefactorPlan)
        assert plan.summary != ""
    finally:
        if old_key:
            os.environ["OPENAI_API_KEY"] = old_key


def test_create_refactor_plan_basic():
    """create_refactor_plan produces a valid plan (no LLM call — mock mode)."""
    entities = [
        CodeEntity(name="UserService", kind="class",
                   file_path=Path("src/services.py"),
                   start_line=1, end_line=10),
        CodeEntity(name="get_user", kind="function",
                   file_path=Path("src/services.py"),
                   start_line=3, end_line=7),
    ]
    analysis = AnalysisResult(
        entities=entities,
        file_count=1,
        total_lines=100,
        languages=["python"],
    )

    # Ensure no API key is set so it falls back
    old_key = os.environ.pop("OPENAI_API_KEY", None)
    try:
        plan = create_refactor_plan(
            description="Rename UserService to AccountService",
            analysis=analysis,
            repo_path=Path("/tmp/test-repo"),
            model="gpt-4o-mini",
        )

        assert isinstance(plan, RefactorPlan)
        assert plan.summary != ""
        assert plan.estimated_risk == "unknown"  # Fallback mode
    finally:
        if old_key:
            os.environ["OPENAI_API_KEY"] = old_key
