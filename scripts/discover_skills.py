#!/usr/bin/env python3
"""
Discover new Claude skill repositories on GitHub.

Uses GitHub API to search for repositories containing SKILL.md files,
filters by license and quality, and outputs new sources to add.
"""

import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import urllib.request
import urllib.parse

SCRIPT_DIR = Path(__file__).parent
SOURCES_FILE = SCRIPT_DIR / "sources.json"
DISCOVERED_FILE = SCRIPT_DIR / "discovered.json"

GITHUB_API = "https://api.github.com"

# Rate limiting
REQUESTS_PER_MINUTE = 10  # Be conservative with unauthenticated requests


def github_request(endpoint: str, token: Optional[str] = None) -> Optional[dict]:
    """Make a request to GitHub API."""
    url = f"{GITHUB_API}{endpoint}" if endpoint.startswith("/") else endpoint
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "claude-skills-collection-discovery"
    }
    
    if token:
        headers["Authorization"] = f"token {token}"
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"  API Error: {e}")
        return None


def search_repositories(query: str, token: Optional[str] = None) -> list[dict]:
    """Search GitHub for repositories matching query."""
    encoded_query = urllib.parse.quote(query)
    endpoint = f"/search/repositories?q={encoded_query}&sort=stars&order=desc&per_page=100"
    
    result = github_request(endpoint, token)
    if result and "items" in result:
        return result["items"]
    return []


def search_code(query: str, token: Optional[str] = None) -> list[dict]:
    """Search GitHub code for files matching query."""
    encoded_query = urllib.parse.quote(query)
    endpoint = f"/search/code?q={encoded_query}&per_page=100"
    
    result = github_request(endpoint, token)
    if result and "items" in result:
        return result["items"]
    return []


def get_repo_info(owner: str, repo: str, token: Optional[str] = None) -> Optional[dict]:
    """Get detailed repository information."""
    endpoint = f"/repos/{owner}/{repo}"
    return github_request(endpoint, token)


def check_skill_structure(owner: str, repo: str, token: Optional[str] = None) -> list[str]:
    """Check if repository has proper skill structure, return list of skill paths."""
    # Check for skills directory
    endpoint = f"/repos/{owner}/{repo}/contents"
    contents = github_request(endpoint, token)
    
    if not contents:
        return []
    
    skill_paths = []
    
    for item in contents:
        if item["type"] == "dir" and item["name"] in ["skills", ".claude", "skill"]:
            # Check subdirectories for SKILL.md
            subdir_endpoint = f"/repos/{owner}/{repo}/contents/{item['path']}"
            subcontents = github_request(subdir_endpoint, token)
            
            if subcontents:
                for subitem in subcontents:
                    if subitem["type"] == "dir":
                        # Check for SKILL.md in skill folder
                        skill_md_endpoint = f"/repos/{owner}/{repo}/contents/{subitem['path']}/SKILL.md"
                        if github_request(skill_md_endpoint, token):
                            skill_paths.append(subitem["path"])
    
    # Also check root for SKILL.md (single-skill repos)
    root_skill = f"/repos/{owner}/{repo}/contents/SKILL.md"
    if github_request(root_skill, token):
        skill_paths.append(".")
    
    return skill_paths


def load_existing_sources() -> set[str]:
    """Load existing source repository names."""
    with open(SOURCES_FILE) as f:
        config = json.load(f)
    
    return {source["name"] for source in config["sources"]}


def load_discovered() -> dict:
    """Load previously discovered repositories."""
    if DISCOVERED_FILE.exists():
        with open(DISCOVERED_FILE) as f:
            return json.load(f)
    return {"repositories": [], "last_scan": None}


def save_discovered(data: dict):
    """Save discovered repositories."""
    with open(DISCOVERED_FILE, "w") as f:
        json.dump(data, f, indent=2)


def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Warning: No GITHUB_TOKEN - using unauthenticated API (limited rate)")
    
    print("=" * 60)
    print("Claude Skills Discovery")
    print("=" * 60)
    
    # Load configuration
    with open(SOURCES_FILE) as f:
        config = json.load(f)
    
    discovery_config = config.get("discovery", {})
    if not discovery_config.get("enabled", False):
        print("Discovery is disabled in sources.json")
        return
    
    existing_sources = load_existing_sources()
    discovered_data = load_discovered()
    
    search_queries = discovery_config.get("search_queries", [])
    min_stars = discovery_config.get("min_stars", 5)
    allowed_licenses = discovery_config.get("allowed_licenses", ["MIT", "Apache-2.0"])
    
    print(f"\nSearching with {len(search_queries)} queries...")
    print(f"Min stars: {min_stars}")
    print(f"Allowed licenses: {', '.join(allowed_licenses)}")
    
    found_repos = {}
    
    for query in search_queries:
        print(f"\n  Query: {query}")
        
        # Search code
        results = search_code(query, token)
        print(f"    Found {len(results)} code results")
        
        for item in results:
            repo = item.get("repository", {})
            full_name = repo.get("full_name", "")
            
            if full_name and full_name not in found_repos and full_name not in existing_sources:
                found_repos[full_name] = repo
        
        # Rate limiting
        time.sleep(60 / REQUESTS_PER_MINUTE)
    
    print(f"\nFound {len(found_repos)} unique repositories to analyze")
    
    # Analyze each repository
    new_sources = []
    
    for full_name, basic_info in found_repos.items():
        owner, repo = full_name.split("/")
        print(f"\n  Analyzing {full_name}...")
        
        # Get detailed info
        repo_info = get_repo_info(owner, repo, token)
        if not repo_info:
            continue
        
        # Check stars
        stars = repo_info.get("stargazers_count", 0)
        if stars < min_stars:
            print(f"    Skipped: {stars} stars < {min_stars}")
            continue
        
        # Check license
        license_info = repo_info.get("license", {})
        license_key = license_info.get("spdx_id", "") if license_info else ""
        
        if license_key not in allowed_licenses and license_key != "NOASSERTION":
            print(f"    Skipped: license '{license_key}' not in allowed list")
            continue
        
        # Check skill structure
        skill_paths = check_skill_structure(owner, repo, token)
        if not skill_paths:
            print(f"    Skipped: no valid skill structure found")
            continue
        
        print(f"    ✓ Found {len(skill_paths)} skills, {stars} stars, {license_key} license")
        
        new_sources.append({
            "name": full_name,
            "url": repo_info["html_url"],
            "branch": repo_info.get("default_branch", "main"),
            "skills_path": skill_paths[0].rsplit("/", 1)[0] if "/" in skill_paths[0] else "skills",
            "stars": stars,
            "license": license_key,
            "description": repo_info.get("description", ""),
            "skill_count": len(skill_paths),
            "discovered_at": datetime.now().isoformat()
        })
        
        # Rate limiting
        time.sleep(60 / REQUESTS_PER_MINUTE)
    
    # Update discovered data
    discovered_data["repositories"] = new_sources
    discovered_data["last_scan"] = datetime.now().isoformat()
    save_discovered(discovered_data)
    
    # Summary
    print("\n" + "=" * 60)
    print(f"Discovery complete!")
    print(f"  New repositories found: {len(new_sources)}")
    print("=" * 60)
    
    if new_sources:
        print("\nNew sources to potentially add:")
        for source in sorted(new_sources, key=lambda x: -x["stars"]):
            print(f"  - {source['name']} ({source['stars']} ⭐, {source['license']})")
            print(f"    {source['description'][:80]}...")
        
        print(f"\nResults saved to: {DISCOVERED_FILE}")
        print("Review and manually add approved sources to sources.json")


if __name__ == "__main__":
    main()
