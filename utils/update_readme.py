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
                if package_name.lower() in line.lower():
                    match = re.search(r'==(.+?)(\s*#|$)', line)
                    if match:
                        versions[package_name] = match.group(1).strip()
                    break
    return versions


def versions_to_markdown_table(versions):
    table = "Package | Version\n---|---\n"
    for package, version in versions.items():
        table += f"{package} | {version}\n"
    return table
