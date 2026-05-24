"""Python AST analyzer using tree-sitter."""

import re
from pathlib import Path
from typing import List

import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Query, QueryCursor

from .base import BaseAnalyzer, CodeEntity, AnalysisResult

PY_LANGUAGE = Language(tspython.language())
QUERY_CLASS = Query(
    PY_LANGUAGE,
    """(class_definition name: (identifier) @class_name) @class""",
)
QUERY_FUNCTION = Query(
    PY_LANGUAGE,
    """(function_definition name: (identifier) @func_name) @func""",
)
QUERY_IMPORT = Query(
    PY_LANGUAGE,
    """(import_statement) @import""",
)
QUERY_FROM_IMPORT = Query(
    PY_LANGUAGE,
    """(import_from_statement) @import""",
)
# Plain identifier decorator: @lru_cache
QUERY_DECORATOR_ID = Query(
    PY_LANGUAGE,
    """(decorated_definition
        (decorator (identifier) @dec_name)
        (function_definition name: (identifier) @func_name)) @decorated""",
)
# Call decorator: @app.route("/api")
QUERY_DECORATOR_CALL = Query(
    PY_LANGUAGE,
    """(decorated_definition
        (decorator (call function: (identifier) @dec_name))
        (function_definition name: (identifier) @func_name)) @decorated""",
)


class PythonAnalyzer(BaseAnalyzer):
    """Analyzes Python source code using tree-sitter."""

    def __init__(self):
        self.parser = Parser(PY_LANGUAGE)

    def analyze_file(self, file_path: Path) -> List[CodeEntity]:
        """Parse a Python file and extract code entities."""
        source = file_path.read_bytes()
        tree = self.parser.parse(source)
        root = tree.root_node
        entities = []

        # Track which names come from decorated definitions
        decorated_names = set()

        # Find classes
        for _idx, captures in QueryCursor(QUERY_CLASS).matches(root):
            entity_node = captures["class"][0]
            name_node = captures["class_name"][0]
            entities.append(CodeEntity(
                name=name_node.text.decode(),
                kind="class",
                file_path=file_path,
                start_line=entity_node.start_point[0] + 1,
                end_line=entity_node.end_point[0] + 1,
            ))

        # Find functions
        for _idx, captures in QueryCursor(QUERY_FUNCTION).matches(root):
            entity_node = captures["func"][0]
            name_node = captures["func_name"][0]
            entities.append(CodeEntity(
                name=name_node.text.decode(),
                kind="function",
                file_path=file_path,
                start_line=entity_node.start_point[0] + 1,
                end_line=entity_node.end_point[0] + 1,
            ))

        # Find decorated functions (plain identifier decorator)
        for _idx, captures in QueryCursor(QUERY_DECORATOR_ID).matches(root):
            decorated_node = captures["decorated"][0]
            dec_name = captures["dec_name"][0].text.decode()
            func_name = captures["func_name"][0].text.decode()
            decorated_names.add(func_name)
            entities.append(CodeEntity(
                name=func_name,
                kind="function",
                file_path=file_path,
                start_line=decorated_node.start_point[0] + 1,
                end_line=decorated_node.end_point[0] + 1,
                metadata={"decorator": dec_name},
            ))

        # Find decorated functions (call decorator)
        for _idx, captures in QueryCursor(QUERY_DECORATOR_CALL).matches(root):
            decorated_node = captures["decorated"][0]
            dec_name = captures["dec_name"][0].text.decode()
            func_name = captures["func_name"][0].text.decode()
            decorated_names.add(func_name)
            entities.append(CodeEntity(
                name=func_name,
                kind="function",
                file_path=file_path,
                start_line=decorated_node.start_point[0] + 1,
                end_line=decorated_node.end_point[0] + 1,
                metadata={"decorator": dec_name},
            ))

        # Remove duplicate plain function entries for decorated functions
        entities = [
            e for e in entities
            if not (e.kind == "function" and e.name in decorated_names and not e.metadata)
        ]

        return entities

    def analyze_directory(self, directory: Path) -> AnalysisResult:
        """Analyze all Python files in a directory."""
        entities = []
        py_files = list(directory.rglob("*.py"))
        total_lines = 0

        # Skip hidden dirs and venvs
        py_files = [
            f for f in py_files
            if not any(p.startswith(".") or p.startswith("venv")
                       for p in f.relative_to(directory).parts)
        ]

        for file_path in py_files:
            try:
                file_entities = self.analyze_file(file_path)
                entities.extend(file_entities)
                total_lines += len(file_path.read_text().splitlines())
            except Exception:
                continue

        return AnalysisResult(
            entities=entities,
            file_count=len(py_files),
            total_lines=total_lines,
            languages=["python"],
        )

    def find_usages(self, entity_name: str, files: List[Path]) -> List[CodeEntity]:
        """Find usages of an entity name across files using regex."""
        usages = []
        pattern = re.compile(rf"\b{re.escape(entity_name)}\b")

        for file_path in files:
            try:
                lines = file_path.read_text().splitlines()
                for i, line in enumerate(lines, 1):
                    if pattern.search(line):
                        usages.append(CodeEntity(
                            name=entity_name,
                            kind="usage",
                            file_path=file_path,
                            start_line=i,
                            end_line=i,
                        ))
            except Exception:
                continue

        return usages
