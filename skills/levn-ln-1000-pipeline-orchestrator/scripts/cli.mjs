#!/usr/bin/env node
/**
 * Pipeline state CLI — deterministic state management for ln-1000.
 * Usage: node cli.mjs <command> [--args]
 * Output: JSON to stdout, errors to stderr.
 * Exit: 0=ok, 1=guard rejection, 2=error.
 */

import { parseArgs } from "node:util";
import {
    startRun, getStatus, saveState, saveCheckpoint,
    loadState, loadCheckpoint, completeRun, cancelRun, pauseRun, updateState,
} from "./lib/store.mjs";
import { validateTransition } from "./lib/guards.mjs";
import { captureBaseline, computeDelta } from "./lib/arch-snapshot.mjs";

const { values, positionals } = parseArgs({
    allowPositionals: true,
    options: {
        story: { type: "string" },
        title: { type: "string" },
        to: { type: "string" },
        stage: { type: "string" },
        storage: { type: "string" },
        reason: { type: "string" },
        force: { type: "boolean", default: false },
        resolve: { type: "boolean", default: false },
        // Checkpoint fields
        "plan-score": { type: "string" },
        readiness: { type: "string" },
        verdict: { type: "string" },
        "quality-score": { type: "string" },
        issues: { type: "string" },
        "last-action": { type: "string" },
        "tasks-completed": { type: "string" },
        "tasks-remaining": { type: "string" },
        "agents-info": { type: "string" },
        "git-stats": { type: "string" },
        // Start fields
        "project-brief": { type: "string" },
        "story-briefs": { type: "string" },
        "business-answers": { type: "string" },
        "status-cache": { type: "string" },
        "skill-repo-path": { type: "string" },
        "worktree-dir": { type: "string" },
        "branch-name": { type: "string" },
    },
});

const command = positionals[0];

function output(data) { process.stdout.write(JSON.stringify(data, null, 2) + "\n"); }
function fail(msg, code = 2) { process.stderr.write(JSON.stringify({ error: msg }) + "\n"); process.exit(code); }
function tryParse(str) { try { return JSON.parse(str); } catch { return str; } }

async function main() {
    switch (command) {
        case "start": {
            const result = startRun(null, {
                story: values.story,
                title: values.title,
                storage: values.storage,
                projectBrief: tryParse(values["project-brief"]),
                storyBriefs: tryParse(values["story-briefs"]),
                businessAnswers: tryParse(values["business-answers"]),
                statusCache: tryParse(values["status-cache"]),
                skillRepoPath: values["skill-repo-path"],
                worktreeDir: values["worktree-dir"],
                branchName: values["branch-name"],
            });
            if (!result.ok && result.recovery) {
                output({ recovery: true, state: result.state });
                return;
            }
            if (!result.ok) fail(result.error);
            output(result);
            break;
        }

        case "status": {
            const result = getStatus(null, values.story);
            output(result);
            break;
        }

        case "advance": {
            const toStage = values.to;
            if (!toStage) fail("--to required");

            const state = loadState(null);
            if (!state || state.complete) fail("No active run");

            // Handle PAUSED -> resume with --resolve
            if (state.stage === "PAUSED" && (values.resolve || values.force)) {
                state.stage = toStage;
                state.paused_reason = null;
                saveState(null, state);
                output({ ok: true, previous_stage: "PAUSED", current_stage: toStage });
                break;
            }

            const checkpoint = loadCheckpoint(null, state.story_id);
            const guard = validateTransition(state, toStage, checkpoint);
            if (!guard.ok) {
                output({ ok: false, ...guard });
                process.exit(1);
            }

            const previous = state.stage;

            // Architecture baseline on STAGE_2 entry
            if (toStage === "STAGE_2" && previous !== "STAGE_2") {
                const baseline = await captureBaseline(process.cwd());
                if (baseline) state.baseline_architecture = baseline;
            }

            // Architecture delta on STAGE_3 entry
            if (toStage === "STAGE_3") {
                const delta = await computeDelta(state.baseline_architecture || null, process.cwd());
                if (delta) {
                    // Store delta in checkpoint (will be picked up by next checkpoint write)
                    state._pending_arch_delta = delta;
                }
            }

            state.stage = toStage;
            if (toStage === "DONE") {
                state.complete = true;
            }
            // Record stage timestamp
            const stageNum = toStage.replace("STAGE_", "");
            if (!isNaN(parseInt(stageNum, 10))) {
                state.stage_timestamps = state.stage_timestamps || {};
                state.stage_timestamps[`stage_${stageNum}_start`] = new Date().toISOString();
            }

            saveState(null, state);
            output({
                ok: true,
                previous_stage: previous,
                current_stage: toStage,
                counter_incremented: guard.counter_incremented || null,
            });
            break;
        }

        case "checkpoint": {
            const stageStr = values.stage;
            if (stageStr == null) fail("--stage required");
            const stage = parseInt(stageStr, 10);

            const state = loadState(null);
            if (!state || state.complete) fail("No active run");

            // Record stage end timestamp
            state.stage_timestamps = state.stage_timestamps || {};
            state.stage_timestamps[`stage_${stage}_end`] = new Date().toISOString();

            const checkpoint = {
                stage,
                started_at: state.stage_timestamps[`stage_${stage}_start`] || new Date().toISOString(),
                completed_at: new Date().toISOString(),
                tasks_completed: tryParse(values["tasks-completed"]) || [],
                tasks_remaining: tryParse(values["tasks-remaining"]) || [],
                last_action: values["last-action"] || "",
            };

            // Stage-specific fields
            if (values["plan-score"] != null) checkpoint.plan_score = parseFloat(values["plan-score"]);
            if (values.readiness != null) checkpoint.readiness = parseFloat(values.readiness);
            if (values.verdict != null) checkpoint.verdict = values.verdict;
            if (values.reason != null) checkpoint.reason = values.reason;
            if (values["quality-score"] != null) checkpoint.quality_score = parseFloat(values["quality-score"]);
            if (values.issues != null) checkpoint.issues = values.issues;
            if (values["agents-info"] != null) checkpoint.agents_info = values["agents-info"];
            if (values["git-stats"] != null) checkpoint.git_stats = tryParse(values["git-stats"]);

            // Architecture delta from advance
            if (state._pending_arch_delta) {
                checkpoint.architecture_delta = state._pending_arch_delta;
                delete state._pending_arch_delta;
            }

            saveCheckpoint(null, state.story_id, checkpoint);
            saveState(null, state);
            output({ ok: true, stage, story_id: state.story_id });
            break;
        }

        case "pause": {
            if (!values.reason) fail("--reason required");
            const result = pauseRun(null, values.reason);
            if (!result.ok) fail(result.error);
            output(result);
            break;
        }

        case "cancel": {
            const result = cancelRun(null, values.reason || "Canceled by user");
            if (!result.ok) fail(result.error);
            output(result);
            break;
        }

        default:
            fail(`Unknown command: ${command}. Use: start, status, advance, checkpoint, pause, cancel`);
    }
}

main().catch(err => fail(err.message));
