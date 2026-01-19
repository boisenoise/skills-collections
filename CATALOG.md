# Skills Catalog

*This catalog is automatically generated after running `./scripts/setup.sh`*

## How to Populate This Catalog

```bash
# Run the setup script to fetch all skills
./scripts/setup.sh

# Or manually run the fetch script
python scripts/fetch_skills.py --clean
```

## Expected Skills After Setup

Based on configured sources, you can expect skills from:

### anthropics/skills (Apache 2.0)
- `anthropic-skill-creator` - Guide for creating skills
- `anthropic-brand-guidelines` - Anthropic brand guidelines  
- `anthropic-internal-comms` - Internal communications
- `anthropic-algorithmic-art` - Create algorithmic art
- `anthropic-canvas-design` - Canvas-based designs
- `anthropic-webapp-testing` - Test web applications with Playwright
- `anthropic-mcp-builder` - Build MCP servers
- And more...

### obra/superpowers (MIT)
- `superpowers-test-driven-development` - TDD workflow
- `superpowers-systematic-debugging` - Debugging methodology
- `superpowers-brainstorming` - Design refinement
- `superpowers-writing-plans` - Implementation planning
- `superpowers-verification-before-completion` - Quality checks
- `superpowers-using-superpowers` - Meta skill for using other skills
- And more (20+ skills)...

### vercel-labs/agent-skills (MIT)
- `vercel-react-best-practices` - React/Next.js optimization (45+ rules)
- `vercel-web-design-guidelines` - Web design standards (100+ rules)
- `vercel-deploy-claimable` - Deploy to Vercel instantly

### K-Dense-AI/claude-scientific-skills (MIT)
140+ scientific skills across domains:
- Bioinformatics & Genomics
- Chemistry & Drug Discovery
- Clinical & Medical Research
- Machine Learning & Data Science
- Physics & Materials Science
- And more...

### alirezarezvani/claude-skills (MIT)
- `rezvani-ceo-advisor` - Executive strategy guidance
- `rezvani-content-creator` - Content creation workflows
- `rezvani-compliance-*` - Various compliance skills (EU MDR, FDA, QMS, etc.)
- And more (48 skills)...

### sickn33/antigravity-awesome-skills (MIT)
130+ universal agentic skills compatible with multiple AI assistants

## Installation

After running setup:

```bash
# Copy all skills
cp -r skills/* ~/.claude/skills/

# Or copy specific skills
cp -r skills/superpowers-tdd ~/.claude/skills/
cp -r skills/vercel-react-best-practices ~/.claude/skills/
```

## Updating

```bash
git pull
./scripts/setup.sh
cp -r skills/* ~/.claude/skills/
```
