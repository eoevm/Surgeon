"""RepoSurgeon CLI — Autonomous codebase refactoring agent."""

import click
from rich.console import Console

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="reposurgeon")
def main():
    """RepoSurgeon — Autonomous codebase refactoring.

    Describe a refactor in natural language, point at a repo,
    and RepoSurgeon plans, executes, and submits a PR.
    """
    pass


@main.command()
@click.argument("repo_url")
@click.option(
    "-d", "--description",
    required=True,
    help="Natural language description of the refactor to perform",
)
@click.option(
    "-b", "--branch",
    default="reposurgeon/refactor",
    help="Branch name for the refactor (default: reposurgeon/refactor)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Plan the refactor but don't execute or create PR",
)
@click.option(
    "--model",
    default="gpt-4o",
    help="LLM model to use for planning (default: gpt-4o)",
)
def refactor(repo_url, description, branch, dry_run, model):
    """Clone REPO_URL, plan a refactor from DESCRIPTION, and submit a PR.

    Example:
        reposurgeon refactor https://github.com/user/repo \\
            -d "Migrate all class-based views to function-based views"
    """
    console.print(f"[bold blue]RepoSurgeon[/] v0.1.0")
    console.print(f"Repo: {repo_url}")
    console.print(f"Task: {description}")

    if dry_run:
        console.print("[yellow]Dry run mode — will plan but not execute.[/]")

    # Pipeline will be wired in later tasks
    console.print("[dim]Pipeline integration coming soon...[/dim]")


@main.command()
@click.argument("repo_url")
def analyze(repo_url):
    """Analyze a repo's codebase structure without refactoring."""
    console.print(f"[bold]Analyzing {repo_url}...[/bold]")
    console.print("[dim]Analysis engine coming soon...[/dim]")


if __name__ == "__main__":
    main()
