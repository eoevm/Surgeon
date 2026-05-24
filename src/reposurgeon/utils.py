"""Shared utilities for RepoSurgeon."""

import tempfile
from pathlib import Path
from contextlib import contextmanager
from typing import Generator


@contextmanager
def temp_workdir() -> Generator[Path, None, None]:
    """Create a temporary working directory that cleans up on exit."""
    with tempfile.TemporaryDirectory(prefix="reposurgeon_") as tmp:
        yield Path(tmp)


def detect_language(file_path: Path) -> str:
    """Detect programming language from file extension."""
    ext_map = {
        ".py": "python",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".go": "go",
    }
    return ext_map.get(file_path.suffix, "unknown")
