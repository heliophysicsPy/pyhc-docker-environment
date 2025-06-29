#!/bin/bash

PACKAGE=$1
BASE_PACKAGE=$(echo "$PACKAGE" | sed 's/\[.*\]//')  # remove bracketed extras
BASE_PACKAGE=$(echo "$BASE_PACKAGE" | sed 's/==.*//')  # remove ==version

# Create a new virtual environment
TEMP_ENV_NAME="temp_env_for_$PACKAGE"
python3 -m venv $TEMP_ENV_NAME

# Activate the virtual environment
source $TEMP_ENV_NAME/bin/activate

# Install the given package and store its pipdeptree output
PIP_INSTALL_OUTPUT_0=$(pip install wheel)
PIP_INSTALL_OUTPUT_1=$(pip install --use-pep517 $PACKAGE)  # note: added `--use-pep517` June 24, 2025 because some older packages started failing with a dot/underscore clash setuptools bug 
PIP_INSTALL_OUTPUT_2=$(pip install -q pipdeptree==2.3.3)

# Remove '==<version' from $PACKAGE if given (unnecessary now that we pass $BASE_PACKAGE to pipdeptree)
PACKAGE=$(echo "$PACKAGE" | sed 's/==.*//')
PIPTREE_OUTPUT=$(pipdeptree -p $BASE_PACKAGE)

# Deactivate the virtual environment
deactivate

# Delete the virtual environment
rm -rf $TEMP_ENV_NAME/

# Return the pipdeptree output
# exit 0
echo "$PIPTREE_OUTPUT"
