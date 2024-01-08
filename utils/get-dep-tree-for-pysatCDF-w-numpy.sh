#!/bin/bash

#PACKAGE=$1
#
## Create a new virtual environment (carefully consider python version?)
#TEMP_ENV_NAME="temp_env_for_$PACKAGE"
#python3.9 -m venv $TEMP_ENV_NAME
#
## Activate the virtual environment
#source $TEMP_ENV_NAME/bin/activate
#
## Upgrade pip and Install numpy
#pip install --upgrade pip
#pip install wheel
#pip install numpy==1.24.3
#
## Check numpy installation
#NUMPY_VERSION=$("$TEMP_ENV_NAME/bin/python" -c "import numpy; print(numpy.__version__)")
#echo "Numpy Version: $NUMPY_VERSION"
#
## Install the specified package
#"$TEMP_ENV_NAME/bin/pip" install --use-pep517 --no-build-isolation $PACKAGE
#if [ $? -ne 0 ]; then
#    echo "Error: Installation of $PACKAGE failed."
#    deactivate
#    rm -rf $TEMP_ENV_NAME/
#    exit 0
#fi
#
## Install pipdeptree and get dependency tree
#pip install pipdeptree
#PIPTREE_OUTPUT=$(pipdeptree -p $PACKAGE)
#
## Deactivate and remove the virtual environment
#deactivate
#rm -rf $TEMP_ENV_NAME/
#
## Output the dependency tree
#echo "Dependency tree for $PACKAGE:"
#echo "$PIPTREE_OUTPUT"
#
#exit 0

##!/bin/bash
#
#PACKAGE=$1
#
## Create a new virtual environment (consider python version)
#TEMP_ENV_NAME="temp_env_for_$PACKAGE"
#python3.9 -m venv $TEMP_ENV_NAME
#
## Activate the virtual environment
#source $TEMP_ENV_NAME/bin/activate
#
## Upgrade pip and Install numpy
#pip install --upgrade pip
#pip install numpy
#
## Check numpy installation
## NUMPY_VERSION=$(python -c "import numpy; print(numpy.__version__)")
## echo "Numpy Version: $NUMPY_VERSION"
#
## Clone pysatCDF from GitHub
#git clone https://github.com/rstoneback/pysatCDF.git
#cd pysatCDF
#
## Install pysatCDF
#python setup.py install
#INSTALL_STATUS=$?
#
## Move out of pysatCDF directory
#cd ..
#
## Delete the pysatCDF directory
#rm -rf pysatCDF
#
## Check if the installation was successful
#if [ $INSTALL_STATUS -ne 0 ]; then
##    echo "Error: Installation of $PACKAGE failed."
#    deactivate
#    rm -rf $TEMP_ENV_NAME/
#    exit 1
#fi
#
## Install pipdeptree and get dependency tree
#pip install pipdeptree
#PIPTREE_OUTPUT=$(pipdeptree -p pysatCDF)
#
## Deactivate and remove the virtual environment
#deactivate
#rm -rf $TEMP_ENV_NAME/
#
## Output the dependency tree
##echo "Dependency tree for pysatCDF:"
#echo "$PIPTREE_OUTPUT"
#
#exit 0

#!/bin/bash

PACKAGE=$1

# Create a new virtual environment (consider python version)
TEMP_ENV_NAME="temp_env_for_$PACKAGE"
python3.9 -m venv $TEMP_ENV_NAME

# Activate the virtual environment
source $TEMP_ENV_NAME/bin/activate

# Upgrade pip and Install numpy, suppressing output
pip install --upgrade pip > /dev/null 2>&1
pip install numpy > /dev/null 2>&1

# Clone pysatCDF from GitHub, suppressing output
git clone https://github.com/rstoneback/pysatCDF.git > /dev/null 2>&1
cd pysatCDF

# Install pysatCDF, suppressing output
python setup.py install > /dev/null 2>&1
INSTALL_STATUS=$?

# Move out of pysatCDF directory
cd ..

# Delete the pysatCDF directory, suppressing output
rm -rf pysatCDF > /dev/null 2>&1

# Check if the installation was successful
if [ $INSTALL_STATUS -ne 0 ]; then
    echo "Error: Installation of $PACKAGE failed."
    deactivate
    rm -rf $TEMP_ENV_NAME/
    exit 1
fi

# Install pipdeptree, suppressing output
pip install pipdeptree > /dev/null 2>&1

# Get dependency tree (Only this output will be displayed)
PIPTREE_OUTPUT=$(pipdeptree -p pysatCDF)

# Deactivate and remove the virtual environment, suppressing output
deactivate > /dev/null 2>&1
rm -rf $TEMP_ENV_NAME/ > /dev/null 2>&1

# Output the dependency tree
echo "$PIPTREE_OUTPUT"

exit 0
