# Dependency Audit Commands

<!-- SCOPE: Dependency audit CLI commands ONLY. Contains npm/pip/dotnet audit commands, output formats. -->
<!-- DO NOT add here: Audit workflow → ln-762-dependency-audit SKILL.md, severity → severity_mapping.md -->

Reference for ecosystem-specific audit commands and tools.

---

## Node.js / npm

| Command | Purpose | Output |
|---------|---------|--------|
| `npm audit` | Check for vulnerabilities | Human-readable |
| `npm audit --json` | Machine-readable output | JSON |
| `npm audit --audit-level=high` | Fail only on high+ severity | Exit code |
| `npm audit fix` | Auto-fix safe updates | Modified package-lock |
| `npm audit fix --dry-run` | Preview fixes | No changes |
| `npm outdated` | Check for updates | Version comparison |

**Tool Alternatives:**
- `npx audit-ci` - CI-friendly wrapper
- `snyk test` - Commercial scanner (free tier available)

---

## .NET / NuGet

| Command | Purpose | Output |
|---------|---------|--------|
| `dotnet list package --vulnerable` | Check vulnerable packages | Human-readable |
| `dotnet list package --outdated` | Check for updates | Version comparison |
| `dotnet list package --deprecated` | Check deprecated packages | Warning list |

**Tool Alternatives:**
- `dotnet-outdated` - Global tool for updates
- NuGet Package Explorer - GUI for package analysis

---

## Python / pip

| Tool | Command | Purpose |
|------|---------|---------|
| **pip-audit** | `pip-audit` | OSV database check |
| **pip-audit** | `pip-audit --fix` | Auto-fix vulnerabilities |
| **safety** | `safety check` | PyUp.io database check |
| **safety** | `safety check --full-report` | Detailed output |

**Note:** pip-audit is preferred (OSV database is more comprehensive).

---

## Go

| Command | Purpose | Output |
|---------|---------|--------|
| `govulncheck ./...` | Check for vulnerabilities | Human-readable |
| `go list -m all` | List all modules | Module list |
| `go mod tidy` | Clean up go.mod | Modified go.mod |

---

## Ruby / Bundler

| Command | Purpose | Output |
|---------|---------|--------|
| `bundle audit check` | Check for vulnerabilities | Human-readable |
| `bundle audit update` | Update advisory database | Database update |
| `bundle outdated` | Check for updates | Version comparison |

---

## Rust / Cargo

| Command | Purpose | Output |
|---------|---------|--------|
| `cargo audit` | Check for vulnerabilities | Human-readable |
| `cargo audit --json` | Machine-readable output | JSON |
| `cargo outdated` | Check for updates | Version comparison |

---

## PHP / Composer

| Command | Purpose | Output |
|---------|---------|--------|
| `composer audit` | Check for vulnerabilities | Human-readable |
| `composer outdated` | Check for updates | Version comparison |

---

## Detection Priority

When multiple ecosystems detected, audit in order:
1. Lock files present (deterministic results)
2. Primary ecosystem (by file count/size)
3. Secondary ecosystems

---

**Version:** 1.0.0
**Last Updated:** 2026-01-10
