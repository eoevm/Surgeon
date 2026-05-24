"""Repository management — clone, branch, cleanup."""

import shutil
import subprocess
from pathlib import Path
from typing import Optional

from rich.console import Console

console = Console()


def clone_repo(url: str, workdir: Path, name: Optional[str] = None) -> Path:
    """Clone a git repository to workdir.

    Args:
        url: Git repository URL (https or ssh)
        workdir: Parent directory for the clone
        name: Optional directory name (derived from URL if not given)

    Returns:
        Path to the cloned repository

    Raises:
        RuntimeError: If clone fails
    """
    if name is None:
        name = url.rstrip("/").split("/")[-1].replace(".git", "")

    target = workdir / name
    if target.exists():
        shutil.rmtree(target)

    console.print(f"[dim]Cloning {url} → {target}[/]")

    result = subprocess.run(
        ["git", "clone", "--depth", "1", url, str(target)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Clone failed: {result.stderr}")

    return target


def create_branch(repo_path: Path, branch_name: str) -> None:
    """Create and switch to a new branch.

    Args:
        repo_path: Path to the git repository
        branch_name: Name for the new branch

    Raises:
        RuntimeError: If branch creation fails
    """
    console.print(f"[dim]Creating branch: {branch_name}[/]")

    result = subprocess.run(
        ["git", "checkout", "-b", branch_name],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Branch creation failed: {result.stderr}")


def commit_changes(repo_path: Path, message: str) -> None:
    """Stage all changes and commit.

    Args:
        repo_path: Path to the git repository
        message: Commit message

    Raises:
        RuntimeError: If commit fails
    """
    subprocess.run(
        ["git", "add", "-A"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )

    result = subprocess.run(
        ["git", "commit", "-m", message],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Commit failed: {result.stderr}")

    console.print(f"[green]Committed: {message}[/]")


def push_branch(repo_path: Path, branch_name: str) -> None:
    """Push the branch to origin.

    Args:
        repo_path: Path to the git repository
        branch_name: Branch to push

    Raises:
        RuntimeError: If push fails
    """
    console.print(f"[dim]Pushing branch: {branch_name}[/]")

    result = subprocess.run(
        ["git", "push", "-u", "origin", branch_name],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Push failed: {result.stderr}")


def cleanup_repo(repo_path: Path) -> None:
    """Remove a cloned repository.

    Args:
        repo_path: Path to the repository directory
    """
    if repo_path.exists():
        shutil.rmtree(repo_path)
        console.print(f"[dim]Cleaned up: {repo_path}[/]")
