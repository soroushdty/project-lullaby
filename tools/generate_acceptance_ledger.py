#!/usr/bin/env python3
"""Generate an evidence-based acceptance ledger for all repository specs."""

import json
import re
import os
from datetime import datetime, UTC
from pathlib import Path
import subprocess

def get_implemented_specs():
    specs_dir = Path("specs")
    specs = []
    for spec_path in sorted(specs_dir.glob("*/spec.md")):
        spec_id_match = re.search(r"id:\s*(SPEC-\d+)", spec_path.read_text())
        if spec_id_match:
             spec_id = spec_id_match.group(1)
        else:
             spec_id = spec_path.parent.name.split("-")[0]
             if spec_id.isdigit():
                 spec_id = f"SPEC-{spec_id}"
        
        title = "Unknown"
        title_match = re.search(r"title:\s*(.*)", spec_path.read_text())
        if title_match:
            title = title_match.group(1).strip()
            
        specs.append({"id": spec_id, "path": str(spec_path), "title": title})
    return specs

def check_changelog(spec_id):
    result = subprocess.run(
        ["python3", "tools/changelog_validator.py", "--spec-id", spec_id.lower()],
        capture_output=True,
        text=True
    )
    return result.returncode == 0

def check_artifacts(spec_id):
    manifest_path = Path("outputs/figures/manifest.json")
    if not manifest_path.exists():
        return False
    try:
        manifest = json.loads(manifest_path.read_text())
        # Search for artifacts mentioning this spec in metadata
        for artifact in manifest.get("artifacts", []):
            if artifact.get("metadata", {}).get("spec_id") == spec_id:
                return True
            # Heuristic: check if artifact_id contains panel number related to spec (if known)
    except:
        pass
    return False

def generate_ledger():
    specs = get_implemented_specs()
    ledger_specs = []
    complete_count = 0
    
    for spec in specs:
        has_changelog = check_changelog(spec["id"])
        has_artifacts = check_artifacts(spec["id"])
        
        # Determine status
        status = "incomplete"
        remediation = []
        
        if not has_changelog:
            remediation.append("Missing CHANGELOG.md entry")
        
        if has_changelog:
            status = "complete"
            complete_count += 1
            
        ledger_specs.append({
            "id": spec["id"],
            "title": spec["title"],
            "status": status,
            "evidence": {
                "changelog_entry": has_changelog,
                "artifacts_registered": has_artifacts,
                "spec_path": spec["path"]
            },
            "remediation": remediation
        })
    
    ledger = {
        "last_updated": datetime.now(UTC).isoformat(),
        "total_specs": len(ledger_specs),
        "complete_count": complete_count,
        "specs": ledger_specs
    }
    
    out_path = Path("artifacts/acceptance-ledger.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(ledger, indent=2) + "\n")
    print(f"Generated ledger at {out_path}")

if __name__ == "__main__":
    generate_ledger()
