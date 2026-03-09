# Context Review Pipeline (mode=context)

MCP Ref research pipeline for mode=context foreground work. Runs in parallel with agent background tasks.

## Applicability Check

Scan `context_files` for technology decision signals. No signals → skip MCP Ref research (steps c-e), proceed to Phase 5.

| Signal Type | Examples |
|-------------|---------|
| Infrastructure choice | Redis, PostgreSQL, K8s, Docker, RabbitMQ |
| API/protocol decision | REST vs GraphQL, WebSocket, gRPC, OAuth 2.0 |
| Security mechanism | JWT, PKCE, CORS, rate limiting, OWASP |
| Library/framework choice | FastAPI, Polly, SQLAlchemy, Pydantic |
| Architectural pattern | CQRS, event sourcing, middleware chain, DI |
| Configuration/tooling | ESLint, Prettier, CI config |

## Stack Detection

Priority order for `query_prefix`:

1. `tech_stack` input parameter → use directly
2. `docs/tools_config.md` Research section → extract stack hints
3. Glob for indicator files:

| Indicator | Stack | Query Prefix |
|-----------|-------|--------------|
| `*.csproj`, `*.sln` | .NET | `"C# ASP.NET Core"` |
| `package.json` + `tsconfig.json` | Node.js | `"TypeScript Node.js"` |
| `requirements.txt`, `pyproject.toml` | Python | `"Python"` |
| `go.mod` | Go | `"Go Golang"` |
| `Cargo.toml` | Rust | `"Rust"` |
| `build.gradle`, `pom.xml` | Java | `"Java"` |

4. Parse context_files for technology mentions (fallback heuristic)

## Compare & Correct Safety Rules

1. **Max 5 corrections** per run
2. **Must cite** specific RFC/standard/doc for each correction
3. **Only correct** when official docs **directly contradict** plan statement (high confidence)
4. Each correction = surgical Edit with inline rationale `"(per {RFC/standard}: ...)"`
5. Ambiguous findings → record as `"REVIEW NEEDED"` (not auto-corrected)
