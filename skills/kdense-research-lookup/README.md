# Research Lookup Skill

Real-time research information lookup that routes each query to the backend best suited to it, then saves the result to `sources/` so every citation stays traceable.

`SKILL.md` is the authoritative reference for how the skill behaves. This README is a quick human-facing overview.

## Backends

| Backend | Speed | Best for | Key |
|---------|-------|----------|-----|
| `parallel-cli search` (default) | 2–10 s | General research, market data, technical lookups, fact-checking | `PARALLEL_API_KEY` |
| Perplexity `sonar-pro-search` | 5–15 s | Scholarly paper searches (papers, DOIs, systematic reviews) | `OPENROUTER_API_KEY` |
| Parallel Chat API (`core`) | 60 s–5 min | Deep, exhaustive multi-source synthesis (on explicit request) | `PARALLEL_API_KEY` |

> **Two different "Parallel" things:** `parallel-cli search` is the fast web-search CLI (the default). The Parallel Chat API `core` model is a separate, slow deep-research endpoint reached only through `scripts/research_lookup.py`. `--force-backend parallel` selects the *slow* Chat API.

## Setup

```bash
# Install the primary dependency
curl -fsSL https://parallel.ai/install.sh | bash
# or: uv tool install "parallel-web-tools[cli]"

# Authenticate / set keys
parallel-cli auth                    # or: export PARALLEL_API_KEY="..."
export OPENROUTER_API_KEY="..."      # optional, for Perplexity academic search
```

## Usage

```bash
# Default: fast web search (save results to sources/)
mkdir -p sources
parallel-cli search "recent advances in CRISPR gene editing 2025" \
  -q "CRISPR" -q "gene editing" --json --max-results 10 \
  -o sources/research_crispr.json

# Academic paper search (Perplexity)
python scripts/research_lookup.py "find papers on CRISPR off-target effects" \
  --force-backend perplexity -o sources/papers_crispr.md

# Deep research (Parallel Chat API — slow, on request only)
python scripts/research_lookup.py "state of quantum error correction" \
  --force-backend parallel -o sources/research_qec.md

# Auto-route between the two API backends
python scripts/research_lookup.py "your query" -o sources/research_topic.md
```

`scripts/research_lookup.py` is also imported by the `market-research-reports` skill, so its CLI stays stable.

## What you get back

- **`parallel-cli search`** — JSON with `title`, `url`, `publish_date`, and content `excerpts` per result.
- **Perplexity / Chat API** — a markdown report plus a Sources list and Additional References (DOIs, academic URLs). Add `--json` to `research_lookup.py` for structured citation objects.

## Notes

- Save every result to `sources/` — it makes the research reproducible, recoverable after context compaction, and cheap to reuse. Check `sources/` before making a new call.
- When a query is about the literature, prefer highly-cited papers from top-tier venues; note citation counts and venues in-line where known. See the quality guidance in `SKILL.md`.
- Query text is sent to `api.parallel.ai` and, for academic searches, to `openrouter.ai`.

## Related skills

- **`parallel-web`** — the full parallel-cli toolkit (search, extract, enrichment, deep research).
- **`citation-management`** — Google Scholar / PubMed search and DOI→BibTeX.
- **`scientific-schematics`** — publication-quality diagrams for research documents.
