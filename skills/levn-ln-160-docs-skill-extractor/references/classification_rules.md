# Classification Rules: Procedural vs Declarative

<!-- DO NOT add here: Workflow phases -> ln-160-docs-skill-extractor SKILL.md -->

Score each H2/H3 section independently. Sum weights per category, then apply thresholds.

## Procedural Signals

| Signal | Weight | Detection Pattern |
|--------|--------|-------------------|
| Numbered steps (3+) | +3 | `^\d+\.` or `Step \d` with 3+ consecutive occurrences |
| Shell/bash code blocks | +2 | Fenced blocks with `bash`, `sh`, `shell`, `zsh` |
| Imperative verbs at line start | +2 | Run, Execute, Deploy, Install, SSH, Connect, Stop, Start, Configure, Check, Verify, Build, Restart |
| Troubleshooting patterns | +2 | Headers containing: Troubleshoot, Fix, Debug, If...then, When... |
| Prerequisites section | +1 | `## Prerequisites`, `## Requirements`, `Before you begin` |
| CLI tool invocations | +1 | npm, docker, kubectl, git, pip, dotnet, curl, wget, ssh |
| Conditional instructions | +1 | `If {condition}, {action}` patterns with imperative follow-up |

## Declarative Signals

| Signal | Weight | Detection Pattern |
|--------|--------|-------------------|
| Architecture descriptions | +2 | layer, component, module, pattern, principle, architecture |
| Requirement statements | +2 | shall, must support, requirement, feature, constraint |
| Data tables (no commands) | +1 | Tables with columns like Version, Type, Schema (no action items) |
| API spec format | +1 | Endpoint definitions, request/response schemas, HTTP methods |
| Diagrams | +1 | mermaid, plantuml, ASCII box drawings, C4 notation |
| Reference lists | +1 | >50% content is links/references to other docs |

## Thresholds

| Condition | Classification | Action |
|-----------|---------------|--------|
| proc >= 4 AND proc > decl * 2 | **PROCEDURAL** | Extract to .claude/commands/ |
| decl >= 4 AND decl > proc * 2 | **DECLARATIVE** | Keep as documentation |
| Both >= 3 | **MIXED** | Extract procedural subsections only |
| Both < 3 | **THIN** | Skip (insufficient content) |

## Source-Specific Hints

Override scoring when source document purpose is unambiguous:

| Source | Sections | Expected Classification |
|--------|----------|------------------------|
| runbook.md | All sections | PROCEDURAL |
| infrastructure.md | Server Inventory, Port Allocation | DECLARATIVE |
| infrastructure.md | SSH Access, Service Management | PROCEDURAL |
| testing-strategy.md | Philosophy, Principles | DECLARATIVE |
| testing-strategy.md | Running Tests, Test Commands | PROCEDURAL |
| tests/README.md | Test Organization | DECLARATIVE |
| tests/README.md | Running Tests, Quick Commands | PROCEDURAL |
| guides/* | Pattern tables (Do/Don't/When) | DECLARATIVE |
| guides/* | Setup/Configuration sections | PROCEDURAL |
| manuals/* | API reference | DECLARATIVE |
| manuals/* | Installation/Usage | PROCEDURAL |

## Command Name Generation

Derive command filename from section content:

1. Take the H2/H3 header text
2. Lowercase, replace spaces with hyphens
3. Remove articles (a, an, the) and prepositions (of, for, with)
4. Truncate to 3 words max
5. Add `.md` extension

Examples: "Deployment Procedure" -> `deploy.md`, "Running E2E Tests" -> `run-e2e-tests.md`, "SSH Access to Production" -> `ssh-production.md`
