# Claude Skills Collection

A comprehensive, auto-updating collection of open-source Claude/AI agent skills compiled from various community repositories. All skills are organized in a flat structure for easy installation to your `~/.claude/skills/` directory.

## 🚀 Quick Start

### Option 1: One-Command Setup

```bash
git clone https://github.com/YOUR_USERNAME/claude-skills-collection.git
cd claude-skills-collection
./scripts/setup.sh
```

This will:
- Fetch all skills from 9+ source repositories
- Organize them in a flat structure with source prefixes
- Generate a catalog of all available skills

### Option 2: Manual Setup

```bash
# Clone this repo
git clone https://github.com/YOUR_USERNAME/claude-skills-collection.git
cd claude-skills-collection

# Install dependencies
pip install pyyaml

# Fetch skills
python scripts/fetch_skills.py --clean

# Copy to your Claude skills folder
cp -r skills/* ~/.claude/skills/
```

### Option 3: Cherry-Pick Specific Skills

After running setup, copy only the skills you want:

```bash
# Copy specific skills
cp -r skills/superpowers-tdd ~/.claude/skills/
cp -r skills/vercel-react-best-practices ~/.claude/skills/
cp -r skills/anthropic-skill-creator ~/.claude/skills/
```

## 📁 Repository Structure

```
claude-skills-collection/
├── skills/                    # All collected skills (flat structure)
│   ├── anthropic-*/          # Official Anthropic skills
│   ├── superpowers-*/        # obra/superpowers ecosystem
│   ├── vercel-*/             # Vercel Labs skills
│   ├── kdense-*/             # K-Dense scientific skills
│   └── ...
├── scripts/
│   ├── fetch_skills.py       # Main skill fetcher
│   ├── discover_skills.py    # GitHub skill discovery
│   ├── sources.json          # Source repository configuration
│   └── setup.sh              # Quick setup script
├── .github/workflows/
│   └── update-skills.yml     # Daily auto-update action
├── CATALOG.md                # Generated skill catalog
└── THIRD_PARTY_LICENSES.md   # License attribution
```

## 📚 Included Sources

| Source | License | Description |
|--------|---------|-------------|
| [anthropics/skills](https://github.com/anthropics/skills) | Apache 2.0 | Official Anthropic skills (creative, technical, enterprise) |
| [obra/superpowers](https://github.com/obra/superpowers) | MIT | TDD, debugging, collaboration - 20+ battle-tested skills |
| [obra/superpowers-skills](https://github.com/obra/superpowers-skills) | MIT | Community-contributed skills |
| [obra/superpowers-lab](https://github.com/obra/superpowers-lab) | MIT | Experimental skills under development |
| [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) | MIT | React/Next.js best practices, Vercel deploy |
| [K-Dense-AI/claude-scientific-skills](https://github.com/K-Dense-AI/claude-scientific-skills) | MIT | 140+ scientific research skills |
| [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills) | MIT | 48 professional skills (CEO advisor, compliance, etc.) |
| [sickn33/antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills) | MIT | 130+ universal agentic skills |

## ⚠️ Excluded Content

The following are **NOT included** due to licensing restrictions:
- `anthropics/skills/docx` - Proprietary (source-available, not open source)
- `anthropics/skills/pdf` - Proprietary
- `anthropics/skills/pptx` - Proprietary
- `anthropics/skills/xlsx` - Proprietary

These document creation skills are available directly in Claude.ai for paid plans.

## 🔄 Auto-Updates

This repository automatically updates daily via GitHub Actions:

- **Daily (6 AM UTC):** Fetches latest skills from all configured sources
- **Weekly (Sundays):** Runs GitHub discovery to find new skill repositories
- **Manual:** Trigger anytime via Actions tab

### Keeping Your Local Copy Updated

```bash
cd claude-skills-collection
git pull
./scripts/setup.sh
cp -r skills/* ~/.claude/skills/
```

## 🔍 Skill Discovery

The discovery script searches GitHub for new skill repositories:

```bash
# Requires GITHUB_TOKEN for API access
export GITHUB_TOKEN=your_token
python scripts/discover_skills.py
```

Found repositories are saved to `scripts/discovered.json` for manual review before being added to sources.

## 🛠️ Adding New Sources

1. Edit `scripts/sources.json`
2. Add your source:
```json
{
  "name": "username/repo",
  "url": "https://github.com/username/repo",
  "branch": "main",
  "skills_paths": ["skills"],
  "prefix": "myprefix",
  "license": "MIT",
  "exclude": [],
  "description": "Description of the skills"
}
```
3. Run `python scripts/fetch_skills.py`
4. Submit a PR!

## 🏷️ Skill Naming Convention

Skills are prefixed with their source for easy identification:
- `anthropic-*` - Official Anthropic skills
- `superpowers-*` - obra/superpowers core skills
- `superpowers-community-*` - Community superpowers skills
- `superpowers-lab-*` - Experimental superpowers skills
- `vercel-*` - Vercel Labs skills
- `kdense-*` - K-Dense scientific skills
- `rezvani-*` - alirezarezvani professional skills
- `antigravity-*` - Antigravity collection skills

## 📜 License

This repository aggregates skills under their original licenses:
- Each skill retains its original license (MIT, Apache 2.0, etc.)
- License info is in each SKILL.md frontmatter
- See `THIRD_PARTY_LICENSES.md` for complete attribution

## ⚠️ Disclaimer

These skills are provided as-is for convenience. Always review skills before using in production:

- Skills can execute code in Claude's environment
- Only use skills from trusted sources
- Test in a safe environment first
- Some skills may have external dependencies

## 🤝 Contributing

Found a great open-source skill repository? 

1. Open an issue with the repository URL
2. Or submit a PR adding it to `scripts/sources.json`

Requirements for new sources:
- Must have an open-source license (MIT, Apache 2.0, BSD, etc.)
- Must follow the SKILL.md format
- Should have at least 5 GitHub stars
- Should be actively maintained
