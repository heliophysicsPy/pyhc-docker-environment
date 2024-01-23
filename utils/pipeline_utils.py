"""
PyHC environment pipeline utility functions.

__author__ = "Shawn Polson"
"""


import os
import re
import requests
import shutil


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


def check_for_package_updates(requirements_path, package_names, ignore_list=None):
    """
    Check if the packages in the requirements.txt file are up-to-date with PyPI.
    """
    if ignore_list is None:
        ignore_list = []
    updates_required = {}

    with open(requirements_path, 'r') as file:
        requirements = file.readlines()

    for package in package_names:
        # Strip any version specifier and fetch the package name
        package_name = package.split('==')[0].strip()

        if package_name in ignore_list:
            continue

        # Extract the current version from requirements.txt
        current_version = None
        for line in requirements:
            if package_name.lower() in line.lower():
                match = re.search(r'==(.+?)(\s*#|$)', line)
                if match:
                    current_version = match.group(1).strip()
                break

        # Fetch the latest version from PyPI
        latest_version = fetch_latest_version_from_pypi(package_name)

        if latest_version and current_version and latest_version != current_version:
            updates_required[package_name] = {'current_version': current_version, 'latest_version': latest_version}

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


def get_dockerfile_template_pyhc_environment():
    return """
    
    """


def get_dockerfile_template_pyhc_gallery_w_executable_paper():
    # TODO: Need to intelligently determine numpy version (don't hardcode 1.24.3) (will this work? `pip install numpy>=1.23.0,<1.27,!=1.15.0`)
    return """# Use an official Anaconda runtime as a parent image
FROM continuumio/miniconda3

# Set the working directory in the container to /app
WORKDIR /app

# Update the packages in the base image and install the necessary compilers
RUN apt-get update && apt-get install -y gcc g++ gfortran ncurses-dev build-essential cmake wget unzip

# Add the "contents" directory contents into the container at /app
ADD contents/ /app

# Check for "executable-paper" directory and download if not present
RUN if [ ! -d "/app/executable-paper" ]; then \
        wget --no-check-certificate 'https://drive.google.com/uc?export=download&id=1Zw5oDCXBxZlwU_BLqeAPflUzXKJGgtzp' -O executable-paper.zip && \
        unzip executable-paper.zip -d /app && \
        rm executable-paper.zip; \
    fi

# Configure CDF library
# `executable-paper` dir: https://drive.google.com/file/d/1Zw5oDCXBxZlwU_BLqeAPflUzXKJGgtzp/view?usp=sharing
RUN mv /app/executable-paper/dependencies/cdf38_0-dist /usr/lib/
ENV CDF_BASE=/usr/lib/cdf38_0-dist
ENV CDF_LIB=$CDF_BASE/lib

# Configure package data directories
RUN mkdir -p /root/.sunpy
RUN mkdir -p /root/heliopy/data
RUN mkdir -p /root/Geospacelab/Data
RUN mkdir -p /root/.spacepy/data
RUN mv /app/executable-paper/pydata/spacepy/data/* /root/.spacepy/data/

# Create the conda environment using environment.yml
RUN conda env create -f /app/environment.yml

# Activate the created environment
RUN echo "source activate pyhc-all" > ~/.bashrc
ENV PATH /opt/conda/envs/pyhc-all/bin:$PATH

# Install additional packages with pip (SpacePy first)
RUN pip install --no-cache-dir numpy==1.24.3
RUN pip install --no-cache-dir spacepy --no-build-isolation
RUN pip install --use-pep517 --retries 5 --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir git+https://github.com/nasa/Kamodo.git
RUN pip install --no-cache-dir pytplot-mpl-temp
RUN pip install --no-cache-dir pyspedas

# Delete cruft
RUN rm /app/environment.yml
RUN rm /app/requirements.txt

# Make port 8888 available to the world outside this container
EXPOSE 8888

# Run Jupyter notebook when the container launches
CMD ["jupyter", "lab", "--ip='*'", "--port=8888", "--no-browser", "--allow-root"]
"""


def replace_requirements(source_file_path='requirements.txt', destination_file_path='docker/pyhc-gallery-w-executable-paper/contents/requirements.txt'):
    # Use shutil to copy the contents from the source to the destination
    shutil.copyfile(source_file_path, destination_file_path)


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

    # Iterate through the lines and comment out numpy and spacepy
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

    # Iterate through the lines and comment out numpy and spacepy
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

    # Iterate through the lines and comment out numpy and spacepy
    for i, line in enumerate(lines):
        if 'pyspedas' in line or 'pytplot' in line or 'pytplot-mpl-temp' in line:
            lines[i] = f"# {line.strip()}  # gets installed last in the Dockerfile\n"

    # Write the modified contents back to the file
    with open(requirements_file_path, 'w') as file:
        file.writelines(lines)
