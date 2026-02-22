---
description: Enforces the dual-audience documentation standards across the AegisAI codebase.
---

# Documentation Standards

## Purpose
Enforces the dual-audience documentation standards across the AegisAI codebase, ensuring absolute clarity for human developers while providing structured metadata and explicit context for autonomous AI agents.

## Responsibilities
- Validate the presence of file-level header comments.
- Enforce comprehensive function/class/method-level docstrings.
- Ensure every component contains an explicit "Agent Usage Note".
- Prevent documentation anti-patterns such as outdated info, fragmentation, and jargon overload.

## Dependencies
- Language Context: Python (FastAPI/SQLAlchemy).
- Best practices derived from Google/Microsoft Dev Style Guides.

## Who/What Should Use It
- AI Agents evaluating or modifying the codebase.
- Human reviewers performing Pull Request checks.

## Agent Usage Note
- **Triggering Condition:** Invoke this standard *whenever* creating a new code file, refactoring logic, or modifying an existing, undocumented file. Do not use for non-code assets.
- **Input Contract:** The target source code chunk or module needing evaluation.
- **Output Contract:** The corrected source code populated with injected file headers, detailed parameter docs, and an "Agent Usage Note".

### Step-by-Step Instructions for Agents:
1. **Analyze Context:** Read the target file thoroughly to glean its core purpose and downstream dependencies.
2. **Inject File Header:** Prepend a module docstring that defines Purpose, Responsibilities, Dependencies, Who/What Should Use It, and an Agent Usage Note.
3. **Draft Docstrings:** For every class and public/private method, embed a docstring enumerating a description, precise parameters (name, type, meaning), return shapes, potential exceptions raised, and a highly realistic code usage example.
4. **Enforce Constraints:** Ensure the new documentation operates within clear boundaries. Avoid implying non-existent system capabilities (hallucinations).
5. **Anti-Patterns Check:** Final pass to guarantee information accuracy. Eliminate "TODO" docstrings. Format using Markdown conventions within the Python docstring bounds.

## Changelog
- **[2026-02-22]** Initial rewrite to match the new dual-audience documentation standard, incorporating structured JSON-ready metadata methodologies and strict trigger definitions to minimize agent hallucinations and off-target executions.
