/**
 * Pipeline state store — atomic JSON read/write with reconciliation.
 * Single writer per project (lock file). State in .hex-skills/pipeline/.
 */

import { existsSync, mkdirSync, writeFileSync, renameSync, unlinkSync, readdirSync, readFileSync } from "node:fs";
import { join, dirname } from "node:path";

const LOCK_FILE = ".lock";

// --- Atomic write (flush + rename in same dir) ---

export function atomicWrite(filePath, data) {
    const dir = dirname(filePath);
    if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
    const tmp = `${filePath}.hexline-tmp-${process.pid}`;
    try {
        writeFileSync(tmp, JSON.stringify(data, null, 2) + "\n", { encoding: "utf-8", flush: true });
        renameSync(tmp, filePath);
    } catch (err) {
        try { unlinkSync(tmp); } catch { /* best-effort */ }
        throw err;
    }
}

function safeRead(filePath) {
    try {
        return JSON.parse(readFileSync(filePath, "utf-8"));
    } catch {
        return null;
    }
}

// --- Stale temp cleanup ---

function cleanStaleTmps(dir) {
    if (!existsSync(dir)) return;
    for (const f of readdirSync(dir)) {
        if (f.endsWith(".hexline-tmp-" + process.pid) || f.match(/\.hexline-tmp-\d+$/)) {
            try { unlinkSync(join(dir, f)); } catch { /* ignore */ }
        }
    }
}

// --- Lock file (single-writer guard) ---

function acquireLock(dir) {
    const lockPath = join(dir, LOCK_FILE);
    if (existsSync(lockPath)) {
        const lockData = safeRead(lockPath);
        if (lockData?.pid) {
            try {
                process.kill(lockData.pid, 0); // check if alive
                return { ok: false, error: `Pipeline already running (PID ${lockData.pid})` };
            } catch {
                // stale lock — process dead
            }
        }
    }
    atomicWrite(lockPath, { pid: process.pid, started_at: new Date().toISOString() });
    return { ok: true };
}

function releaseLock(dir) {
    const lockPath = join(dir, LOCK_FILE);
    try { unlinkSync(lockPath); } catch { /* ignore */ }
}

// --- Pipeline dir resolution ---

export function pipelineDir(projectRoot) {
    return join(projectRoot || process.cwd(), ".hex-skills", "pipeline");
}

function statePath(dir) { return join(dir, "state.json"); }
function checkpointPath(dir, storyId) { return join(dir, `checkpoint-${storyId}.json`); }

// --- State CRUD ---

export function loadState(projectRoot) {
    const dir = pipelineDir(projectRoot);
    return safeRead(statePath(dir));
}

export function loadCheckpoint(projectRoot, storyId) {
    const dir = pipelineDir(projectRoot);
    return safeRead(checkpointPath(dir, storyId));
}

export function saveState(projectRoot, state) {
    const dir = pipelineDir(projectRoot);
    state.updated_at = new Date().toISOString();
    atomicWrite(statePath(dir), state);
}

export function saveCheckpoint(projectRoot, storyId, checkpoint) {
    const dir = pipelineDir(projectRoot);
    atomicWrite(checkpointPath(dir, storyId), checkpoint);
}

// --- Start run ---

export function startRun(projectRoot, opts) {
    const dir = pipelineDir(projectRoot);
    cleanStaleTmps(dir);

    // Check for active run
    const existing = loadState(projectRoot);
    if (existing && !existing.complete) {
        return { ok: false, recovery: true, state: existing };
    }

    const lock = acquireLock(dir);
    if (!lock.ok) return lock;

    const state = {
        story_id: opts.story,
        story_title: opts.title || "",
        stage: "QUEUED",
        complete: false,
        quality_cycles: 0,
        validation_retries: 0,
        crash_count: 0,
        storage_mode: opts.storage || "file",
        pipeline_start_time: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        project_brief: opts.projectBrief || null,
        story_briefs: opts.storyBriefs || {},
        business_answers: opts.businessAnswers || {},
        status_cache: opts.statusCache || {},
        skill_repo_path: opts.skillRepoPath || "",
        worktree_dir: opts.worktreeDir || "",
        branch_name: opts.branchName || "",
        stage_timestamps: {},
        git_stats: {},
        readiness_scores: {},
        infra_issues: [],
        previous_quality_score: {},
        story_results: {},
        paused_reason: null,
    };
    saveState(projectRoot, state);
    return { ok: true, state };
}

// --- Status with reconciliation ---

export function getStatus(projectRoot, storyId) {
    const state = loadState(projectRoot);
    if (!state) return { ok: true, active: false };
    if (state.complete) return { ok: true, active: false, state };

    const id = storyId || state.story_id;
    const checkpoint = loadCheckpoint(projectRoot, id);

    // Reconciliation: if checkpoint exists but stage disagrees, mark PAUSED
    if (checkpoint && state.stage !== "QUEUED") {
        const stageNum = parseInt(state.stage.replace("STAGE_", ""), 10);
        if (!isNaN(stageNum) && checkpoint.stage > stageNum) {
            state.stage = `STAGE_${checkpoint.stage}`;
            state.paused_reason = `Reconciled: checkpoint at stage ${checkpoint.stage}, state was behind`;
            saveState(projectRoot, state);
        }
    }

    // Compute resume_action
    const resumeAction = computeResumeAction(state, checkpoint);

    return {
        ok: true,
        active: true,
        state,
        checkpoint: checkpoint || null,
        resume_action: resumeAction,
    };
}

function computeResumeAction(state, checkpoint) {
    const stage = state.stage;
    if (stage === "DONE") return "Pipeline complete";
    if (stage === "PAUSED") return `Paused: ${state.paused_reason || "unknown reason"}. Use --resolve to continue.`;
    if (stage === "QUEUED") return "Determine target stage from kanban, then advance";

    const stageNum = parseInt(stage.replace("STAGE_", ""), 10);
    if (isNaN(stageNum)) return `Unknown stage: ${stage}`;

    const hasCheckpoint = checkpoint && checkpoint.stage === stageNum;
    if (hasCheckpoint) {
        // Checkpoint exists for current stage — advance to next
        const skills = ["ln-300", "ln-310", "ln-400", "ln-500"];
        const nextStage = stageNum + 1;
        if (nextStage > 3) return "Advance to DONE";
        return `Advance to STAGE_${nextStage}, then invoke Skill(${skills[nextStage]})`;
    }
    // No checkpoint — invoke current stage skill
    const skills = ["ln-300", "ln-310", "ln-400", "ln-500"];
    return `Invoke Skill(${skills[stageNum]}) for stage ${stageNum}`;
}

// --- Complete / Cancel ---

export function completeRun(projectRoot) {
    const state = loadState(projectRoot);
    if (!state) return { ok: false, error: "No active run" };
    state.complete = true;
    state.stage = "DONE";
    saveState(projectRoot, state);
    releaseLock(pipelineDir(projectRoot));
    return { ok: true };
}

export function cancelRun(projectRoot, reason) {
    const state = loadState(projectRoot);
    if (!state) return { ok: false, error: "No active run" };
    state.complete = true;
    state.paused_reason = reason || "Canceled";
    saveState(projectRoot, state);
    releaseLock(pipelineDir(projectRoot));
    return { ok: true };
}

export function pauseRun(projectRoot, reason) {
    const state = loadState(projectRoot);
    if (!state) return { ok: false, error: "No active run" };
    state.stage = "PAUSED";
    state.paused_reason = reason;
    saveState(projectRoot, state);
    return { ok: true };
}

// --- Update state fields ---

export function updateState(projectRoot, updates) {
    const state = loadState(projectRoot);
    if (!state) return { ok: false, error: "No active run" };
    Object.assign(state, updates);
    saveState(projectRoot, state);
    return { ok: true, state };
}

// --- Cleanup ---

export function cleanup(projectRoot) {
    const dir = pipelineDir(projectRoot);
    releaseLock(dir);
    // State files left for forensics; user deletes .hex-skills/pipeline/ manually
}
