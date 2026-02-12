"""
Lightweight version utilities for PyHC Docker Environment.

This module only uses standard library imports so it can be used
by the GitHub Actions workflow before heavy dependencies are installed.

__author__ = "Shawn Polson"
"""

import os
import re


def parse_python_version_from_env_yml(env_yml_path):
    """Parse Python version from environment.yml.

    The Python line in environment.yml can have various formats:
    - conda-forge::python=3.12.9=h9e4cc4f_0_cpython  (with channel and build string)
    - python=3.12.9                                   (simple)
    - python>=3.12                                    (version specifier)

    Args:
        env_yml_path: Path to environment.yml file

    Returns:
        Python version string (e.g., "3.12" for minor version)

    Raises:
        FileNotFoundError: If environment.yml doesn't exist
        ValueError: If Python version cannot be parsed
    """
    with open(env_yml_path, 'r') as f:
        content = f.read()

    # Look for python version line in dependencies
    # Match patterns like: python=3.12.9, conda-forge::python=3.12.9=build_string
    python_pattern = re.compile(
        r'^\s*-\s*(?:[\w-]+::)?python[=<>!]+(\d+\.\d+(?:\.\d+)?)',
        re.MULTILINE
    )

    match = python_pattern.search(content)
    if match:
        full_version = match.group(1)
        # Return minor version (e.g., "3.12" from "3.12.9")
        parts = full_version.split('.')
        if len(parts) >= 2:
            return f"{parts[0]}.{parts[1]}"
        return full_version

    raise ValueError(f"Could not parse Python version from {env_yml_path}")


def get_environment_yml_path():
    """Get the path to environment.yml relative to the repo root.

    Returns:
        Path to environment.yml
    """
    # This file is in utils/, so go up one level to repo root
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(repo_root, 'docker', 'pyhc-environment', 'contents', 'environment.yml')


def get_python_version():
    """Get the Python version from environment.yml.

    Convenience function that combines path resolution and parsing.

    Returns:
        Python version string (e.g., "3.12")

    Raises:
        FileNotFoundError: If environment.yml doesn't exist
        ValueError: If Python version cannot be parsed
    """
    env_yml_path = get_environment_yml_path()
    return parse_python_version_from_env_yml(env_yml_path)


if __name__ == "__main__":
    # When run directly, print the Python version (for use in shell scripts)
    print(get_python_version())
