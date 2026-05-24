"""Refactor executor — applies planned changes to files."""

from dataclasses import dataclass
from pathlib import Path
from typing import List

from rich.console import Console

from .planner import PlanStep, RefactorPlan

console = Console()


@dataclass
class ExecutionResult:
    """Result of executing a single refactor step."""

    step: int
    success: bool
    file: str
    error: str = ""


def execute_step(step: PlanStep, repo_path: Path) -> ExecutionResult:
    """Execute a single refactor step on a file.

    Performs exact string replacement: old_code → new_code.
    Only replaces the FIRST occurrence to avoid duplicate matches.
    """
    file_path = repo_path / step.file

    if not file_path.exists():
        return ExecutionResult(
            step=step.step,
            success=False,
            file=step.file,
            error=f"File not found: {step.file}",
        )

    original = file_path.read_text()

    if step.old_code not in original:
        return ExecutionResult(
            step=step.step,
            success=False,
            file=step.file,
            error=f"Target code not found in {step.file}: {step.old_code[:80]}...",
        )

    # Replace only the first occurrence
    modified = original.replace(step.old_code, step.new_code, 1)
    file_path.write_text(modified)

    console.print(
        f"[green]✓[/] Step {step.step}: {step.description} "
        f"([dim]{step.file}[/])"
    )

    return ExecutionResult(step=step.step, success=True, file=step.file)


def execute_plan(plan: RefactorPlan, repo_path: Path) -> List[ExecutionResult]:
    """Execute all steps in a refactor plan sequentially.

    Stops on first failure.
    """
    results = []

    for step in plan.steps:
        result = execute_step(step, repo_path)
        results.append(result)
        if not result.success:
            console.print(f"[red]✗[/] Failed at step {step.step}: {result.error}")
            break

    success_count = sum(1 for r in results if r.success)
    console.print(
        f"\n[bold]Executed {success_count}/{len(plan.steps)} steps[/]"
    )

    return results
