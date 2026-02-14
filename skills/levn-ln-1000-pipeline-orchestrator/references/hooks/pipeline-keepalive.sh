#!/bin/bash
# Stop hook for pipeline lead — prevents Claude from stopping while pipeline is active.
# Exit code 2 = "don't stop" (Claude Code hooks protocol).
# This hook IS the heartbeat driver: each exit 2 creates a new agentic loop iteration
# where queued worker messages get delivered and processed by ON handlers in Phase 4.
# Lead writes .pipeline/state.json with complete=false during pipeline execution.
# Phase 5 sets complete=true before cleanup, allowing graceful stop.
# Lead writes .pipeline/lead-session.id at pipeline start — only that session gets heartbeat.

INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id')

PIPELINE_STATE=$(cat .pipeline/state.json 2>/dev/null || echo '{"complete": true}')
COMPLETE=$(echo "$PIPELINE_STATE" | jq -r '.complete')

if [ "$COMPLETE" = "false" ]; then
  LEAD_SESSION=$(cat .pipeline/lead-session.id 2>/dev/null || echo "")
  if [ "$SESSION_ID" = "$LEAD_SESSION" ] || [ -z "$LEAD_SESSION" ]; then
    WORKERS=$(echo "$PIPELINE_STATE" | jq -r '.active_workers // 0')
    REMAINING=$(echo "$PIPELINE_STATE" | jq -r '.stories_remaining // 0')
    LAST=$(echo "$PIPELINE_STATE" | jq -r '.last_check // "unknown"')
    echo "HEARTBEAT: ${WORKERS} active workers, ${REMAINING} stories remaining. Last check: ${LAST}. Process any queued worker messages now." >&2
    sleep 60
    exit 2
  fi
fi

exit 0
