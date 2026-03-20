# Deprecated Claude Code APIs

Features removed from Claude Code that skills should not reference.

| Feature | Removed In | Replacement | Detection Pattern |
|---------|-----------|-------------|-------------------|
| `Agent(resume: id)` | 2.1.77 | `SendMessage({to: agentId})` | `Agent(resume:` |
| `effort: "max"` | 2.1.72 | `effort: "high"` | `effort.*max` |
| `TeamCreate` for sequential pipelines | 2026 (repo decision) | Sequential `Skill()` calls | `TeamCreate` in pipeline context |

**Update this file** when new Claude Code versions deprecate features.
