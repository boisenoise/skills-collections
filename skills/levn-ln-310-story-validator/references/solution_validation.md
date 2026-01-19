# Solution Validation (Criterion #6)

Detailed rules for library version verification.

---

## Criterion #6: Library & Version

**Check:** Libraries are latest stable versions

**Penalty:** HIGH (5 points)

✅ **GOOD:**
- "Using express v4.19.2 (latest stable as of 2025-01)"
- "Prisma v5.8.1 (current stable, verified via npm)"
- "OAuth2-proxy v7.6.0 (latest release)"

❌ **BAD:**
- "Using express v3.x" (outdated, v4.x available)
- "Any JWT library" (no specific version)
- "Latest version" (no verification)

**Auto-fix actions:**
1. Check if manuals exist from Phase 2 research (created by ln-002)
2. IF manuals exist:
   - Read recommended version from manual (e.g., Manual: oauth2-proxy v7.6.0)
   - Compare with Story Technical Notes current version
   - IF outdated or unspecified → Update with version from manual
   - Add manual reference: "See [Manual: library-vX](docs/manuals/library-vX.md)"
3. IF no manuals exist (fallback to Context7):
   - Query `mcp__context7__resolve-library-id(libraryName="[library]")`
   - Query `mcp__context7__query-docs(libraryId="...", query="latest version")`
   - Extract latest stable version from docs
   - Add inline reference: "Library v[version] (verified via Context7)"
4. Update Linear issue via `mcp__linear-server__update_issue`
5. Add comment: "Library versions verified and updated"

**Example transformation:**

**Before:**
```markdown
## Technical Notes

### Integration Points
- Use Passport.js for authentication
- PostgreSQL database
```

**After (with manuals from ln-002):**
```markdown
## Technical Notes

### Integration Points
- Passport.js v0.7.0 (latest stable, see [Manual: Passport v0.7](docs/manuals/passport-v0.7.md))
- PostgreSQL v16.1 (compatible with Prisma v5.8.1, see [Manual: Prisma v5](docs/manuals/prisma-v5.md))

### Library References
| Library | Version | Source |
|---------|---------|--------|
| passport | v0.7.0 | docs/manuals/passport-v0.7.md |
| @prisma/client | v5.8.1 | docs/manuals/prisma-v5.md |
| postgresql | v16.1 | Context7 verified |
```

**Skip Fix When:**
- All libraries have specific versions with sources
- Story in Done/Canceled status

---

## Execution Notes

**Sequential Dependency:**
- Criterion #6 depends on #1-#5 being completed first
- Cannot verify libraries until Technical Notes exist (#1)
- Cannot verify libraries until Standards checked (#5)

**Research Integration:**
- Phase 2 creates documentation via ln-002 delegation
- Criterion #6 reads from Phase 2 docs, fallback to Context7 if needed
- All research completed BEFORE Phase 4 auto-fix begins

**Linear Updates:**
- Criterion auto-fix updates Linear issue once
- Add single comment summarizing library version updates

---

**Version:** 3.0.0
**Last Updated:** 2025-01-07
