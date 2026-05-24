"""TypeScript/JavaScript AST analyzer using tree-sitter."""

import re
from pathlib import Path
from typing import List

import tree_sitter_typescript as tstypescript
from tree_sitter import Language, Parser, Query, QueryCursor

from .base import BaseAnalyzer, CodeEntity, AnalysisResult

TS_LANGUAGE = Language(tstypescript.language_typescript())
QUERY_CLASS = Query(
    TS_LANGUAGE,
    """(class_declaration name: (type_identifier) @class_name) @class""",
)
QUERY_EXPORT_CLASS = Query(
    TS_LANGUAGE,
    """(export_statement
        (class_declaration name: (type_identifier) @class_name)) @class""",
)
QUERY_FUNCTION = Query(
    TS_LANGUAGE,
    """(function_declaration name: (identifier) @func_name) @func""",
)
QUERY_EXPORT_FUNCTION = Query(
    TS_LANGUAGE,
    """(export_statement
        (function_declaration name: (identifier) @func_name)) @func""",
)
QUERY_ARROW = Query(
    TS_LANGUAGE,
    """(variable_declarator
        name: (identifier) @func_name
        value: (arrow_function)) @func""",
)
QUERY_METHOD = Query(
    TS_LANGUAGE,
    """(method_definition name: (property_identifier) @method_name) @method""",
)

TS_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}


class TypeScriptAnalyzer(BaseAnalyzer):
    """Analyzes TypeScript/JavaScript source code using tree-sitter."""

    def __init__(self):
        self.parser = Parser(TS_LANGUAGE)

    def analyze_file(self, file_path: Path) -> List[CodeEntity]:
        """Parse a TypeScript/JavaScript file and extract entities."""
        source = file_path.read_bytes()
        tree = self.parser.parse(source)
        root = tree.root_node
        entities = []
        seen = set()  # Deduplicate (name, kind, start_line) tuples

        def _add(query, kind, name_key, entity_key):
            for _idx, captures in QueryCursor(query).matches(root):
                entity_node = captures[entity_key][0]
                name_node = captures[name_key][0]
                name = name_node.text.decode()
                start = entity_node.start_point[0] + 1
                end = entity_node.end_point[0] + 1
                dedup_key = (name, kind, start)
                if dedup_key not in seen:
                    seen.add(dedup_key)
                    entities.append(CodeEntity(
                        name=name,
                        kind=kind,
                        file_path=file_path,
                        start_line=start,
                        end_line=end,
                    ))

        _add(QUERY_CLASS, "class", "class_name", "class")
        _add(QUERY_EXPORT_CLASS, "class", "class_name", "class")
        _add(QUERY_FUNCTION, "function", "func_name", "func")
        _add(QUERY_EXPORT_FUNCTION, "function", "func_name", "func")
        _add(QUERY_ARROW, "function", "func_name", "func")
        _add(QUERY_METHOD, "method", "method_name", "method")

        return entities

    def analyze_directory(self, directory: Path) -> AnalysisResult:
        """Analyze all TS/JS files in a directory."""
        entities = []
        ts_files = []
        total_lines = 0

        for ext in TS_EXTENSIONS:
            for f in directory.rglob(f"*{ext}"):
                parts = f.relative_to(directory).parts
                if not any(p.startswith(".") or "node_modules" in p for p in parts):
                    ts_files.append(f)

        for file_path in ts_files:
            try:
                file_entities = self.analyze_file(file_path)
                entities.extend(file_entities)
                total_lines += len(file_path.read_text().splitlines())
            except Exception:
                continue

        return AnalysisResult(
            entities=entities,
            file_count=len(ts_files),
            total_lines=total_lines,
            languages=["typescript", "javascript"],
        )

    def find_usages(self, entity_name: str, files: List[Path]) -> List[CodeEntity]:
        """Find usages of an entity name across files."""
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
