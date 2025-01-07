#!/bin/bash

PACKAGE=$1
BASE_PACKAGE=$(echo "$PACKAGE" | sed 's/\[.*\]//')

# Create a new virtual environment (carefully consider python version?)
TEMP_ENV_NAME="temp_env_for_$PACKAGE"
python3.10 -m venv $TEMP_ENV_NAME

# Activate the virtual environment
source $TEMP_ENV_NAME/bin/activate

# Install the given package and store its pipdeptree output
PIP_INSTALL_OUTPUT_0=$(pip install wheel)
PIP_INSTALL_OUTPUT_1=$(pip install $PACKAGE)
PIP_INSTALL_OUTPUT_2=$(pip install -q pipdeptree==2.3.3)

# Remove '==<version' from $PACKAGE if given
PACKAGE=$(echo "$PACKAGE" | sed 's/==.*//')
PIPTREE_OUTPUT=$(pipdeptree -p $BASE_PACKAGE)

# Deactivate the virtual environment
deactivate

# Delete the virtual environment
rm -rf $TEMP_ENV_NAME/

# Return the pipdeptree output
# exit 0
echo "$PIPTREE_OUTPUT"
