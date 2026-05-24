"""Tests for AST analyzer."""

import textwrap
from pathlib import Path

from reposurgeon.analyzer import PythonAnalyzer, CodeEntity


def test_python_analyzer_classes():
    """Detects Python class definitions."""
    code = textwrap.dedent("""
    class UserService:
        def get_user(self, user_id: int):
            pass

    class AdminService(UserService):
        def ban_user(self, user_id: int):
            pass
    """).strip()

    tmp = Path("/tmp/test_analyzer.py")
    tmp.write_text(code)

    analyzer = PythonAnalyzer()
    entities = analyzer.analyze_file(tmp)

    classes = [e for e in entities if e.kind == "class"]
    assert len(classes) == 2
    assert classes[0].name == "UserService"
    assert classes[1].name == "AdminService"

    tmp.unlink()


def test_python_analyzer_functions():
    """Detects Python function definitions."""
    code = textwrap.dedent("""
    def calculate_total(items):
        return sum(items)

    async def fetch_data(url):
        pass

    @lru_cache
    def cached_lookup(key):
        return {}
    """).strip()

    tmp = Path("/tmp/test_analyzer_funcs.py")
    tmp.write_text(code)

    analyzer = PythonAnalyzer()
    entities = analyzer.analyze_file(tmp)

    functions = [e for e in entities if e.kind == "function"]
    assert len(functions) == 3
    names = {f.name for f in functions}
    assert names == {"calculate_total", "fetch_data", "cached_lookup"}

    # Check decorator detection
    cached = [e for e in entities if e.name == "cached_lookup"]
    assert len(cached) == 1
    assert cached[0].metadata.get("decorator") == "lru_cache"

    tmp.unlink()


def test_empty_file():
    """Empty files produce no entities."""
    tmp = Path("/tmp/test_empty.py")
    tmp.write_text("")

    analyzer = PythonAnalyzer()
    entities = analyzer.analyze_file(tmp)

    assert len(entities) == 0
    tmp.unlink()


def test_analyze_directory(tmp_path):
    """Analyzes a directory of Python files."""
    (tmp_path / "module_a.py").write_text("class Foo:\n    pass\n")
    (tmp_path / "module_b.py").write_text("def bar():\n    return 42\n")

    analyzer = PythonAnalyzer()
    result = analyzer.analyze_directory(tmp_path)

    assert result.file_count == 2
    assert len(result.entities) == 2
    assert result.languages == ["python"]


def test_find_usages(tmp_path):
    """Finds usages of a name across files."""
    (tmp_path / "a.py").write_text("from lib import UserService\nsvc = UserService()\n")
    (tmp_path / "b.py").write_text("class UserService:\n    pass\n")

    analyzer = PythonAnalyzer()
    usages = analyzer.find_usages("UserService", [tmp_path / "a.py", tmp_path / "b.py"])

    assert len(usages) >= 2

def test_code_entity_fields():
    """CodeEntity has expected fields."""
    entity = CodeEntity(
        name="test_func",
        kind="function",
        file_path=Path("/tmp/test.py"),
        start_line=10,
        end_line=25,
        parent="MyClass",
        metadata={"async": True},
    )

    assert entity.name == "test_func"
    assert entity.kind == "function"
    assert entity.parent == "MyClass"
    assert entity.metadata["async"] is True
