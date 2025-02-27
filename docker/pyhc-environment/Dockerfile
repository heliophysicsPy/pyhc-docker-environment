# Use an official Anaconda runtime as a parent image
FROM continuumio/miniconda3

# Set the working directory in the container to /app
WORKDIR /app

# Update the packages in the base image and install the necessary compilers, then cleanup
RUN apt-get update && apt-get install -y gcc g++ gfortran ncurses-dev build-essential cmake libgl1-mesa-glx vim nano wget curl git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create the jovyan user (required for Binder)
RUN useradd -m -s /bin/bash -N -u 1000 jovyan

# Add the "contents" directory contents into the container at /app
ADD contents/ /app

# Configure CDF library and package data directories
RUN mv /app/cdf38_0-dist /usr/lib/ && \
    mkdir -p /root/.sunpy /root/heliopy/data /root/Geospacelab/Data /root/.spacepy/data

ENV CDF_BASE=/usr/lib/cdf38_0-dist
ENV CDF_LIB=$CDF_BASE/lib

# Create the conda environment using environment.yml and activate it, then cleanup
RUN conda env create -f /app/environment.yml && \
    echo ". /opt/conda/etc/profile.d/conda.sh && conda activate pyhc-all" > /etc/profile.d/init_conda.sh && \
    conda clean -afy

# Add environment's bin directory to PATH for global access to commands
ENV PATH /opt/conda/envs/pyhc-all/bin:$PATH

# Install PyHC packages with pip (Kamodo separately)
RUN pip install --no-cache-dir git+https://github.com/nasa/Kamodo.git && \
    pip install --use-pep517 --retries 5 --no-cache-dir -r /app/requirements.txt

# Cleanup environment.yml and requirements.txt after their use
RUN rm /app/environment.yml /app/requirements.txt

# Copy notebooks to jovyan's home directory and set permissions
RUN cp /app/import-test.ipynb /home/jovyan/import-test.ipynb && \
    cp /app/unit-tests.ipynb /home/jovyan/unit-tests.ipynb && \
    chown -R jovyan:users /home/jovyan && \
    chown -R jovyan:users /app

# Change ownership of the entire conda directory to allow package installation/modification
RUN chown -R jovyan:users /opt/conda && \
    chmod -R u+w /opt/conda

# Pre-build the wmm2015 and wmm2020 packages using Bash shell
RUN /bin/bash -c "source activate pyhc-all && \
    python -c 'import wmm2015' && \
    python -c 'import wmm2020'"

# Set the working directory to jovyan's home for Binder compatibility
WORKDIR /home/jovyan

# Make port 8888 available to the world outside this container
EXPOSE 8888

# Run Jupyter notebook when the container launches
CMD ["jupyter", "lab", "--ip='*'", "--port=8888", "--no-browser", "--allow-root"]
