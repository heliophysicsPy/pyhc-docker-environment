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
# (forcibly install opencv-python 4.10.0.82 to avoid numpy 2 conflict—numpy 2 required for Python >=3.9 starting v4.10.0.84)
PIP_INSTALL_OUTPUT_numpy=$(pip install numpy==1.26.4)
PIP_INSTALL_OUTPUT_opencv=$(pip install opencv-python==4.10.0.82)
PIP_INSTALL_OUTPUT_0=$(pip install wheel)
PIP_INSTALL_OUTPUT_1=$(pip install $PACKAGE)
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
