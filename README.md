# RepoSurgeon

Autonomous codebase refactoring agent. Point it at any GitHub repo, describe the change in natural language, and it clones, analyzes, plans, executes, and submits an atomic PR.

```bash
reposurgeon refactor https://github.com/user/repo \
    -d "Migrate all class-based views to function-based views"
```

## How It Works

1. **Clone** — Clones the target repository into an isolated workspace
2. **Analyze** — Parses the entire codebase with tree-sitter AST (Python + TypeScript)
3. **Plan** — Uses an LLM to generate a step-by-step refactor plan from the AST analysis + your description
4. **Execute** — Applies each step via precise string replacement, in order
5. **PR** — Commits changes and creates a GitHub pull request

## Installation

```bash
pip install reposurgeon
```

Or from source:

```bash
git clone https://github.com/reposurgeon/reposurgeon.git
cd reposurgeon
pip install -e ".[dev]"
```

## Quick Start

```bash
# Set your GitHub token (for PR creation)
export GITHUB_TOKEN=ghp_xxx

# Set your OpenAI key (for planning)
export OPENAI_API_KEY=sk-xxx

# Run a refactor
reposurgeon refactor https://github.com/user/repo \
    -d "Rename UserService to AccountService across the entire codebase"

# Dry run (plan only, no changes)
reposurgeon refactor https://github.com/user/repo \
    -d "Extract helper functions from god objects" \
    --dry-run

# Use a specific branch
reposurgeon refactor https://github.com/user/repo \
    -d "Add type hints to all function signatures" \
    -b "refactor/add-types"
```

## Supported Languages

| Language | Analyzer | Status |
|----------|----------|--------|
| Python | tree-sitter | ✅ |
| TypeScript | tree-sitter | ✅ |
| JavaScript | tree-sitter | ✅ |
| Go | Planned | 🚧 |
| Rust | Planned | 🚧 |

## Configuration

| Env Var | Required | Description |
|---------|----------|-------------|
| `GITHUB_TOKEN` | For PRs | GitHub personal access token with repo scope |
| `OPENAI_API_KEY` | For planning | OpenAI API key (supports any OpenAI-compatible endpoint) |

## Refactor Operations

RepoSurgeon can perform these operations:

- **Rename** — Rename classes, functions, variables
- **Move** — Move code between files
- **Extract** — Extract logic into helper functions/classes
- **Inline** — Inline simple functions back into callers
- **Modify** — Change signatures, add parameters, update logic
- **Delete** — Remove dead code safely

## Architecture

```
reposurgeon/
├── cli.py          # Click CLI (refactor, analyze commands)
├── pipeline.py     # Orchestration: clone→analyze→plan→execute→PR
├── repo.py         # Git operations (clone, branch, commit, push)
├── analyzer/       # Multi-language AST analysis
│   ├── base.py     # Abstract analyzer interface
│   ├── python.py   # Python via tree-sitter
│   └── typescript.py  # TypeScript/JS via tree-sitter
├── planner.py      # LLM-powered refactor planning
├── executor.py     # Apply planned changes to files
├── pr.py           # GitHub PR creation
└── utils.py        # Shared utilities
```

## Why RepoSurgeon?

Most "AI coding tools" are chatbots — you explain what you want, they generate code, you copy-paste. RepoSurgeon is different:

- **Autonomous** — Runs the entire pipeline without babysitting
- **AST-aware** — Understands code structure, not just text matching
- **Multi-file** — Handles complex refactors across hundreds of files
- **Verifiable** — Every change is in a clean PR you can review before merging
- **Language-agnostic core** — Easy to add support for new languages

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup.

## License

MIT © RepoSurgeon Contributors
