#!/usr/bin/env node

import { execFileSync } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const cliPath = join(__dirname, "..", "cli.mjs");
const projectRoot = mkdtempSync(join(tmpdir(), "pipeline-runtime-"));

function run(args) {
    return JSON.parse(execFileSync("node", [cliPath, ...args], {
        cwd: projectRoot,
        encoding: "utf8",
    }));
}

try {
    const started = run(["start", "--story", "PROJ-123", "--title", "Story title"]);
    if (!started.ok) {
        throw new Error("Failed to start pipeline runtime");
    }

    run(["advance", "--story", "PROJ-123", "--to", "STAGE_0"]);
    run(["checkpoint", "--story", "PROJ-123", "--stage", "0", "--plan-score", "4", "--tasks-remaining", "[]", "--last-action", "plan complete"]);
    run(["advance", "--story", "PROJ-123", "--to", "STAGE_1"]);
    run(["checkpoint", "--story", "PROJ-123", "--stage", "1", "--verdict", "GO", "--readiness", "8", "--last-action", "validation complete"]);
    run(["advance", "--story", "PROJ-123", "--to", "STAGE_2"]);
    run(["checkpoint", "--story", "PROJ-123", "--stage", "2", "--tasks-completed", "[]", "--git-stats", "{}", "--last-action", "execution complete"]);
    run(["advance", "--story", "PROJ-123", "--to", "STAGE_3"]);
    run(["checkpoint", "--story", "PROJ-123", "--stage", "3", "--verdict", "PASS", "--quality-score", "90", "--last-action", "gate complete"]);
    const completed = run(["complete", "--story", "PROJ-123"]);

    if (!completed.ok || completed.state.phase !== "DONE") {
        throw new Error("Pipeline runtime did not complete");
    }

    process.stdout.write("pipeline-runtime smoke passed\n");
} finally {
    rmSync(projectRoot, { recursive: true, force: true });
}
