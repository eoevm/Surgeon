"""AST analyzer — base interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class CodeEntity:
    """A code entity discovered by the analyzer."""

    name: str
    kind: str  # "class", "function", "method", "import", "variable"
    file_path: Path
    start_line: int
    end_line: int
    parent: Optional[str] = None  # Parent class/module name
    metadata: dict = field(default_factory=dict)


@dataclass
class AnalysisResult:
    """Result of analyzing a codebase."""

    entities: List[CodeEntity]
    file_count: int
    total_lines: int
    languages: List[str]


class BaseAnalyzer(ABC):
    """Abstract base for language-specific AST analyzers."""

    @abstractmethod
    def analyze_file(self, file_path: Path) -> List[CodeEntity]:
        """Parse a single file and return discovered entities."""
        ...

    @abstractmethod
    def find_usages(self, entity_name: str, files: List[Path]) -> List[CodeEntity]:
        """Find all usages of an entity across files."""
        ...
