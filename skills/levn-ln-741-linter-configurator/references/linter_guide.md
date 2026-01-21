# Linter Configuration Guide

<!-- SCOPE: ESLint/Prettier configuration rules ONLY. Contains config choices, rule explanations, conflict resolution. -->
<!-- DO NOT add here: Configuration workflow → ln-741-linter-configurator SKILL.md -->

Reference for ln-741-linter-configurator.

---

## TypeScript/React: ESLint + Prettier

### Why This Combination?

- **ESLint** catches code quality issues (bugs, bad patterns)
- **Prettier** handles formatting (spacing, quotes, semicolons)
- **eslint-config-prettier** prevents conflicts between them

### Key Configuration Choices

| Setting | Value | Rationale |
|---------|-------|-----------|
| Config format | Flat config (eslint.config.mjs) | Modern standard, better performance |
| TypeScript parser | typescript-eslint | Required for TS support |
| React plugin | eslint-plugin-react | React-specific rules |
| React hooks | eslint-plugin-react-hooks | Prevents hooks mistakes |

### Common Customizations

**Disable a rule:**
```javascript
rules: {
  '@typescript-eslint/no-explicit-any': 'off',
}
```

**Add stricter rules:**
```javascript
// Use tseslint.configs.strict instead of recommended
...tseslint.configs.strict,
```

---

## .NET: Roslyn Analyzers + dotnet format

### Why This Combination?

- **Roslyn Analyzers** provide compile-time code analysis
- **dotnet format** enforces .editorconfig rules
- **Directory.Build.props** applies settings to all projects

### Key Configuration Choices

| Setting | Value | Rationale |
|---------|-------|-----------|
| Nullable | enable | Catch null reference bugs |
| TreatWarningsAsErrors | true | Enforce quality in CI |
| AnalysisLevel | latest | Get newest analyzer rules |

### Common Customizations

**Suppress specific warning:**
```xml
<PropertyGroup>
  <NoWarn>CS1591</NoWarn> <!-- Missing XML comment -->
</PropertyGroup>
```

**Add additional analyzers:**
```xml
<ItemGroup>
  <PackageReference Include="StyleCop.Analyzers" Version="1.2.0-beta.556">
    <PrivateAssets>all</PrivateAssets>
  </PackageReference>
</ItemGroup>
```

---

## Python: Ruff

### Why Ruff?

Ruff is a single tool that replaces:
- Black (formatting)
- isort (import sorting)
- flake8 + plugins (linting)
- pyupgrade (syntax modernization)
- autoflake (unused import removal)

**Speed:** ~1000x faster than traditional tools.

### Key Configuration Choices

| Setting | Value | Rationale |
|---------|-------|-----------|
| target-version | py310+ | Modern Python features |
| line-length | 100 | Reasonable for modern screens |
| select | E, W, F, I, B, UP | Balanced rule set |

### Common Customizations

**Add more rule sets:**
```toml
select = [
    "E", "W", "F", "I", "B", "C4", "UP", "SIM",
    "S",      # flake8-bandit (security)
    "PTH",    # flake8-use-pathlib
    "ERA",    # eradicate (commented code)
]
```

**Ignore specific rules:**
```toml
ignore = [
    "E501",   # Line length (formatter handles)
    "B008",   # Function call in default argument
]
```

**Per-file ignores:**
```toml
[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101"]  # Allow assert in tests
"__init__.py" = ["F401"]  # Allow unused imports
```

---

## Verification Commands

| Stack | Lint | Format Check |
|-------|------|--------------|
| TypeScript | `npm run lint` | `npm run format:check` |
| .NET | `dotnet format --verify-no-changes` | (same command) |
| Python | `ruff check .` | `ruff format --check .` |

---

## Troubleshooting

### ESLint/Prettier Conflicts

**Symptom:** ESLint auto-fix changes formatting that Prettier then changes back.

**Solution:** Ensure eslint-config-prettier is last in config:
```javascript
export default tseslint.config(
  eslint.configs.recommended,
  ...tseslint.configs.recommended,
  prettier,  // MUST be last
);
```

### TypeScript Parser Errors

**Symptom:** `Parsing error: Cannot read file 'tsconfig.json'`

**Solution:** Add parserOptions:
```javascript
{
  languageOptions: {
    parserOptions: {
      project: true,
      tsconfigRootDir: import.meta.dirname,
    },
  },
}
```

### Ruff vs Black Formatting

**Symptom:** Different formatting between Ruff and existing Black config.

**Solution:** Ruff's formatter is Black-compatible by default. If migrating:
1. Remove Black from dependencies
2. Use `ruff format` instead of `black`
3. Remove .black.toml / pyproject.toml [tool.black]

---

**Version:** 1.0.0
**Last Updated:** 2026-01-10
