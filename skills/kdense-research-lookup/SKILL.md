---
name: research-lookup
description: 'Look up current research and scientific information across three backends: fast web search via parallel-cli (default), the Parallel Chat API for deep multi-source synthesis, and Perplexity sonar-pro-search for scholarly paper searches. Automatically routes each query to the best backend and saves every result to sources/ for reproducible citation. Use this whenever you need to find papers, gather statistics or market data, verify a scientific claim, collect citations, or research any topic for scientific/technical writing — even if the user does not say "research" explicitly. Note: query text is sent to api.parallel.ai (PARALLEL_API_KEY) and, for academic searches, to openrouter.ai (OPENROUTER_API_KEY).'
allowed-tools: Read Write Edit Bash
license: MIT license
compatibility: parallel-cli required (primary); PARALLEL_API_KEY and OPENROUTER_API_KEY optional for deep/academic backends
required_environment_variables: [{"name": "PARALLEL_API_KEY", "prompt": "Parallel web search API key.", "required_for": "optional features"}, {"name": "OPENROUTER_API_KEY", "prompt": "OpenRouter API key (fallback model access).", "required_for": "optional features"}]
metadata: {"version": "1.2", "skill-author": "K-Dense Inc.", "openclaw": {"primaryEnv": "PARALLEL_API_KEY", "envVars": [{"name": "PARALLEL_API_KEY", "required": false, "description": "Parallel web search API key."}, {"name": "OPENROUTER_API_KEY", "required": false, "description": "OpenRouter API key (fallback model access)."}]}}
---

# Research Information Lookup

Real-time research lookup that routes each query to the backend best suited to it, then saves the result so every citation can be traced later.

## The three backends

| Backend | Speed | Use it for | How to call |
|---------|-------|-----------|-------------|
| **`parallel-cli search`** (default) | 2–10 s | Almost everything: general research, market/industry data, technical lookups, current events, fact-checking, comparisons | `parallel-cli search` (direct) |
| **Perplexity sonar-pro-search** | 5–15 s | Scholarly paper searches where peer-reviewed database coverage matters (find papers, DOIs, systematic reviews) | `scripts/research_lookup.py --force-backend perplexity` |
| **Parallel Chat API** (`core` model) | 60 s–5 min | Deep, exhaustive multi-source synthesis — only when the user explicitly asks for "deep research" | `scripts/research_lookup.py --force-backend parallel` |

> **Naming caution — there are two different "Parallel" things.**
> `parallel-cli search` is the fast web-search CLI (the default). The "Parallel Chat API (`core` model)" is a separate, slow deep-research endpoint reached only through `research_lookup.py`. `--force-backend parallel` selects the *slow* Chat API, **not** the fast CLI. Don't conflate them.

Default to `parallel-cli search`. It is fast and cheap and handles the large majority of research needs. Reach for the other two only when the query specifically calls for scholarly paper coverage (Perplexity) or exhaustive synthesis (Chat API).

## When to use this skill

- **Current research**: latest studies, findings, and developments
- **Literature verification**: check facts, statistics, or claims against current sources
- **Background research**: gather context and evidence for scientific writing
- **Citations**: find relevant papers and studies to cite
- **Technical documentation**: specifications, protocols, methodologies
- **Market/industry data**: current statistics, trends, competitive intelligence

---

## Backend selection

```
Query arrives
    |
    +-- Asks for papers/DOIs/scholarly review? ("find papers", "cite", "systematic review", ...)
    |       --> Perplexity sonar-pro-search   (scripts/research_lookup.py --force-backend perplexity)
    |
    +-- User explicitly wants deep/exhaustive/comprehensive research?
    |       --> Parallel Chat API (core)       (scripts/research_lookup.py --force-backend parallel)
    |
    +-- Everything else (the common case)
            --> parallel-cli search            (fast, default)
```

`research_lookup.py` applies this same logic automatically when you give it a bare query (no `--force-backend`): it routes academic-keyword queries to Perplexity and everything else to the Parallel Chat API. Use it that way when you want auto-routing between the two API backends; use `parallel-cli search` directly when you want the fast default.

**Academic keywords that signal a paper search:** `find papers`, `research papers on`, `published studies`, `cite`, `citation`, `doi`, `pubmed`, `pmid`, `peer-reviewed`, `journal article`, `scholarly`, `arxiv`, `preprint`, `systematic review`, `meta-analysis`, `literature search`, `foundational/seminal/landmark papers`, `highly cited`.

---

## Default backend: `parallel-cli search`

Fast, cost-effective web search with optional academic source prioritization. For scientific or technical topics, run **two** searches — one restricted to scholarly domains, one general — and merge them, leading with the academic sources. This surfaces peer-reviewed work that a general search alone tends to bury. For non-scientific queries, a single general search is enough.

```bash
mkdir -p sources   # so -o can write here (parallel-cli won't create the dir)

# 1. Academic-focused search (scholarly domains only)
parallel-cli search "your research query" -q "keyword1" -q "keyword2" \
  --json --max-results 10 --excerpt-max-chars-total 27000 \
  --include-domains "scholar.google.com,arxiv.org,pubmed.ncbi.nlm.nih.gov,semanticscholar.org,biorxiv.org,medrxiv.org,ncbi.nlm.nih.gov,nature.com,science.org,ieee.org,acm.org,springer.com,wiley.com,cell.com,pnas.org,nih.gov" \
  -o sources/research_<topic>-academic.json

# 2. General search (catches non-academic sources)
parallel-cli search "your research query" -q "keyword1" -q "keyword2" \
  --json --max-results 10 --excerpt-max-chars-total 27000 \
  -o sources/research_<topic>-general.json
```

Useful flags:
- `--after-date YYYY-MM-DD` — restrict to recent results for time-sensitive queries
- `--include-domains a.com,b.com` — limit to specific sources
- `--max-results N` — how many results to return
- `-o path.json` — save results (always do this; see [Saving results](#saving-results))

Saved JSON contains the full result objects — `title`, `url`, `publish_date`, and content `excerpts` — everything needed to cite and to re-read later without re-querying.

To pull the full text of a specific result, extract it:

```bash
parallel-cli extract "https://example.com/paper" --json
```

---

## Academic paper search: Perplexity sonar-pro-search

Use when the query specifically asks for papers, citations, or DOIs. Perplexity searches in academic mode, prioritizing peer-reviewed sources, and returns a summary plus complete citations.

```bash
python scripts/research_lookup.py "Find papers on CRISPR off-target effects in clinical trials" \
  --force-backend perplexity \
  -o sources/papers_<topic>.md
```

Returns: a summary of key findings, 5–8 high-quality citations (authors, title, journal, year, DOI when available), citation-count and venue signals where known, and research gaps. Requires `OPENROUTER_API_KEY`.

Add `--json` if you need the structured citation objects (`url`, `title`, `date`, `snippet`, `doi`, `type`) for programmatic use such as BibTeX generation.

---

## Deep research: Parallel Chat API (`core` model)

Use **only** when the user explicitly asks for deep, exhaustive, or comprehensive research. It is much slower (60 s–5 min) and more expensive than `parallel-cli search` — never make it the default.

```bash
python scripts/research_lookup.py "current state of quantum computing error correction" \
  --force-backend parallel \
  -o sources/research_<topic>.md
```

Returns a comprehensive markdown report with inline citations plus a Sources list (title, URL) and Additional References (DOIs, academic URLs). Requires `PARALLEL_API_KEY`.

---

## Prioritizing high-quality papers

When a query is about the literature, favor influential, well-established work over obscure publications — a reader trusts a claim backed by a landmark paper in a top venue far more than one backed by an unvetted source. Use citation counts and venue as the two main quality signals.

### Citation thresholds (rough guide)

| Paper age | Citations | Classification |
|-----------|-----------|----------------|
| 0–3 years | 20+ | Noteworthy |
| 0–3 years | 100+ | Highly influential |
| 3–7 years | 100+ | Significant |
| 3–7 years | 500+ | Landmark |
| 7+ years | 500+ | Seminal |
| 7+ years | 1000+ | Foundational |

### Venue tiers (prefer higher)

- **Tier 1 — premier:** Nature, Science, Cell, PNAS; NEJM, Lancet, JAMA, BMJ; Nature Medicine/Biotechnology/Methods; NeurIPS, ICML, ICLR, ACL, CVPR
- **Tier 2 — high-impact specialized:** journals with impact factor > 10; top subfield conferences (EMNLP, NAACL, ECCV, MICCAI)
- **Tier 3 — respected specialized:** journals with impact factor 5–10

These are heuristics, not gates — a directly relevant Tier-3 paper beats a tangential Tier-1 one. When you have the numbers, note them in-line (e.g. "cited 800+ times, Nature 2021") so the reader can judge the evidence themselves.

---

## Saving results

Save every research result to the project's `sources/` folder. Research results are expensive to obtain and are the evidence base for every downstream citation, so keeping them makes the work reproducible and cheap to revisit. Concretely, saved results let you:

- **Trace** any claim back to the raw source that supports it (and let a reviewer do the same).
- **Recover** context after compaction — re-read a saved file instead of re-querying.
- **Reuse** one lookup across multiple sections without paying for it again.
- **Skip** redundant calls — check `sources/` before querying (`ls sources/`); if a prior result already covers the topic, read it instead.

Use the `-o` flag on every call. Preserve all citations, URLs, and DOIs in the saved file.

| Backend | Save target | Filename pattern |
|---------|-------------|------------------|
| `parallel-cli search` (default) | `sources/research_<topic>.json` | `research_<topic>-academic.json`, `research_<topic>-general.json` |
| Perplexity (academic) | `sources/papers_<topic>.md` | `papers_<topic>.md` (add `--json` for structured citations) |
| Parallel Chat API (deep) | `sources/research_<topic>.md` | `research_<topic>.md` |

`research_lookup.py` creates the `sources/` directory automatically. When calling `parallel-cli` directly, run `mkdir -p sources` first — it won't create the directory for you.

When you save a result, log a one-line note so the audit trail is legible, e.g.:

```
[14:30:00] SAVED: sources/research_crispr_advances-academic.json (10 results)
[14:30:05] SAVED: sources/papers_transformer_attention.md (6 papers)
```

---

## Setup

`parallel-cli` is the primary dependency. If it isn't installed:

```bash
curl -fsSL https://parallel.ai/install.sh | bash
# or: uv tool install "parallel-web-tools[cli]"

parallel-cli auth            # or: export PARALLEL_API_KEY="..."
```

Environment variables:

```bash
export PARALLEL_API_KEY="..."     # parallel-cli search AND the Parallel Chat API (deep research)
export OPENROUTER_API_KEY="..."   # Perplexity academic search (optional)
```

---

## Command reference

```bash
# Fast web search (DEFAULT) — always save to sources/
parallel-cli search "query" -q "kw1" -q "kw2" \
  --json --max-results 10 --excerpt-max-chars-total 27000 \
  -o sources/research_<topic>.json

# Academic-focused variant (add scholarly domains)
parallel-cli search "query" -q "kw1" \
  --json --max-results 10 --excerpt-max-chars-total 27000 \
  --include-domains "arxiv.org,pubmed.ncbi.nlm.nih.gov,nature.com,science.org,cell.com,pnas.org,nih.gov" \
  -o sources/research_<topic>-academic.json

# Time-sensitive
parallel-cli search "query" -q "kw" --json --max-results 10 --after-date 2024-01-01 \
  -o sources/research_<topic>.json

# Extract full text from a URL
parallel-cli extract "https://example.com/paper" --json

# Academic paper search (Perplexity)
python scripts/research_lookup.py "find papers on <topic>" --force-backend perplexity \
  -o sources/papers_<topic>.md

# Deep research (Parallel Chat API, slow/expensive — on request only)
python scripts/research_lookup.py "deep dive on <topic>" --force-backend parallel \
  -o sources/research_<topic>.md

# Auto-route between the two API backends (academic->Perplexity, else->Chat API)
python scripts/research_lookup.py "query" -o sources/research_<topic>.md

# Batch several queries through the API backends
python scripts/research_lookup.py --batch "query 1" "query 2" -o sources/batch_<topic>.md
```

---

## Related skills

- **`parallel-web`** — the full parallel-cli toolkit (search, extract, data enrichment, deep research) with more options than the essentials shown here. Reach for it for enrichment jobs or advanced extraction.
- **`citation-management`** — Google Scholar / PubMed search and DOI→BibTeX conversion. Use it to turn the DOIs and URLs found here into formatted references.
- **`scientific-schematics`** — generate publication-quality diagrams. If a research document would be clearer with a figure, hand off to this skill rather than embedding image-generation here.

---

## Errors and limitations

- **`parallel-cli` not found** — install it (see [Setup](#setup)).
- **Missing API key** — `parallel-cli search` and the Chat API need `PARALLEL_API_KEY`; Perplexity needs `OPENROUTER_API_KEY`. `research_lookup.py` reports clearly if none is set and, when auto-routing, falls back to whichever backend has a key.
- **Deep research is slow** — the Chat API `core` model can take up to 5 minutes; expect it and don't use it for quick lookups.
- **Paywalls / restricted data** — none of the backends can read proprietary databases or full text behind paywalls.
- **Weak results** — rephrase with more specific terms or a date range, or try a different backend before giving up.
