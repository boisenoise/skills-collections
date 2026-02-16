#!/bin/bash
# TeammateIdle hook — prevents workers from going idle while they have active stage assignments.
# Exit code 2 = "don't idle, keep working" (Claude Code hooks protocol).
# Lead creates .pipeline/worker-{name}-active.flag when assigning a stage.
# Worker creates .pipeline/worker-{name}-done.flag AFTER receiving ACK from lead.
# Lead removes both flags after processing worker's stage completion report.

INPUT=$(cat)
TEAMMATE=$(echo "$INPUT" | jq -r '.teammate_name')

if [ -f ".pipeline/worker-${TEAMMATE}-active.flag" ] && [ ! -f ".pipeline/worker-${TEAMMATE}-done.flag" ]; then
  echo "You have an active stage assignment. Continue working." >&2
  exit 2
fi

exit 0
