"""
Main script to generate Docker images of Python environments with the latest versions of all published PyHC packages.

Steps:
  1. Generate dependency conflict spreadsheet
  2. If no conflicts found, create requirements.txt file from spreadsheet
  3. Comment out numpy and SpacePy (and pysatcdf, kamodo, and pySPEDAS/PyTplot) in requirements.txt (they'll be installed separately)
  4. Update the requirements.txt files.
  5. Create 3 Docker images from Dockerfiles (pyhc-environment, pyhc-gallery, pyhc-gallery-w-executable-paper)
  6. If the right ("push"?) flag is set, push those Docker images to Docker Hub with tags like :vYYYY.mm.dd; then Update source files in GitHub

__author__ = "Shawn Polson"
"""


import os
from datetime import datetime
import sys

# Add the parent directory to sys.path to make the generate-dependency-table module available
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.generate_dependency_table import *
from utils.pipeline_utils import *


if __name__ == '__main__':
    filename = f"PyHC-Dependency-Table-{datetime.now().strftime('%m-%d-%Y-%H-%M')}.xlsx"
    spreadsheet_folder = "spreadsheets"
    if not os.path.exists(spreadsheet_folder):
        os.makedirs(spreadsheet_folder)
    spreadsheet_path = os.path.join(spreadsheet_folder, filename)

    all_packages = get_core_pyhc_packages() + get_other_pyhc_packages() + get_supplementary_packages()
    table_data = generate_dependency_table_data(all_packages)

    table = excel_spreadsheet_from_table_data(table_data)
    table.save(spreadsheet_path)

    try:
        # # TODO: DELETE BELOW LINE
        # spreadsheet_path = "spreadsheets/PyHC-Dependency-Table-01-04-2024-17-23.xlsx"

        requirements_file_path = "requirements.txt"
        requirements_txt = spreadsheet_to_requirements_file(spreadsheet_path)
        with open(requirements_file_path, 'w') as file:
            file.write(requirements_txt)
        comment_out_numpy_and_spacepy(requirements_file_path)
        comment_out_pysatcdf(requirements_file_path)
        comment_out_kamodo(requirements_file_path)
        comment_out_pyspedas_pytplot_pytplot_mpl_temp(requirements_file_path)
        replace_requirements(source_file_path=requirements_file_path,
                             destination_file_path='docker/pyhc-gallery-w-executable-paper/contents/requirements.txt')
    except ValueError as e:
        raise e

    # TODO: Push to GitHub?
    # TODO: At this point we can try building docker images

    print("Done.")
