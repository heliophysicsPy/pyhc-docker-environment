"""
Main script to generate Docker images of Python environments with the latest versions of all published PyHC packages.

Pipeline steps:
  1. Generate dependency conflict spreadsheet
  2. If no conflicts found, create requirements.txt file from spreadsheet
  3. Comment out numpy and SpacePy (and pysatcdf, kamodo, and pySPEDAS/PyTplot) in requirements.txt (they'll be installed separately)
  4. Update the requirements.txt files in all Docker images' `contents/` folders

  In GitHub Actions:
    5. Build the Docker images from Dockerfiles (pyhc-environment, pyhc-gallery, pyhc-gallery-w-executable-paper)
    6. Push those Docker images to Docker Hub with tags like :vYYYY.mm.dd
    7. Update source files in GitHub

__author__ = "Shawn Polson"
"""


import os
import sys
from datetime import datetime
from utils.generate_dependency_table import *
from utils.pipeline_utils import *


def pipeline_should_run(packages_to_ignore=['cdflib', 'geospacelab', 'heliopy', 'pytplot', 'plasmapy', 'aiapy']):
    """
    Step 1: Check if any PyHC packages have released updates. If not, the pipeline doesn't need to run (return False).
    """
    requirements_file_path = os.path.join(os.path.dirname(__file__), 'docker', 'pyhc-environment', 'contents', 'requirements.txt')
    all_packages = get_core_pyhc_packages() + get_other_pyhc_packages()
    updates = check_for_package_updates(requirements_file_path, all_packages, packages_to_ignore)
    if updates:
        print("Updates required for the following PyHC packages:", flush=True)
        for package, versions in updates.items():
            print(
                f"{package}: Current version {versions['current_version']}, Latest version {versions['latest_version']}",
                flush=True)
        return True
    else:
        print("All PyHC packages are up to date.", flush=True)
        return False


if __name__ == '__main__':
    if not pipeline_should_run():
        print("Pipeline will not run.", flush=True)
        print("::set-output name=should_run::false", flush=True)  # Tells GitHub Actions not to continue
    else:

        # Generate dependency conflict spreadsheet
        filename = f"PyHC-Dependency-Table-{datetime.now().strftime('%Y-%m-%d-%H-%M')}.xlsx"
        spreadsheet_folder = "spreadsheets"
        if not os.path.exists(spreadsheet_folder):
            os.makedirs(spreadsheet_folder)
        spreadsheet_path = os.path.join(spreadsheet_folder, filename)

        all_packages = get_core_pyhc_packages() + get_other_pyhc_packages() + get_supplementary_packages()
        table_data = generate_dependency_table_data(all_packages)

        table = excel_spreadsheet_from_table_data(table_data)
        table.save(spreadsheet_path)

        try:
            requirements_txt = spreadsheet_to_requirements_file(spreadsheet_path)

            # Path to the docker folder in the repository
            docker_folder_path = os.path.join(os.path.dirname(__file__), 'docker')

            # Get Docker image names and update requirements.txt for each
            docker_image_names = get_docker_image_names(docker_folder_path)
            for image_name in docker_image_names:
                docker_requirements_path = os.path.join(docker_folder_path, image_name, 'contents', 'requirements.txt')
                with open(docker_requirements_path, 'w') as file:
                    file.write(requirements_txt)

                # Comment out specific packages
                comment_out_numpy_and_spacepy(docker_requirements_path)
                comment_out_pysatcdf(docker_requirements_path)
                comment_out_kamodo(docker_requirements_path)
                comment_out_pyspedas_pytplot_pytplot_mpl_temp(docker_requirements_path)

        except ValueError as e:
            raise e

        print("::set-output name=should_run::true", flush=True)
        print("Updated all Docker images' requirements.", flush=True)
