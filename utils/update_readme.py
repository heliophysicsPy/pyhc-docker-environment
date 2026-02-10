"""
Extracts PyHC package versions from docker/pyhc-environment/contents/resolved-versions.txt
and puts them into a table in the README.

V2: Reads package names and lockfile versions from docker/pyhc-environment/contents
"""

import os
import re

try:
    from .pipeline_utils import parse_packages_txt
except ImportError:
    from pipeline_utils import parse_packages_txt


def _extract_display_name(package_entry):
    """Return package name for README display, preserving extras but not version pins."""
    return re.split(r'(?:===|==|~=|!=|<=|>=|<|>)', package_entry, maxsplit=1)[0].strip()


def _normalize_for_lockfile_match(name):
    """Normalize for lockfile matching: strip extras and normalize separators/case."""
    name_no_extras = re.sub(r'\[.*\]', '', name).strip()
    return name_no_extras.lower().replace('-', '_').replace('.', '_')


def extract_versions_from_lockfile(lockfile_path, package_names):
    """Extract versions for specified packages from the persisted lockfile.

    Args:
        lockfile_path: Path to resolved-versions.txt (uv pip compile output)
        package_names: List of package names to look for

    Returns:
        Dict mapping package names to versions
    """
    versions = {}

    with open(lockfile_path, 'r') as file:
        lockfile_content = file.read()

    package_names_normalized = {}
    for package_name in package_names:
        key = _normalize_for_lockfile_match(package_name)
        if key and key not in package_names_normalized:
            package_names_normalized[key] = package_name

    for line in lockfile_content.split('\n'):
        line = line.strip()
        # Skip empty lines, comments, and indented lines (dependency annotations)
        if not line or line.startswith('#') or line.startswith(' '):
            continue
        # Match package==version format
        match = re.match(r'^([a-zA-Z0-9_.-]+)==([^\s#]+)', line)
        if match:
            pkg_name, version = match.groups()
            pkg_normalized = _normalize_for_lockfile_match(pkg_name)
            if pkg_normalized in package_names_normalized:
                # Use the original package name from packages.txt for display
                original_name = package_names_normalized[pkg_normalized]
                versions[original_name] = version

    return versions


def versions_to_markdown_table(versions):
    table = "Package | Version\n---|---\n"
    for package in sorted(versions, key=lambda x: x.lower()):
        table += f"{package} | {versions[package]}\n"
    return table


def update_readme_with_table(readme_path, section_header, new_table):
    """
    Removes everything below the README's section header and replaces with the new_table
    """
    with open(readme_path, 'r') as file:
        lines = file.readlines()

    # Find the index of the section header
    section_index = next((i for i, line in enumerate(lines) if section_header in line), None)

    # If section is found, update the README
    if section_index is not None:
        updated_readme = lines[:section_index + 1] + [new_table]
        with open(readme_path, 'w') as file:
            file.writelines(updated_readme)


if __name__ == '__main__':
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # V2 canonical file paths under docker/pyhc-environment/contents
    contents_dir = os.path.join(repo_root, 'docker', 'pyhc-environment', 'contents')
    packages_file_path = os.path.join(contents_dir, 'packages.txt')
    lockfile_path = os.path.join(contents_dir, 'resolved-versions.txt')

    package_entries = parse_packages_txt(packages_file_path, preserve_specifiers=True)
    pyhc_packages = [_extract_display_name(entry) for entry in package_entries]
    package_versions = extract_versions_from_lockfile(lockfile_path, pyhc_packages)
    md_table = versions_to_markdown_table(package_versions)

    readme_file_path = os.path.join(repo_root, 'README.md')
    section_header = "## PyHC Package Versions in Current Environment"
    update_readme_with_table(readme_file_path, section_header, md_table)
