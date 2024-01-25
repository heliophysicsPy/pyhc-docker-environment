"""
Extracts PyHC package versions from pyhc-environment's requirements.txt and puts them into a table in the README.
"""

import os
import re

from generate_dependency_table import *


def extract_versions_from_requirements(requirements_path, package_names):
    versions = {}
    with open(requirements_path, 'r') as file:
        requirements = file.readlines()

    for package in package_names:
        package_name, *version_specifier = package.split('==')
        package_name = package_name.strip()

        # If version is already specified, use it directly
        if version_specifier:
            versions[package_name] = version_specifier[0].strip()
        else:
            # Extract version from requirements.txt
            for line in requirements:
                # Regex to match the package name at the start of the line or after a comment
                match = re.match(rf"(^|\#\s*){package_name.lower()}([><=]=?)", line.lower())
                if match:
                    version_match = re.search(r'([><=]=?\s*)([^#\s]+)', line)
                    if version_match:
                        versions[package_name] = version_match.group(2).strip()
                        break
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
    requirements_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'docker', 'pyhc-environment', 'contents', 'requirements.txt')
    pyhc_packages = get_core_pyhc_packages() + get_other_pyhc_packages()

    package_versions = extract_versions_from_requirements(requirements_file_path, pyhc_packages)
    md_table = versions_to_markdown_table(package_versions)

    readme_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'README.md')
    section_header = "## PyHC Package Versions in Current Environment"
    update_readme_with_table(readme_file_path, section_header, md_table)
