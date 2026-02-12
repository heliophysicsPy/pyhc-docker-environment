"""
PyHC environment pipeline utility functions.

__author__ = "Shawn Polson"
"""


import os
import re
import requests
import collections
from datetime import datetime, timedelta
import pandas as pd
from packaging.version import Version
from packaging.specifiers import SpecifierSet, InvalidSpecifier


try:
    from .version_utils import (
        parse_python_version_from_env_yml,
        get_environment_yml_path,
        get_python_version,
    )
except ImportError:
    from version_utils import (
        parse_python_version_from_env_yml,
        get_environment_yml_path,
        get_python_version,
    )


def set_github_output(name: str, value: str) -> None:
    """Set a GitHub Actions output variable.

    Uses the modern $GITHUB_OUTPUT file method, with fallback to
    the deprecated ::set-output syntax for local testing.
    """
    if value is None:
        value = ""
    elif not isinstance(value, str):
        value = str(value)

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            # Use multiline-safe format when needed
            if "\n" in value:
                f.write(f"{name}<<EOF\n{value}\nEOF\n")
            else:
                f.write(f"{name}={value}\n")
    else:
        # Fallback for local testing or older GitHub Actions syntax
        if "\n" in value:
            value = value.replace("\n", "%0A")
        print(f"::set-output name={name}::{value}")


def parse_packages_txt(packages_path, preserve_specifiers=False):
    """Parse packages.txt and return package entries.

    Args:
        packages_path: Path to packages.txt
        preserve_specifiers: If True, preserve extras/version pins. If False,
            return only base package names.

    Returns:
        List of parsed package entries from packages.txt.
    """
    packages = []
    with open(packages_path, 'r') as file:
        for line in file:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            # Remove inline comments while preserving the package spec itself.
            package_entry = line.split('#', 1)[0].strip()
            if not package_entry:
                continue

            if preserve_specifiers:
                # Keep exact package entry, e.g. "pyhc-core[tests]==0.0.7".
                packages.append(package_entry)
            else:
                # Extract base package name, e.g. "pyhc-core".
                package_name = re.split(r'[=<>!\[\s]', package_entry)[0]
                if package_name:
                    packages.append(package_name)
    return packages


def fetch_latest_version_from_pypi(package_name):
    """
    Fetch the latest version of a package from PyPI.
    """
    try:
        response = requests.get(f"https://pypi.org/pypi/{package_name}/json")
        response.raise_for_status()
        data = response.json()
        return data['info']['version']
    except requests.RequestException as e:
        print(f"Error fetching package {package_name} from PyPI: {e}")
        return None


def fetch_all_versions_from_pypi(package_name: str) -> list:
    """
    Fetch all available versions of a package from PyPI.

    Args:
        package_name: Name of the package to query

    Returns:
        List of version strings, or None if fetch fails
    """
    try:
        response = requests.get(f"https://pypi.org/pypi/{package_name}/json")
        response.raise_for_status()
        data = response.json()
        return list(data['releases'].keys())
    except requests.RequestException as e:
        print(f"Error fetching versions for {package_name} from PyPI: {e}")
        return None


def find_highest_satisfying_version(package_name: str, constraint: SpecifierSet) -> str:
    """
    Find the highest version of a package that satisfies the given constraint.

    Args:
        package_name: Name of the package to query
        constraint: SpecifierSet defining version constraints

    Returns:
        Highest version string that satisfies the constraint, or None if:
        - PyPI fetch fails
        - No version satisfies the constraint
    """
    all_versions = fetch_all_versions_from_pypi(package_name)
    if all_versions is None:
        return None

    # Filter to valid, non-prerelease versions that satisfy the constraint
    valid_versions = []
    for v in all_versions:
        try:
            parsed = Version(v)
            # Skip pre-releases and dev releases
            if parsed.is_prerelease or parsed.is_devrelease:
                continue
            # Check if version satisfies constraint
            if v in constraint:
                valid_versions.append(parsed)
        except Exception:
            # Skip versions that can't be parsed
            continue

    if not valid_versions:
        return None

    # Return highest valid version
    return str(max(valid_versions))


def strip_extras(package_name):
    # This regex removes any bracketed extras.
    return re.sub(r'\[.*?\]', '', package_name)


def check_for_package_updates(requirements_path, package_names, ignore_list=None, skip_versions=None):
    """
    Check if the specified packages are up-to-date with PyPI.

    This function compares the current environment's packages (as listed in the given
    requirements.txt file) against the latest versions on PyPI. If any package is not
    present in requirements.txt (i.e., newly added to the list of packages you want to
    track), it will be considered as "Not Installed" and treated as requiring an update
    to add it to the environment.

    Args:
        requirements_path (str): The path to the requirements.txt file.
        package_names (list of str): The list of packages to check.
        ignore_list (list of str, optional): A list of package names to ignore.
        skip_versions (dict, optional): A dict mapping package names (lowercase) to lists
            of version strings to skip. If the latest PyPI version is in the skip list,
            it won't be reported as an update. Useful for skipping broken releases.

    Returns:
        dict: A dictionary mapping package names to a dict with 'current_version' and
              'latest_version' keys for packages that require updates. For newly introduced
              packages, 'current_version' will be set to "Not Installed".
    """
    if ignore_list is None:
        ignore_list = []
    if skip_versions is None:
        skip_versions = {}
    updates_required = {}

    with open(requirements_path, 'r') as file:
        requirements = file.readlines()

    for package in package_names:
        # Strip any version specifier and fetch the package name
        package_name = package.split('==')[0].strip()

        # Strip extras from package_name before querying PyPI
        package_name_base = strip_extras(package_name)

        if package_name in ignore_list or package_name_base in ignore_list:
            continue

        # Extract the current version from requirements.txt
        current_version = None
        for line in requirements:
            # Match only when the package name is at the beginning of the line or after a comment/whitespace
            # and is followed by == or whitespace - this prevents partial matches
            if re.search(rf'(^|\s|#)\s*{re.escape(package_name.lower())}(==|\s|$|\[)', line.lower()):
                match = re.search(r'==(.+?)(\s*#|$)', line)  # Note, this only catches lines with == (should be the case for all PyHC packages, but there's an updated regex in update_readme.py for reference)
                if match:
                    current_version = match.group(1).strip()
                break

        # Fetch the latest version from PyPI using the stripped package name
        latest_version = fetch_latest_version_from_pypi(package_name_base)

        # Check if this version should be skipped (e.g., known broken release)
        # Normalize both sides to lowercase for case-insensitive matching
        skip_versions_lower = {k.lower(): v for k, v in skip_versions.items()}
        skip_list = skip_versions_lower.get(package_name_base.lower(), [])
        if latest_version and latest_version in skip_list:
            continue

        # If we have a latest_version from PyPI, determine if an update is needed.
        if latest_version:
            # If package is not installed or installed but out-of-date, we consider it an update.
            if current_version is None or latest_version != current_version:
                updates_required[package_name] = {
                    'current_version': current_version if current_version else "Not Installed",
                    'latest_version': latest_version
                }

    return updates_required


def get_docker_image_names(docker_folder_path):
    """
    Extracts the names of Docker images from the subfolders under the specified `docker/` directory.
    """
    try:
        return [name for name in os.listdir(docker_folder_path) if
                os.path.isdir(os.path.join(docker_folder_path, name))]
    except Exception as e:
        print(f"Error in getting Docker image names: {e}")
        return []


def comment_out_numpy_and_spacepy(requirements_file_path):
    """
    This function takes a requirements.txt file as input, comments out lines for "numpy" and/or "spacepy",
    and adds a comment after these lines.
    """
    # Read the contents of the file
    with open(requirements_file_path, 'r') as file:
        lines = file.readlines()

    # Iterate through the lines and comment out numpy and spacepy
    for i, line in enumerate(lines):
        if 'numpy' in line or 'spacepy' in line:
            lines[i] = f"# {line.strip()}  # gets installed first in the Dockerfile\n"

    # Write the modified contents back to the file
    with open(requirements_file_path, 'w') as file:
        file.writelines(lines)


def comment_out_pysatcdf(requirements_file_path):
    """
    This function takes a requirements.txt file as input, comments out the line for "pysatCDF",
    and adds a comment after the line.
    """
    # Read the contents of the file
    with open(requirements_file_path, 'r') as file:
        lines = file.readlines()

    # Iterate through the lines and comment out package
    for i, line in enumerate(lines):
        if 'pysatCDF' in line:
            lines[i] = f"# {line.strip()}  # pip install is broken and I don't want to install from GitHub\n"

    # Write the modified contents back to the file
    with open(requirements_file_path, 'w') as file:
        file.writelines(lines)


def comment_out_kamodo(requirements_file_path):
    """
    This function takes a requirements.txt file as input, comments out the line for "kamodo",
    and adds a comment after the line.
    """
    # Read the contents of the file
    with open(requirements_file_path, 'r') as file:
        lines = file.readlines()

    # Iterate through the lines and comment out package
    for i, line in enumerate(lines):
        if 'kamodo' in line:
            lines[i] = f"# {line.strip()}  # gets installed from GitHub instead\n"

    # Write the modified contents back to the file
    with open(requirements_file_path, 'w') as file:
        file.writelines(lines)


def comment_out_pyspedas_pytplot_pytplot_mpl_temp(requirements_file_path):
    """
    This function takes a requirements.txt file as input, comments out lines for "pyspedas", "pytplot", and
    "pytplot-mpl-temp" and adds a comment after these lines.
    """
    # Read the contents of the file
    with open(requirements_file_path, 'r') as file:
        lines = file.readlines()

    # Iterate through the lines and comment out packages
    for i, line in enumerate(lines):
        if 'pyspedas' in line or 'pytplot' in line or 'pytplot-mpl-temp' in line:
            lines[i] = f"# {line.strip()}  # gets installed last in the Dockerfile\n"

    # Write the modified contents back to the file
    with open(requirements_file_path, 'w') as file:
        file.writelines(lines)


def comment_out_pytplot_and_pytplot_mpl_temp(requirements_file_path):
    """
    This function takes a requirements.txt file as input, comments out lines for "pytplot"
    and "pytplot_mpl_temp", and adds a comment after those lines.
    """
    # Read the contents of the file
    with open(requirements_file_path, 'r') as file:
        lines = file.readlines()

    # Iterate through the lines and comment out packages
    for i, line in enumerate(lines):
        if 'pytplot' in line or 'pytplot-mpl-temp' in line:
            lines[i] = f"# {line.strip()}  # pySPEDAS controls PyTplot installation\n"

    # Write the modified contents back to the file
    with open(requirements_file_path, 'w') as file:
        file.writelines(lines)


def specify_numpy_1_26_4(requirements_file_path):
    """
    This function takes a requirements.txt file as input, modifies the line for numpy to specify version 1.26.4,
    and adds a comment after the line indicating the original specification and reason for the change.
    """
    # Read the contents of the file
    with open(requirements_file_path, 'r') as file:
        lines = file.readlines()

    # Iterate through the lines and find the numpy package
    for i, line in enumerate(lines):
        if 'numpy' in line:
            original_line = line.strip()
            lines[i] = f"numpy==1.26.4  # was originally '{original_line}' but numpy 2 breaks our env (issue #12)\n"

    # Write the modified contents back to the file
    with open(requirements_file_path, 'w') as file:
        file.writelines(lines)


def get_spec0_packages():
    """
    Returns a list of SPEC 0 core packages with minimum supported versions based on current date.
    SPEC 0 policy: Drop support for core package dependencies 2 years after their initial release.

    :return: A list like ["numpy>=2.0.0", "scipy>=1.11.0", ...]
    """
    # SPEC 0 core packages
    core_packages = [
        "numpy",
        "scipy",
        "matplotlib",
        "pandas",
        "scikit-image",
        "networkx",
        "scikit-learn",
        "xarray",
        "ipython",
        "zarr"
    ]

    # SPEC 0: Drop support 2 years after release
    # So minimum supported version = oldest version whose drop_date hasn't passed yet
    plus24 = timedelta(days=int(365 * 2))  # 2 year support window for core packages
    current_date = datetime.now()

    spec0_requirements = []

    for package in core_packages:
        print(f"Querying PyPI for {package} SPEC 0 minimum version...", end="", flush=True)

        try:
            # Query PyPI for package releases
            response = requests.get(
                f"https://pypi.org/simple/{package}",
                headers={"Accept": "application/vnd.pypi.simple.v1+json"},
            )
            response.raise_for_status()
            data = response.json()

            # Collect release dates for each version
            file_date = collections.defaultdict(list)
            for f in data["files"]:
                ver = f["filename"].split("-")[1]
                try:
                    version = Version(ver)
                except:
                    continue

                # Skip pre-releases and patch versions (only consider X.Y.0)
                if version.is_prerelease or version.micro != 0:
                    continue

                # Parse upload time
                release_date = None
                for format in ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"]:
                    try:
                        release_date = datetime.strptime(f["upload-time"], format)
                        break
                    except:
                        pass

                if not release_date:
                    continue

                file_date[version].append(release_date)

            # Get earliest release date for each version
            release_dates = {v: min(file_date[v]) for v in file_date}

            # Filter versions that are still within support window
            # (drop_date must be in the future)
            supported_versions = []
            for ver, release_date in sorted(release_dates.items()):
                drop_date = release_date + plus24
                if drop_date >= current_date:
                    supported_versions.append(ver)

            # Get minimum supported version
            if supported_versions:
                min_version = min(supported_versions)
                spec0_requirements.append(f"{package}>={min_version}")
                print(f"OK (>={min_version})")
            else:
                # No version meets criteria, don't add constraint
                print("OK (no constraint)")

        except Exception as e:
            print(f"FAILED ({e})")
            # On error, continue without adding this package
            continue

    return spec0_requirements


# ============================================
# Auto-Pin Functions (Strict Latest-Pin Workflow)
# ============================================


def fetch_all_latest_versions(packages: list) -> dict:
    """Fetch latest versions from PyPI for all packages.

    Fails explicitly if any fetch fails.

    Args:
        packages: List of package names to fetch versions for

    Returns:
        Dict mapping package name → latest version

    Raises:
        RuntimeError: If any PyPI fetch fails
    """
    # TODO: Consider parallelization to speed up fetching if this becomes slow
    versions = {}
    for pkg in packages:
        latest = fetch_latest_version_from_pypi(pkg)
        if latest is None:
            raise RuntimeError(f"Failed to fetch latest version for '{pkg}' from PyPI")
        versions[pkg] = latest
    return versions


def get_current_pyhc_pins(packages_file: str) -> dict:
    """Extract current version pins from packages.txt.

    Skips commented-out packages (excluded packages like kamodo, pysatCDF).

    Args:
        packages_file: Path to packages.txt

    Returns:
        Dict mapping package name (lowercase) → version (or None if unpinned).
        Includes original package entry for preserving extras.
    """
    pins = {}
    with open(packages_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue  # Skip comments and empty lines
            # Parse "package==1.2.3" or "package[extras]==1.2.3" or just "package"
            if '==' in line:
                # Split only on first == to handle version correctly
                name_part, version = line.split('==', 1)
                # Remove inline comments from version
                version = version.split('#')[0].strip()
                # Extract base name (remove extras)
                name = re.split(r'\[', name_part)[0].strip()
                pins[name.lower()] = {
                    'version': version,
                    'original': line,
                    'extras': '[' + name_part.split('[')[1] if '[' in name_part else ''
                }
            else:
                # No version pin
                # Remove inline comments
                clean_line = line.split('#')[0].strip()
                name = re.split(r'\[', clean_line)[0].strip()
                extras = ''
                if '[' in clean_line:
                    extras = '[' + clean_line.split('[')[1].split(']')[0] + ']'
                pins[name.lower()] = {
                    'version': None,
                    'original': line,
                    'extras': extras
                }
    return pins


def parse_direct_requirements_from_lockfile(lockfile_path: str) -> dict:
    """Extract direct package requirements from a uv lockfile.

    A package is considered direct when its ``# via`` metadata includes
    ``-r ...packages.txt`` (supports both single-line and block-style formats).

    Args:
        lockfile_path: Path to resolved-versions.txt

    Returns:
        Dict mapping direct package name (lowercase) -> version.
    """
    direct_requirements = {}

    if not os.path.exists(lockfile_path):
        return direct_requirements

    current_pkg = None
    current_ver = None
    current_is_direct = False

    def finalize_current():
        if current_pkg and current_is_direct:
            direct_requirements[current_pkg] = current_ver

    with open(lockfile_path, "r") as f:
        for raw_line in f:
            line = raw_line.rstrip("\n")
            stripped = line.strip()

            if not stripped:
                continue

            # New package entry line: "name==version"
            if not line.startswith((" ", "\t")) and not stripped.startswith("#"):
                finalize_current()
                current_pkg = None
                current_ver = None
                current_is_direct = False

                match = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==([^\s#]+)$", stripped)
                if match:
                    current_pkg = match.group(1).lower()
                    current_ver = match.group(2)
                continue

            if not current_pkg:
                continue

            # Supports:
            #   "    # via -r docker/.../packages.txt"
            #   "    #   -r docker/.../packages.txt"
            via_match = re.match(r"^\s*#\s*(?:via\s+)?-r\s+(.+)$", line)
            if via_match:
                requirement_source = via_match.group(1).strip()
                if re.search(r"(^|[\\/])packages\.txt$", requirement_source):
                    current_is_direct = True

    finalize_current()
    return direct_requirements


def detect_package_set_changes(packages_file: str, lockfile_path: str) -> dict:
    """Detect package additions/removals between packages.txt and lockfile direct deps.

    This compares package *names only* (case-insensitive, extras stripped).
    Version-only edits for packages that exist in both files are intentionally ignored.

    Args:
        packages_file: Path to packages.txt
        lockfile_path: Path to resolved-versions.txt

    Returns:
        Dict with two keys:
            - "added": {package_name: current_version_or_None}
            - "removed": {package_name: lockfile_version_or_None}
    """
    current_pins = get_current_pyhc_pins(packages_file)

    def normalize_name(name: str) -> str:
        return re.sub(r"[-_.]+", "-", name).lower()

    current_by_norm = {normalize_name(name): name for name in current_pins}
    current_norm_names = set(current_by_norm.keys())

    # If lockfile doesn't exist, treat all current packages as added so pipeline runs.
    if not os.path.exists(lockfile_path):
        return {
            "added": {name: current_pins[name].get("version") for name in sorted(current_pins)},
            "removed": {},
        }

    lockfile_direct = parse_direct_requirements_from_lockfile(lockfile_path)
    lockfile_by_norm = {normalize_name(name): name for name in lockfile_direct}
    lockfile_norm_names = set(lockfile_by_norm.keys())

    added_norm = sorted(current_norm_names - lockfile_norm_names)
    removed_norm = sorted(lockfile_norm_names - current_norm_names)

    return {
        "added": {
            current_by_norm[norm_name]: current_pins[current_by_norm[norm_name]].get("version")
            for norm_name in added_norm
        },
        "removed": {
            lockfile_by_norm[norm_name]: lockfile_direct.get(lockfile_by_norm[norm_name])
            for norm_name in removed_norm
        },
    }


def update_packages_txt_with_pins(packages_file: str, new_versions: dict) -> None:
    """Update packages.txt with new version pins.

    Preserves comments, extras, ordering, and section structure.

    Args:
        packages_file: Path to packages.txt
        new_versions: Dict mapping package name → new version
    """
    # Normalize new_versions keys to lowercase for matching
    versions_lower = {k.lower(): v for k, v in new_versions.items()}

    with open(packages_file, 'r') as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        stripped = line.strip()

        # Preserve empty lines and comments as-is
        if not stripped or stripped.startswith('#'):
            new_lines.append(line)
            continue

        # Parse the package entry
        # Handle inline comments
        inline_comment = ''
        if '#' in stripped:
            parts = stripped.split('#', 1)
            pkg_part = parts[0].strip()
            inline_comment = '  # ' + parts[1].strip()
        else:
            pkg_part = stripped

        # Extract package name and extras
        if '==' in pkg_part:
            name_with_extras = pkg_part.split('==')[0]
        else:
            name_with_extras = pkg_part

        # Separate name from extras
        if '[' in name_with_extras:
            name = name_with_extras.split('[')[0]
            extras = '[' + name_with_extras.split('[')[1]
            if ']' not in extras:
                extras += ']'
        else:
            name = name_with_extras
            extras = ''

        # Look up new version
        name_lower = name.lower()
        if name_lower in versions_lower:
            new_version = versions_lower[name_lower]
            # Construct new line with version pin
            new_entry = f"{name}{extras}=={new_version}{inline_comment}\n"
            new_lines.append(new_entry)
        else:
            # Package not in new_versions dict, keep as-is
            new_lines.append(line)

    with open(packages_file, 'w') as f:
        f.writelines(new_lines)


def parse_constraints(constraints_file: str) -> dict:
    """Parse constraints.txt to extract version constraints.

    Supports all pip constraint operators: ==, !=, <, <=, >, >=, ~=
    and compound constraints like "pkg!=1.0,<2.0".

    Args:
        constraints_file: Path to constraints.txt

    Returns:
        Dict mapping package name (lowercase) → SpecifierSet object
    """
    constraints = {}

    if not os.path.exists(constraints_file):
        return constraints

    with open(constraints_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # Remove inline comments
            line = line.split('#')[0].strip()
            if not line:
                continue

            # Parse package name and specifier
            # Match package name (can include - and _), then version specifier
            match = re.match(r'^([a-zA-Z0-9_-]+)(.*)', line)
            if not match:
                print(f"Warning: Could not parse constraint line: {line}")
                continue

            name = match.group(1).lower()
            specifier_str = match.group(2).strip()

            if not specifier_str:
                # No version specifier, skip
                continue

            try:
                specifier = SpecifierSet(specifier_str)
                if name in constraints:
                    # Combine with existing constraints
                    constraints[name] = constraints[name] & specifier
                else:
                    constraints[name] = specifier
            except InvalidSpecifier as e:
                print(f"Warning: Invalid specifier '{specifier_str}' for {name}: {e}")
                continue

    return constraints


def auto_pin_packages_to_latest(packages_file: str, constraints_file: str = None) -> dict:
    """Update packages.txt with latest PyPI versions that satisfy constraints.

    For each package:
    - If no constraint exists, use the latest PyPI version
    - If latest version satisfies constraints, use it
    - If latest version doesn't satisfy constraints, find the highest version that does

    This ensures packages.txt always contains the latest allowable versions.

    Supports all constraint operators: ==, !=, <, <=, >, >=, ~=

    Args:
        packages_file: Path to packages.txt
        constraints_file: Optional path to constraints.txt

    Returns:
        Dict of changed packages: {pkg: (old_version, new_version)}

    Raises:
        RuntimeError: If any PyPI fetch fails or no valid version exists for a constrained package
    """
    # 0. Parse constraints to get version specifiers
    if constraints_file is None:
        constraints_file = os.path.join(os.path.dirname(packages_file), "constraints.txt")
    version_constraints = parse_constraints(constraints_file)
    if version_constraints:
        print(f"Loaded constraints: {dict((k, str(v)) for k, v in version_constraints.items())}")

    # 1. Get current pins (skips commented-out packages)
    old_pins = get_current_pyhc_pins(packages_file)

    # 2. Fetch latest versions (fails explicitly on error)
    packages = list(old_pins.keys())
    print(f"Fetching latest versions for {len(packages)} packages from PyPI...")
    latest_versions = fetch_all_latest_versions(packages)

    # 3. Check constraints and determine final versions
    final_versions = {}
    constrained_updates = []
    for pkg, latest_ver in latest_versions.items():
        constraint = version_constraints.get(pkg)
        if constraint is not None and latest_ver not in constraint:
            # Latest version doesn't satisfy constraint - find highest valid version
            print(f"  {pkg}: latest {latest_ver} blocked by '{constraint}', searching for valid version...")
            valid_ver = find_highest_satisfying_version(pkg, constraint)
            if valid_ver is None:
                raise RuntimeError(
                    f"No version of '{pkg}' satisfies constraint '{constraint}'. "
                    f"Latest version is {latest_ver}. Please update constraints.txt."
                )
            final_versions[pkg] = valid_ver
            constrained_updates.append(f"{pkg}: using {valid_ver} (latest {latest_ver} blocked by '{constraint}')")
        else:
            # Latest version satisfies constraints (or no constraint exists) - use it
            final_versions[pkg] = latest_ver

    if constrained_updates:
        print("Packages pinned to non-latest due to constraints:")
        for msg in constrained_updates:
            print(f"  {msg}")

    # 4. Calculate changes
    changes = {}
    for pkg, new_ver in final_versions.items():
        old_ver = old_pins.get(pkg, {}).get('version')
        if old_ver != new_ver:
            changes[pkg] = (old_ver, new_ver)

    # 5. Write updated packages.txt (preserves comments, extras, ordering)
    if changes:
        update_packages_txt_with_pins(packages_file, final_versions)
        print(f"Updated {len(changes)} package(s) in {packages_file}")
    else:
        print("All packages already at latest compatible versions")

    return changes
