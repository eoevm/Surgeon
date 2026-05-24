"""Tests for the refactor executor."""

from pathlib import Path
from reposurgeon.executor import execute_step, execute_plan, ExecutionResult
from reposurgeon.planner import PlanStep, RefactorPlan


def test_execute_step_rename(tmp_path):
    """Execute a single rename step."""
    # Create test file
    test_file = tmp_path / "test.py"
    test_file.write_text("class OldName:\n    pass\n")

    step = PlanStep(
        step=1,
        action="rename",
        target="OldName",
        file=str(test_file),
        description="Rename OldName to NewName",
        old_code="class OldName:",
        new_code="class NewName:",
    )

    result = execute_step(step, tmp_path)
    assert result.success
    assert test_file.read_text() == "class NewName:\n    pass\n"


def test_execute_step_failure_not_found(tmp_path):
    """Execution fails when old_code not found in file."""
    test_file = tmp_path / "test.py"
    test_file.write_text("x = 1\n")

    step = PlanStep(
        step=1,
        action="rename",
        target="nonexistent",
        file=str(test_file),
        description="Change something that doesn't exist",
        old_code="class Nonexistent:",
        new_code="class Something:",
    )

    result = execute_step(step, tmp_path)
    assert not result.success
    assert "not found" in result.error.lower()


def test_execute_plan(tmp_path):
    """Execute a full multi-step plan."""
    # Create multiple files
    (tmp_path / "models.py").write_text("class User:\n    pass\n")
    (tmp_path / "services.py").write_text(
        "from models import User\n\n"
        "def get_user():\n"
        "    return User()\n"
    )

    plan = RefactorPlan(
        summary="Rename User to Account",
        steps=[
            PlanStep(
                step=1, action="rename", target="User",
                file="models.py",
                description="Rename class User to Account",
                old_code="class User:",
                new_code="class Account:",
            ),
            PlanStep(
                step=2, action="rename", target="User",
                file="services.py",
                description="Update import",
                old_code="from models import User",
                new_code="from models import Account",
            ),
            PlanStep(
                step=3, action="rename", target="User",
                file="services.py",
                description="Update usage",
                old_code="return User()",
                new_code="return Account()",
            ),
        ],
        affected_files=["models.py", "services.py"],
        estimated_risk="low",
    )

    results = execute_plan(plan, tmp_path)
    assert len(results) == 3
    assert all(r.success for r in results)
    assert "class Account:" in (tmp_path / "models.py").read_text()
    assert "from models import Account" in (tmp_path / "services.py").read_text()
    assert "return Account()" in (tmp_path / "services.py").read_text()
