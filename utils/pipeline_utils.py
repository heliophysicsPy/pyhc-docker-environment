"""
PyHC environment pipeline utility functions.

__author__ = "Shawn Polson"
"""


import os
import re
import requests


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


def strip_extras(package_name):
    # This regex removes any bracketed extras.
    return re.sub(r'\[.*?\]', '', package_name)


def check_for_package_updates(requirements_path, package_names, ignore_list=None):
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

    Returns:
        dict: A dictionary mapping package names to a dict with 'current_version' and 
              'latest_version' keys for packages that require updates. For newly introduced 
              packages, 'current_version' will be set to "Not Installed".
    """
    if ignore_list is None:
        ignore_list = []
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
    prepends the Kamodo Git URL (TODO: re-enable), and adds a comment at the end of the line.
    """
    # Read the contents of the file
    with open(requirements_file_path, 'r') as file:
        lines = file.readlines()

    # Iterate through the lines and comment out package
    for i, line in enumerate(lines):
        if line.strip().startswith(("kamodo", "kamodo==")):
            # lines[i] = f"git+https://github.com/nasa/Kamodo.git  # {line.strip()}  # gets installed from GitHub instead\n"  # Can't include Kamodo's git URL yet (it breaks pip install with conflict on pandas<2)
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
