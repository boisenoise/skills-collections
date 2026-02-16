# Known Issues

Production-discovered problems and self-recovery patterns for pipeline lead.

| Symptom | Likely Cause | Self-Recovery |
|---------|-------------|---------------|
| Lead outputs generic text after long run | Context compression destroyed SKILL.md + state | Follow CONTEXT RECOVERY PROTOCOL in SKILL.md |
| Worker checkpoint/done.flag not found | Worker in worktree wrote to `.worktrees/` not project root | Verify PIPELINE_DIR in worker prompt = absolute path |
| hashline-edit tools unavailable | MCP tool references lost after compression | `ToolSearch("+hashline-edit")` to reload |
| Lead can't spawn workers after compression | team_name/business_answers lost | Read from `.pipeline/state.json` (persisted since Phase 3.2) |

---
**Version:** 1.0.0
**Last Updated:** 2026-02-15
