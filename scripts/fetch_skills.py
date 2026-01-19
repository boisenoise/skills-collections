#!/usr/bin/env python3
"""
Fetch and organize Claude skills from multiple repositories.

This script:
1. Clones/updates skill repositories
2. Copies skills to a flat structure with source prefixes
3. Validates SKILL.md format
4. Generates a catalog of all skills
5. Discovers new skills on GitHub (optional)
"""

import json
import os
import shutil
import subprocess
import sys
import re
import yaml
from pathlib import Path
from datetime import datetime
from typing import Optional
import argparse

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
SKILLS_DIR = REPO_ROOT / "skills"
CACHE_DIR = REPO_ROOT / ".cache"
SOURCES_FILE = SCRIPT_DIR / "sources.json"
CATALOG_FILE = REPO_ROOT / "CATALOG.md"
LICENSES_FILE = REPO_ROOT / "THIRD_PARTY_LICENSES.md"


def load_sources() -> dict:
    """Load sources configuration."""
    with open(SOURCES_FILE) as f:
        return json.load(f)


def run_cmd(cmd: list[str], cwd: Optional[Path] = None) -> tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)."""
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def clone_or_update_repo(url: str, name: str, branch: str = "main") -> Path:
    """Clone or update a repository in the cache directory."""
    repo_dir = CACHE_DIR / name.replace("/", "_")
    
    if repo_dir.exists():
        print(f"  Updating {name}...")
        run_cmd(["git", "fetch", "origin"], cwd=repo_dir)
        run_cmd(["git", "reset", "--hard", f"origin/{branch}"], cwd=repo_dir)
    else:
        print(f"  Cloning {name}...")
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        run_cmd(["git", "clone", "--depth", "1", "-b", branch, url, str(repo_dir)])
    
    return repo_dir


def parse_skill_frontmatter(skill_md_path: Path) -> Optional[dict]:
    """Parse YAML frontmatter from a SKILL.md file."""
    try:
        content = skill_md_path.read_text(encoding="utf-8")
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                return yaml.safe_load(parts[1])
    except Exception as e:
        print(f"    Warning: Could not parse {skill_md_path}: {e}")
    return None


def validate_skill(skill_dir: Path) -> bool:
    """Validate that a skill directory has required files and format."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return False
    
    frontmatter = parse_skill_frontmatter(skill_md)
    if not frontmatter:
        return False
    
    # Must have name and description
    if "name" not in frontmatter or "description" not in frontmatter:
        return False
    
    return True


def copy_skill(src_dir: Path, dest_name: str, source_info: dict) -> Optional[dict]:
    """Copy a skill directory to the skills folder with proper naming."""
    dest_dir = SKILLS_DIR / dest_name
    
    # Remove existing skill if present
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    
    # Copy the skill
    shutil.copytree(src_dir, dest_dir)
    
    # Parse and return skill metadata
    skill_md = dest_dir / "SKILL.md"
    frontmatter = parse_skill_frontmatter(skill_md)
    
    if frontmatter:
        return {
            "name": dest_name,
            "original_name": frontmatter.get("name", src_dir.name),
            "description": frontmatter.get("description", ""),
            "source": source_info["name"],
            "source_url": source_info["url"],
            "license": frontmatter.get("license", source_info.get("license", "Unknown")),
        }
    return None


def process_source(source: dict) -> list[dict]:
    """Process a single source repository and copy its skills."""
    print(f"\nProcessing {source['name']}...")
    
    repo_dir = clone_or_update_repo(
        source["url"], 
        source["name"],
        source.get("branch", "main")
    )
    
    # Support multiple skills paths
    skills_paths = source.get("skills_paths", [source.get("skills_path", "skills")])
    if isinstance(skills_paths, str):
        skills_paths = [skills_paths]
    
    skills_metadata = []
    exclude_list = source.get("exclude", [])
    prefix = source.get("prefix", "")
    processed_skills = set()  # Track to avoid duplicates
    
    for skills_path_str in skills_paths:
        if skills_path_str == ".":
            skills_path = repo_dir
        else:
            skills_path = repo_dir / skills_path_str
        
        if not skills_path.exists():
            print(f"  Skills path not found: {skills_path_str}")
            continue
        
        print(f"  Scanning: {skills_path_str}/")
        
        for skill_dir in skills_path.iterdir():
            if not skill_dir.is_dir():
                continue
            
            skill_name = skill_dir.name
            
            # Skip if already processed
            if skill_name in processed_skills:
                continue
            
            # Skip excluded skills
            if skill_name in exclude_list:
                print(f"    Skipping excluded: {skill_name}")
                continue
            
            # Skip hidden directories
            if skill_name.startswith("."):
                continue
            
            # Validate skill
            if not validate_skill(skill_dir):
                # Check if this directory contains skills (nested structure)
                nested_skills = [d for d in skill_dir.iterdir() if d.is_dir() and validate_skill(d)]
                if nested_skills:
                    for nested_dir in nested_skills:
                        nested_name = nested_dir.name
                        if nested_name in processed_skills or nested_name in exclude_list:
                            continue
                        
                        dest_name = f"{prefix}-{nested_name}" if prefix else nested_name
                        print(f"    Copying (nested): {skill_name}/{nested_name} -> {dest_name}")
                        metadata = copy_skill(nested_dir, dest_name, source)
                        if metadata:
                            skills_metadata.append(metadata)
                            processed_skills.add(nested_name)
                continue
            
            # Create destination name with prefix
            dest_name = f"{prefix}-{skill_name}" if prefix else skill_name
            
            print(f"    Copying: {skill_name} -> {dest_name}")
            metadata = copy_skill(skill_dir, dest_name, source)
            
            if metadata:
                skills_metadata.append(metadata)
                processed_skills.add(skill_name)
    
    return skills_metadata


def discover_new_skills(config: dict, github_token: Optional[str] = None) -> list[dict]:
    """Search GitHub for new skill repositories."""
    if not config.get("enabled", False):
        return []
    
    print("\nDiscovering new skills on GitHub...")
    
    # This would use the GitHub API to search for new skills
    # For now, return empty list - implement with GitHub API later
    discovered = []
    
    # TODO: Implement GitHub search using:
    # - config["search_queries"]
    # - config["min_stars"]
    # - config["allowed_licenses"]
    
    return discovered


def generate_catalog(all_skills: list[dict]):
    """Generate the CATALOG.md file with all skills listed."""
    content = f"""# Skills Catalog

*Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M UTC")}*

Total skills: **{len(all_skills)}**

## Skills by Source

"""
    
    # Group by source
    by_source = {}
    for skill in all_skills:
        source = skill.get("source", "Unknown")
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(skill)
    
    for source, skills in sorted(by_source.items()):
        content += f"### {source}\n\n"
        content += "| Skill | Description |\n"
        content += "|-------|-------------|\n"
        
        for skill in sorted(skills, key=lambda x: x["name"]):
            desc = skill.get("description", "")[:100]
            if len(skill.get("description", "")) > 100:
                desc += "..."
            content += f"| `{skill['name']}` | {desc} |\n"
        
        content += "\n"
    
    content += """## Installation

Copy individual skills:
```bash
cp -r skills/SKILL_NAME ~/.claude/skills/
```

Copy all skills:
```bash
cp -r skills/* ~/.claude/skills/
```
"""
    
    CATALOG_FILE.write_text(content)
    print(f"\nGenerated {CATALOG_FILE}")


def generate_licenses(all_skills: list[dict], sources: list[dict]):
    """Generate the THIRD_PARTY_LICENSES.md file."""
    content = f"""# Third-Party Licenses

This repository aggregates skills from multiple sources. Each skill retains its original license.

*Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M UTC")}*

## Source Repositories

"""
    
    for source in sources:
        content += f"""### {source['name']}

- **URL:** {source['url']}
- **License:** {source.get('license', 'See repository')}
- **Description:** {source.get('description', '')}

"""
    
    content += """## License Summary

| License | Count |
|---------|-------|
"""
    
    license_counts = {}
    for skill in all_skills:
        lic = skill.get("license", "Unknown")
        license_counts[lic] = license_counts.get(lic, 0) + 1
    
    for lic, count in sorted(license_counts.items()):
        content += f"| {lic} | {count} |\n"
    
    content += """

## Full License Texts

### MIT License

```
MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### Apache License 2.0

See: https://www.apache.org/licenses/LICENSE-2.0

"""
    
    LICENSES_FILE.write_text(content)
    print(f"Generated {LICENSES_FILE}")


def main():
    parser = argparse.ArgumentParser(description="Fetch and organize Claude skills")
    parser.add_argument("--discover", action="store_true", help="Enable GitHub discovery")
    parser.add_argument("--clean", action="store_true", help="Clean skills directory first")
    parser.add_argument("--source", type=str, help="Process only this source")
    args = parser.parse_args()
    
    print("=" * 60)
    print("Claude Skills Collection - Fetch Script")
    print("=" * 60)
    
    # Load configuration
    config = load_sources()
    sources = config["sources"]
    
    # Clean skills directory if requested
    if args.clean and SKILLS_DIR.exists():
        print("\nCleaning skills directory...")
        shutil.rmtree(SKILLS_DIR)
    
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Process sources
    all_skills = []
    
    for source in sources:
        if args.source and source["name"] != args.source:
            continue
        
        try:
            skills = process_source(source)
            all_skills.extend(skills)
        except Exception as e:
            print(f"  Error processing {source['name']}: {e}")
    
    # Discover new skills
    if args.discover:
        discovered = discover_new_skills(config.get("discovery", {}))
        all_skills.extend(discovered)
    
    # Generate documentation
    print("\n" + "=" * 60)
    print("Generating documentation...")
    print("=" * 60)
    
    generate_catalog(all_skills)
    generate_licenses(all_skills, sources)
    
    # Summary
    print("\n" + "=" * 60)
    print(f"Done! Collected {len(all_skills)} skills from {len(sources)} sources")
    print("=" * 60)
    
    # Save metadata for GitHub Action
    metadata_file = REPO_ROOT / ".skill_metadata.json"
    with open(metadata_file, "w") as f:
        json.dump({
            "last_updated": datetime.now().isoformat(),
            "skill_count": len(all_skills),
            "sources_processed": len(sources),
            "skills": all_skills
        }, f, indent=2)


if __name__ == "__main__":
    main()
