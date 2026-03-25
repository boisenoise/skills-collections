/**
 * Pipeline transition guards — full matrix from pipeline_states.md.
 * CLI guards complement but do NOT replace kanban ASSERTs.
 */

const TRANSITIONS = new Map([
    // QUEUED routing (determined by kanban status)
    ["QUEUED->STAGE_0", (state, cp) => ({ ok: true })],
    ["QUEUED->STAGE_1", (state, cp) => ({ ok: true })],
    ["QUEUED->STAGE_2", (state, cp) => ({ ok: true })],
    ["QUEUED->STAGE_3", (state, cp) => ({ ok: true })],

    // Stage 0 -> Stage 1
    ["STAGE_0->STAGE_1", (state, cp) => {
        if (!cp || cp.stage !== 0) return { ok: false, error: "Stage 0 checkpoint missing", recovery: "Run ln-300 first" };
        return { ok: true };
    }],
    ["STAGE_0->PAUSED", (state, cp) => ({ ok: true })],

    // Stage 1 -> Stage 2 (requires GO + readiness >= 5)
    ["STAGE_1->STAGE_2", (state, cp) => {
        if (!cp || cp.stage !== 1) return { ok: false, error: "Stage 1 checkpoint missing", recovery: "Run ln-310 first" };
        if (cp.verdict !== "GO") return { ok: false, error: `Verdict is ${cp.verdict}, not GO`, recovery: "Fix validation issues" };
        if (cp.readiness != null && cp.readiness < 5) return { ok: false, error: `Readiness ${cp.readiness} < 5`, recovery: "Improve story quality" };
        return { ok: true };
    }],

    // Stage 1 retry (NO-GO, validation_retries < 1)
    ["STAGE_1->STAGE_1", (state, cp) => {
        if (state.validation_retries >= 1) return { ok: false, error: "Validation retry exhausted", recovery: "Escalate to user" };
        state.validation_retries++;
        return { ok: true, counter_incremented: "validation_retries" };
    }],
    ["STAGE_1->PAUSED", (state, cp) => ({ ok: true })],

    // Stage 2 -> Stage 3
    ["STAGE_2->STAGE_3", (state, cp) => {
        if (!cp || cp.stage !== 2) return { ok: false, error: "Stage 2 checkpoint missing", recovery: "Run ln-400 first" };
        return { ok: true };
    }],
    ["STAGE_2->PAUSED", (state, cp) => ({ ok: true })],

    // Stage 3 -> DONE
    ["STAGE_3->DONE", (state, cp) => {
        if (!cp || cp.stage !== 3) return { ok: false, error: "Stage 3 checkpoint missing", recovery: "Run ln-500 first" };
        const validVerdicts = ["PASS", "CONCERNS", "WAIVED"];
        if (!validVerdicts.includes(cp.verdict)) return { ok: false, error: `Verdict ${cp.verdict} not in ${validVerdicts.join(",")}`, recovery: "Quality gate must pass" };
        return { ok: true };
    }],

    // Stage 3 -> Stage 2 (rework cycle)
    ["STAGE_3->STAGE_2", (state, cp) => {
        if (state.quality_cycles >= 2) return { ok: false, error: "Quality cycle limit reached (2)", recovery: "Escalate to user" };
        state.quality_cycles++;
        return { ok: true, counter_incremented: "quality_cycles" };
    }],
    ["STAGE_3->PAUSED", (state, cp) => ({ ok: true })],
]);

// Any state -> PAUSED (always allowed)
function isPauseTransition(to) { return to === "PAUSED"; }

/**
 * Validate a state transition.
 * @param {object} state - Current pipeline state (may be mutated for counter increments)
 * @param {string} toStage - Target stage
 * @param {object|null} checkpoint - Latest checkpoint for current story
 * @returns {{ok: boolean, error?: string, recovery?: string, counter_incremented?: string}}
 */
export function validateTransition(state, toStage, checkpoint) {
    if (isPauseTransition(toStage) && !TRANSITIONS.has(`${state.stage}->${toStage}`)) {
        return { ok: true };
    }

    const key = `${state.stage}->${toStage}`;
    const guard = TRANSITIONS.get(key);
    if (!guard) {
        return { ok: false, error: `Invalid transition: ${key}`, recovery: "Check pipeline_states.md for valid transitions" };
    }
    return guard(state, checkpoint);
}

/**
 * Determine target stage from kanban status (QUEUED routing).
 * @param {string} kanbanStatus - Story status from kanban
 * @param {boolean} hasTasks - Whether story has tasks
 * @returns {string} Target stage
 */
export function determineTargetStage(kanbanStatus, hasTasks) {
    const status = kanbanStatus.toLowerCase().trim();
    if ((status === "backlog") && !hasTasks) return "STAGE_0";
    if ((status === "backlog") && hasTasks) return "STAGE_1";
    if (["todo", "in progress", "to rework"].includes(status)) return "STAGE_2";
    if (status === "to review") return "STAGE_3";
    if (["done", "postponed", "canceled"].includes(status)) return null; // skip
    return "STAGE_0"; // fallback
}
