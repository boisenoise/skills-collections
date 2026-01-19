#!/bin/bash
# Setup script for Claude Skills Collection
# This script fetches all skills and installs them to your ~/.claude/skills/ directory

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

echo "============================================================"
echo "Claude Skills Collection - Setup"
echo "============================================================"

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not found"
    exit 1
fi

# Check for git
if ! command -v git &> /dev/null; then
    echo "Error: Git is required but not found"
    exit 1
fi

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip3 install pyyaml --quiet 2>/dev/null || pip install pyyaml --quiet

# Run fetch script
echo ""
echo "Fetching skills from all sources..."
python3 "$SCRIPT_DIR/fetch_skills.py" --clean

# Count skills
SKILL_COUNT=$(ls -d "$REPO_ROOT/skills"/*/ 2>/dev/null | wc -l)

echo ""
echo "============================================================"
echo "Setup complete! $SKILL_COUNT skills collected."
echo "============================================================"
echo ""
echo "Next steps:"
echo ""
echo "  1. Review the skills in: $REPO_ROOT/skills/"
echo ""
echo "  2. Copy all skills to your Claude configuration:"
echo "     cp -r $REPO_ROOT/skills/* ~/.claude/skills/"
echo ""
echo "  3. Or copy specific skills:"
echo "     cp -r $REPO_ROOT/skills/superpowers-tdd ~/.claude/skills/"
echo ""
echo "  4. See CATALOG.md for the full list of available skills"
echo ""
