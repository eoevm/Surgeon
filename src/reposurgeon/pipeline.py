"""Main pipeline — orchestrates clone → analyze → plan → execute → PR."""

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .repo import clone_repo, create_branch, commit_changes, push_branch, cleanup_repo
from .analyzer.python import PythonAnalyzer
from .analyzer.typescript import TypeScriptAnalyzer
from .analyzer.base import AnalysisResult
from .planner import create_refactor_plan, RefactorPlan
from .executor import execute_plan
from .pr import create_pr, PRMetadata
from .utils import temp_workdir

console = Console()


def run_pipeline(
    repo_url: str,
    description: str,
    branch: str = "reposurgeon/refactor",
    dry_run: bool = False,
    model: str = "gpt-4o",
    github_token: Optional[str] = None,
) -> Optional[str]:
    """Run the complete refactoring pipeline.

    Returns:
        PR URL if successful, None otherwise
    """
    repo_path = None
    with temp_workdir() as workdir:
        try:
            # Phase 1: Clone
            console.print(Panel.fit("[bold]Phase 1: Clone Repository[/]"))
            repo_path = clone_repo(repo_url, workdir)
            create_branch(repo_path, branch)

            # Phase 2: Analyze
            console.print(Panel.fit("[bold]Phase 2: Analyze Codebase[/]"))
            py_analyzer = PythonAnalyzer()
            ts_analyzer = TypeScriptAnalyzer()

            py_result = py_analyzer.analyze_directory(repo_path)
            ts_result = ts_analyzer.analyze_directory(repo_path)

            # Merge results
            all_entities = py_result.entities + ts_result.entities
            analysis = AnalysisResult(
                entities=all_entities,
                file_count=py_result.file_count + ts_result.file_count,
                total_lines=py_result.total_lines + ts_result.total_lines,
                languages=(py_result.languages + ts_result.languages),
            )

            # Display analysis summary
            table = Table(title="Codebase Analysis")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            table.add_row("Files", str(analysis.file_count))
            table.add_row("Lines", str(analysis.total_lines))
            table.add_row("Entities", str(len(analysis.entities)))
            table.add_row("Languages", ", ".join(set(analysis.languages)))
            console.print(table)

            # Phase 3: Plan
            console.print(Panel.fit("[bold]Phase 3: Generate Refactor Plan[/]"))
            plan = create_refactor_plan(description, analysis, repo_path, model)

            console.print(f"[bold]Plan:[/] {plan.summary}")
            console.print(f"[bold]Risk:[/] {plan.estimated_risk}")
            console.print(f"[bold]Steps:[/] {len(plan.steps)}")

            for step in plan.steps[:10]:
                console.print(
                    f"  [cyan]{step.step}.[/] {step.action}: {step.description} "
                    f"([dim]{step.file}[/])"
                )
            if len(plan.steps) > 10:
                console.print(f"  [dim]... and {len(plan.steps) - 10} more[/]")

            if dry_run:
                console.print("[yellow]Dry run complete — no changes made.[/]")
                return None

            # Phase 4: Execute
            console.print(Panel.fit("[bold]Phase 4: Execute Refactor[/]"))
            results = execute_plan(plan, repo_path)

            succeeded = sum(1 for r in results if r.success)
            if succeeded == 0:
                console.print("[red]No steps executed successfully. Aborting.[/]")
                return None

            # Phase 5: Commit & PR
            console.print(Panel.fit("[bold]Phase 5: Commit and Create PR[/]"))
            commit_msg = f"refactor: {plan.summary}\n\nRepoSurgeon autonomous refactor\nDetails: {description}"
            commit_changes(repo_path, commit_msg)

            meta = PRMetadata(
                title=f"refactor: {plan.summary}",
                summary=f"## Description\n{description}\n\n{plan.summary}",
                affected_files=plan.affected_files,
                estimated_risk=plan.estimated_risk,
                steps_count=len(plan.steps),
                steps_completed=succeeded,
            )

            pr_url = None
            if not dry_run and results:
                try:
                    push_branch(repo_path, branch)
                    pr_url = create_pr(repo_path, meta, branch, token=github_token)
                except Exception as e:
                    console.print(f"[yellow]PR creation skipped: {e}[/]")
                    console.print(
                        "[yellow]Branch pushed. Create PR manually.[/]"
                    )

            console.print(Panel.fit(
                f"[green bold]✓ Refactor complete![/]\n"
                + (f"PR: {pr_url}" if pr_url else "Changes committed locally.")
            ))
            return pr_url

        finally:
            if repo_path is not None:
                cleanup_repo(repo_path)
