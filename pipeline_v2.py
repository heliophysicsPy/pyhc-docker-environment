"""
PyHC Docker Environment Pipeline V2

Simplified pipeline that uses packages.txt (just package names) instead of
the complex version resolution spreadsheet approach. Lets uv resolve
transitive dependencies at build time.

Key differences from v1:
- packages.txt contains only PyHC package names (with optional pins for broken releases)
- resolved-versions.txt is a lockfile tracking what was deployed
- Change detection compares current resolution against lockfile
- No more pipdeptree dependency resolution per-package

__author__ = "Shawn Polson"
"""

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from utils.pipeline_utils import set_github_output, parse_packages_txt, get_python_version


def run_uv_compile(packages_file: str, output_file: str, python_version: str = None) -> tuple[bool, str]:
    """
    Run uv pip compile to resolve dependencies.

    Args:
        packages_file: Path to packages.txt
        output_file: Path to write resolved dependencies
        python_version: Python version to target (default: from environment.yml)

    Returns:
        Tuple of (success, error_message)
    """
    if python_version is None:
        python_version = get_python_version()

    cmd = [
        "uv", "pip", "compile",
        packages_file,
        "-o", output_file,
        "--python-version", python_version,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            return False, result.stderr
        return True, ""
    except subprocess.TimeoutExpired:
        return False, "uv pip compile timed out after 10 minutes"
    except Exception as e:
        return False, str(e)


def normalize_lockfile(content: str) -> list[str]:
    """
    Normalize lockfile content for comparison.

    Extracts just the package==version lines, ignoring comments and metadata.
    Returns sorted list of normalized package lines.
    """
    lines = []
    for line in content.split("\n"):
        line = line.strip()
        # Skip empty lines, comments, and 'via' annotations
        if not line or line.startswith("#") or line.startswith("# via"):
            continue
        # Only keep lines with package==version format
        if "==" in line and not line.startswith(" "):
            # Normalize to lowercase for comparison
            lines.append(line.lower())
    return sorted(lines)


def check_for_changes(packages_file: str, lockfile_path: str, tmp_resolved_path: str) -> tuple[bool, str, list[str]]:
    """
    Compare current resolution against last deployed lockfile.

    Args:
        packages_file: Path to packages.txt
        lockfile_path: Path to existing resolved-versions.txt
        tmp_resolved_path: Path to write new resolution for comparison

    Returns:
        Tuple of (should_run, reason, changes_list)
    """
    # Run uv to see what it would resolve TODAY
    success, error = run_uv_compile(packages_file, tmp_resolved_path)

    if not success:
        return True, f"resolution_failed: {error}", []

    # Check if lockfile exists
    if not os.path.exists(lockfile_path):
        return True, "no_existing_lockfile", []

    # Compare against stored lockfile
    with open(lockfile_path, "r") as f:
        current_content = f.read()

    with open(tmp_resolved_path, "r") as f:
        new_content = f.read()

    current_packages = normalize_lockfile(current_content)
    new_packages = normalize_lockfile(new_content)

    if current_packages != new_packages:
        # Find what changed
        current_set = set(current_packages)
        new_set = set(new_packages)

        added = new_set - current_set
        removed = current_set - new_set

        changes = []
        for pkg in sorted(added):
            changes.append(f"+ {pkg}")
        for pkg in sorted(removed):
            changes.append(f"- {pkg}")

        return True, "versions_changed", changes

    return False, "no_changes", []


def update_lockfile(tmp_resolved_path: str, lockfile_path: str) -> None:
    """Update the stored lockfile after successful build."""
    shutil.copy(tmp_resolved_path, lockfile_path)
    print(f"Updated lockfile at {lockfile_path}")


def generate_spreadsheet(packages_file=None):
    """
    Generate dependency spreadsheet using legacy v1 code.
    This is available for debugging/analysis but not part of normal v2 flow.

    Args:
        packages_file: Path to packages.txt (default: repo root packages.txt)
    """
    try:
        from utils.generate_dependency_table import (
            generate_dependency_table_data,
            excel_spreadsheet_from_table_data,
        )

        if packages_file is None:
            packages_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "packages.txt")

        filename = f"PyHC-Dependency-Table-{datetime.now().strftime('%Y-%m-%d-%H-%M')}.xlsx"
        spreadsheet_folder = "spreadsheets"
        if not os.path.exists(spreadsheet_folder):
            os.makedirs(spreadsheet_folder)
        spreadsheet_path = os.path.join(spreadsheet_folder, filename)

        # Read packages from packages.txt (single source of truth)
        all_packages = parse_packages_txt(packages_file)
        print(f"Generating spreadsheet for {len(all_packages)} packages from {packages_file}")

        table_data = generate_dependency_table_data(all_packages)
        table = excel_spreadsheet_from_table_data(table_data)
        table.save(spreadsheet_path)

        print(f"Generated spreadsheet: {spreadsheet_path}")
        return spreadsheet_path
    except ImportError as e:
        print(f"Error importing legacy code for spreadsheet generation: {e}")
        print("Make sure pipeline_requirements.txt dependencies are installed.")
        return None


def main():
    parser = argparse.ArgumentParser(description="PyHC Docker Environment Pipeline V2")
    parser.add_argument(
        "--generate-spreadsheet",
        action="store_true",
        help="Generate dependency spreadsheet using legacy v1 code (for debugging)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force pipeline to run even if no changes detected"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check for changes without triggering build"
    )
    args = parser.parse_args()

    # Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    packages_file = os.path.join(script_dir, "packages.txt")
    lockfile_path = os.path.join(script_dir, "resolved-versions.txt")
    tmp_resolved_path = "/tmp/new-resolved-versions.txt"

    # Handle spreadsheet generation mode
    if args.generate_spreadsheet:
        spreadsheet = generate_spreadsheet()
        if spreadsheet:
            print(f"Spreadsheet saved to: {spreadsheet}")
            set_github_output("spreadsheet_path", spreadsheet)
        return

    # Check for changes
    print("Checking for package updates...")
    should_run, reason, changes = check_for_changes(packages_file, lockfile_path, tmp_resolved_path)

    if args.force:
        should_run = True
        reason = "forced"

    if not should_run:
        print(f"No changes detected ({reason}), skipping build.")
        set_github_output("should_run", "false")
        return

    print(f"Changes detected ({reason}), triggering build.")

    if changes:
        print("Package changes:")
        for change in changes[:20]:  # Limit output
            print(f"  {change}")
        if len(changes) > 20:
            print(f"  ... and {len(changes) - 20} more changes")

    if args.dry_run:
        print("Dry run mode - not updating files.")
        set_github_output("should_run", "false")
        return

    # Set GitHub Actions outputs
    set_github_output("should_run", "true")
    set_github_output("change_reason", reason)

    # Format changes for GitHub Actions output (URL-encoded newlines)
    if changes:
        changes_formatted = "%0A".join(changes[:20])
        if len(changes) > 20:
            changes_formatted += f"%0A... and {len(changes) - 20} more"
        set_github_output("package_changes", changes_formatted)

    print("Pipeline check complete. Ready for Docker build.")


def post_build_update_lockfile():
    """
    Call this after successful Docker build to update the lockfile.
    Can be called from GitHub Actions or manually.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    lockfile_path = os.path.join(script_dir, "resolved-versions.txt")
    tmp_resolved_path = "/tmp/new-resolved-versions.txt"

    if os.path.exists(tmp_resolved_path):
        update_lockfile(tmp_resolved_path, lockfile_path)
        print("Lockfile updated successfully.")
    else:
        print("Warning: Temp resolved file not found. Lockfile not updated.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--post-build":
        post_build_update_lockfile()
    else:
        main()
