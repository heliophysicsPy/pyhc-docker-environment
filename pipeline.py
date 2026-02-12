"""
PyHC Docker Environment Pipeline

This script drives the workflow stages and operates on canonical files in:
docker/pyhc-environment/contents/

Primary modes:
- --auto-pin: pin PyHC packages in packages.txt to latest constraint-compatible versions
  and detect direct package set additions/removals against resolved-versions.txt
- --compile: run uv pip compile to produce /tmp/new-resolved-versions.txt
- --post-build: persist /tmp/new-resolved-versions.txt to resolved-versions.txt
- --generate-spreadsheet: optional dependency analysis artifact for diagnostics

Behavior notes:
- packages.txt contains pinned direct PyHC package entries (extras preserved)
- constraints.txt is applied during auto-pin and compile
- resolved-versions.txt is the persisted lockfile for the last successful build

__author__ = "Shawn Polson"
"""

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from utils.pipeline_utils import (
    set_github_output,
    parse_packages_txt,
    get_python_version,
    auto_pin_packages_to_latest,
    detect_package_set_changes,
)

REPO_ROOT = Path(__file__).resolve().parent
PYHC_ENV_CONTENTS_DIR = REPO_ROOT / "docker" / "pyhc-environment" / "contents"
PACKAGES_FILE = str(PYHC_ENV_CONTENTS_DIR / "packages.txt")
CONSTRAINTS_FILE = str(PYHC_ENV_CONTENTS_DIR / "constraints.txt")
LOCKFILE_PATH = str(PYHC_ENV_CONTENTS_DIR / "resolved-versions.txt")
TMP_RESOLVED_PATH = "/tmp/new-resolved-versions.txt"


def format_changed_packages(
    version_changes: dict[str, tuple[str | None, str]],
    package_set_changes: dict[str, dict[str, str | None]] | None = None,
) -> str:
    """Format package change lines for GitHub issue comments and workflow logs."""
    lines = []
    for pkg, versions in sorted(version_changes.items(), key=lambda item: item[0].lower()):
        old, new = versions
        old_version = old if old else "unpinned"
        lines.append(f"{pkg}: {old_version} → {new}")

    if package_set_changes:
        added = package_set_changes.get("added", {})
        removed = package_set_changes.get("removed", {})

        for pkg in sorted(added):
            added_version = added[pkg] if added[pkg] else "unpinned"
            lines.append(f"{pkg}: added {added_version}")

        for pkg in sorted(removed):
            removed_version = removed[pkg] if removed[pkg] else "unknown"
            lines.append(f"{pkg}: {removed_version} → removed")

    return "\n".join(lines)


def run_uv_compile(packages_file: str, output_file: str, python_version: str = None,
                   constraints_file: str = None) -> tuple[bool, str]:
    """
    Run uv pip compile to resolve dependencies.

    Args:
        packages_file: Path to packages.txt
        output_file: Path to write resolved dependencies
        python_version: Python version to target (default: from environment.yml)
        constraints_file: Optional path to constraints.txt for blocking versions

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

    # Add constraints file if provided and exists
    if constraints_file and os.path.exists(constraints_file):
        cmd.extend(["-c", constraints_file])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            return False, result.stderr
        return True, ""
    except subprocess.TimeoutExpired:
        return False, "uv pip compile timed out after 10 minutes"
    except Exception as e:
        return False, str(e)


def update_lockfile(tmp_resolved_path: str, lockfile_path: str) -> None:
    """Update the stored lockfile after successful build."""
    shutil.copy(tmp_resolved_path, lockfile_path)
    print(f"Updated lockfile at {lockfile_path}")


def generate_spreadsheet(packages_file=None):
    """
    Generate dependency spreadsheet using legacy v1 code.
    This is available for debugging/analysis but not part of the normal workflow.

    Args:
        packages_file: Path to packages.txt (default: docker/pyhc-environment/contents/packages.txt)
    """
    try:
        from utils.generate_dependency_table import (
            generate_dependency_table_data,
            excel_spreadsheet_from_table_data,
            find_spec0_problems,
            find_dependency_conflicts,
        )

        if packages_file is None:
            packages_file = PACKAGES_FILE

        filename = f"PyHC-Dependency-Table-{datetime.now().strftime('%Y-%m-%d-%H-%M')}.xlsx"
        spreadsheet_folder = "spreadsheets"
        if not os.path.exists(spreadsheet_folder):
            os.makedirs(spreadsheet_folder)
        spreadsheet_path = os.path.join(spreadsheet_folder, filename)

        # Read exact entries (including extras and version pins) from packages.txt.
        all_packages = parse_packages_txt(packages_file, preserve_specifiers=True)
        print(f"Generating spreadsheet for {len(all_packages)} package entries from {packages_file}")

        workers_str = os.environ.get("PYHC_SPREADSHEET_WORKERS", "2")
        try:
            max_workers = max(1, int(workers_str))
        except ValueError as exc:
            raise ValueError(
                f"Invalid PYHC_SPREADSHEET_WORKERS value '{workers_str}'. "
                "Expected a positive integer."
            ) from exc

        print(f"Using spreadsheet worker count: {max_workers}")
        table_data = generate_dependency_table_data(all_packages, max_workers=max_workers)

        # Check for dependency conflicts in spreadsheet
        dependency_conflicts = find_dependency_conflicts(table_data)
        if dependency_conflicts:
            conflict_comment_lines = [
                "**Dependency conflicts found in spreadsheet:**",
                "```",
                *dependency_conflicts,
                "```",
            ]
            conflict_comment = "\n".join(conflict_comment_lines)
            print(f"Found {len(dependency_conflicts)} dependency conflict(s) in spreadsheet:")
            for conflict in dependency_conflicts:
                print(f"  {conflict}")
        else:
            conflict_comment = ""
            print("No dependency conflicts found in spreadsheet.")

        set_github_output("conflict_comment", conflict_comment)
        set_github_output("conflict_count", str(len(dependency_conflicts)))

        # Check for SPEC 0 problems
        spec0_problems = find_spec0_problems(table_data)
        if spec0_problems:
            spec0_comment_lines = [
                "**SPEC 0 problems detected:**",
                "```",
                *spec0_problems,
                "```",
            ]
            spec0_comment = "\n".join(spec0_comment_lines)
            print(f"Detected {len(spec0_problems)} SPEC 0 problem(s):")
            for problem in spec0_problems:
                print(f"  {problem}")
        else:
            spec0_comment = ""
            print("No SPEC 0 problems detected.")

        set_github_output("spec0_comment", spec0_comment)
        set_github_output("spec0_problem_count", str(len(spec0_problems)))

        table = excel_spreadsheet_from_table_data(table_data)
        table.save(spreadsheet_path)

        print(f"Generated spreadsheet: {spreadsheet_path}")
        return spreadsheet_path
    except ImportError as e:
        print(f"Error importing legacy code for spreadsheet generation: {e}")
        print("Make sure pipeline_requirements.txt dependencies are installed.")
        return None


def main():
    parser = argparse.ArgumentParser(description="PyHC Docker Environment Pipeline")
    parser.add_argument(
        "--generate-spreadsheet",
        action="store_true",
        help="Generate dependency spreadsheet using legacy v1 code (for debugging)"
    )
    parser.add_argument(
        "--auto-pin",
        action="store_true",
        help="Update packages.txt with strict latest PyPI version pins for PyHC packages"
    )
    parser.add_argument(
        "--compile",
        action="store_true",
        help="Run uv pip compile with constraints to generate lockfile"
    )
    parser.add_argument(
        "--post-build",
        action="store_true",
        help="Update persisted lockfile from /tmp/new-resolved-versions.txt after successful build"
    )
    args = parser.parse_args()

    # Canonical file paths
    packages_file = PACKAGES_FILE
    lockfile_path = LOCKFILE_PATH
    constraints_file = CONSTRAINTS_FILE
    tmp_resolved_path = TMP_RESOLVED_PATH

    # Handle post-build lockfile update mode
    if args.post_build:
        post_build_update_lockfile()
        return

    # Handle spreadsheet generation mode
    if args.generate_spreadsheet:
        spreadsheet = generate_spreadsheet()
        if spreadsheet:
            print(f"Spreadsheet saved to: {spreadsheet}")
            set_github_output("spreadsheet_path", spreadsheet)
        return

    # Handle auto-pin mode (strict latest PyHC pinning)
    if args.auto_pin:
        print("Auto-pinning packages to latest PyPI versions...")
        try:
            version_changes = auto_pin_packages_to_latest(packages_file, constraints_file)
        except RuntimeError as e:
            print(f"ERROR: {e}")
            set_github_output("pyhc_packages_changed", "false")
            set_github_output("auto_pin_error", str(e))
            sys.exit(1)

        package_set_changes = detect_package_set_changes(packages_file, lockfile_path)
        added_packages = package_set_changes.get("added", {})
        removed_packages = package_set_changes.get("removed", {})
        added_names = set(added_packages.keys())

        # Avoid duplicate lines for newly added unpinned packages auto-pinned in this same run.
        display_version_changes = {
            pkg: versions for pkg, versions in version_changes.items() if pkg not in added_names
        }

        has_version_changes = bool(display_version_changes)
        has_package_set_changes = bool(added_packages or removed_packages)
        should_run = has_version_changes or has_package_set_changes

        if should_run:
            if has_version_changes:
                print(f"\nPyHC packages updated: {len(display_version_changes)}")
            for pkg, (old, new) in sorted(display_version_changes.items()):
                old_str = old if old else "unpinned"
                print(f"  {pkg}: {old_str} -> {new}")

            if has_package_set_changes:
                print("\nDetected package list changes in packages.txt:")
                for pkg in sorted(added_packages):
                    version = added_packages[pkg] if added_packages[pkg] else "unpinned"
                    print(f"  {pkg}: added {version}")
                for pkg in sorted(removed_packages):
                    version = removed_packages[pkg] if removed_packages[pkg] else "unknown"
                    print(f"  {pkg}: {version} -> removed")

            set_github_output("pyhc_packages_changed", "true")
            set_github_output(
                "changed_packages",
                format_changed_packages(display_version_changes, package_set_changes),
            )
        else:
            print("No PyHC package updates found")
            set_github_output("pyhc_packages_changed", "false")
        return

    # Handle compile mode (just run uv compile with constraints)
    if args.compile:
        print("Running uv pip compile with constraints...")
        success, error = run_uv_compile(packages_file, tmp_resolved_path,
                                        constraints_file=constraints_file)
        if not success:
            print(f"ERROR: Dependency resolution failed:\n{error}")
            set_github_output("compile_success", "false")
            set_github_output("compile_error", error)
            sys.exit(1)
        print("Dependency resolution succeeded. Resolved versions:")
        print("-" * 50)
        with open(tmp_resolved_path, "r") as f:
            print(f.read())
        print("-" * 50)
        set_github_output("compile_success", "true")
        return

    parser.error("No mode specified. Use one of: --auto-pin, --compile, --generate-spreadsheet, --post-build")


def post_build_update_lockfile():
    """
    Call this after successful Docker build to update the lockfile.
    Can be called from GitHub Actions or manually.
    """
    lockfile_path = LOCKFILE_PATH
    tmp_resolved_path = TMP_RESOLVED_PATH

    if os.path.exists(tmp_resolved_path):
        update_lockfile(tmp_resolved_path, lockfile_path)
        print("Lockfile updated successfully.")
    else:
        print("Warning: Temp resolved file not found. Lockfile not updated.")


if __name__ == "__main__":
    main()
