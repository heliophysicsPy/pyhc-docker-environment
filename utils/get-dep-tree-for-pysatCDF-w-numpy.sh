#!/bin/bash

set -euxo pipefail

PACKAGE=$1

# Create a new virtual environment (consider python version)
TEMP_ENV_NAME="temp_env_for_$PACKAGE"
python3.9 -m venv $TEMP_ENV_NAME

# Activate the virtual environment
source $TEMP_ENV_NAME/bin/activate

# Upgrade pip and Install numpy
pip install --upgrade pip
pip install numpy==1.24.3 pysatCDF

# # Clone pysatCDF from GitHub
# git clone https://github.com/rstoneback/pysatCDF.git
# cd pysatCDF

# # Install pysatCDF
# python setup.py install
# INSTALL_STATUS=$?

# # Move out of pysatCDF directory
# cd ..

# # Delete the pysatCDF directory
# rm -rf pysatCDF

# # Check if the installation was successful
# if [ $INSTALL_STATUS -ne 0 ]; then
#     echo "Error: Installation of $PACKAGE failed."
#     deactivate
#     rm -rf $TEMP_ENV_NAME/
#     exit 1
# fi

# Install pipdeptree
pip install pipdeptree==2.3.3

# Get dependency tree (Only this output will be displayed)
PIPTREE_OUTPUT=$(pipdeptree -p pysatCDF)

# Deactivate and remove the virtual environment
deactivate
rm -rf $TEMP_ENV_NAME/

# Output the dependency tree
echo "$PIPTREE_OUTPUT"

exit 0
