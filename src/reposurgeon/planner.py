"""Refactor planning — LLM-powered step generation."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from openai import OpenAI
from .analyzer.base import AnalysisResult

SYSTEM_PROMPT = """You are RepoSurgeon, an expert code refactoring agent.
Given a natural language description of a desired refactor and an AST analysis
of the codebase, produce a step-by-step plan.

Output ONLY valid JSON with this structure:
{
  "summary": "one-line summary of the refactor",
  "estimated_risk": "low|medium|high",
  "steps": [
    {
      "step": 1,
      "action": "rename|move|extract|inline|modify|delete",
      "target": "entity name being changed",
      "file": "relative/path/to/file",
      "description": "what this step does",
      "old_code": "original code snippet (5-10 lines for context)",
      "new_code": "replacement code snippet"
    }
  ]
}

Rules:
- Each step must be atomic (one change per file)
- Include surrounding context in old_code/new_code (not just the changed line)
- Order steps so dependencies come first (rename before update references)
- Be precise about file paths (use paths from the analysis)
- Only include files that actually need changes
"""


@dataclass
class PlanStep:
    """A single step in a refactor plan."""

    step: int
    action: str
    target: str
    file: str
    description: str
    old_code: str
    new_code: str


@dataclass
class RefactorPlan:
    """Complete refactor plan."""

    summary: str
    steps: List[PlanStep]
    affected_files: List[str]
    estimated_risk: str


def create_refactor_plan(
    description: str,
    analysis: AnalysisResult,
    repo_path: Path,
    model: str = "gpt-4o",
) -> RefactorPlan:
    """Create a refactor plan using LLM analysis.

    Args:
        description: Natural language refactor description
        analysis: AST analysis results
        repo_path: Path to the cloned repository
        model: LLM model to use

    Returns:
        A RefactorPlan with ordered steps
    """
    # Build context for the LLM
    entity_summary = "\n".join(
        f"  - {e.kind}: {e.name} in {e.file_path} "
        f"(lines {e.start_line}-{e.end_line})"
        for e in analysis.entities[:100]  # Limit context size
    )

    prompt = f"""Codebase Analysis:
Files: {analysis.file_count}
Languages: {', '.join(analysis.languages)}
Total lines: {analysis.total_lines}

Entities found:
{entity_summary}

Refactor Request: {description}

Create a step-by-step refactor plan."""

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Fallback: create a minimal plan without LLM
        return RefactorPlan(
            summary=f"Refactor: {description}",
            steps=[],
            affected_files=[],
            estimated_risk="unknown",
        )

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=4000,
    )

    plan_data = json.loads(response.choices[0].message.content)

    steps = [
        PlanStep(
            step=s["step"],
            action=s["action"],
            target=s["target"],
            file=s["file"],
            description=s["description"],
            old_code=s["old_code"],
            new_code=s["new_code"],
        )
        for s in plan_data["steps"]
    ]

    return RefactorPlan(
        summary=plan_data["summary"],
        steps=steps,
        affected_files=list(set(s["file"] for s in plan_data["steps"])),
        estimated_risk=plan_data.get("estimated_risk", "unknown"),
    )
