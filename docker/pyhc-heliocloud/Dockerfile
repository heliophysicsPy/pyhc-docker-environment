# Use an official Anaconda runtime as a parent image
# FROM continuumio/miniconda3  # What PyHC Environment used; HelioCloud uses Pangeo instead
ARG PANGEO_BASE_IMAGE_TAG=2024.01.15
FROM pangeo/base-image:${PANGEO_BASE_IMAGE_TAG}

# Switch to root so we can run apt-get etc.
USER root

# Set the working directory in the container to /app
WORKDIR /app

# Copy the "contents" directory contents into the container at /app
COPY contents/ /app

# Update the packages in the base image and install the necessary compilers, then cleanup
RUN apt-get update && apt-get install -y gcc g++ gfortran ncurses-dev build-essential cmake libgl1-mesa-glx libhdf5-dev libnetcdf-dev capnproto libcapnp-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install apt.txt packages (TODO: delete; should be handled by pangeo's ONBUILD)
# RUN echo "Found apt.txt; installing packages..." && \
#     apt-get update -qq && \
#     xargs -a /app/apt.txt apt-get install -y && \
#     apt-get clean && \
#     rm -rf /var/lib/apt/lists/*

# Configure CDF library and package data directories
RUN mv /app/cdf38_0-dist /usr/lib/ && \
    mkdir -p /root/.sunpy /root/heliopy/data /root/Geospacelab/Data /root/.spacepy/data

ENV CDF_BASE=/usr/lib/cdf38_0-dist
ENV CDF_LIB=$CDF_BASE/lib

# Install Message Of The Day (motd)
RUN echo "cat /etc/motd" > /etc/profile.d/show_motd.sh
COPY --chown=1000:1000 motd /etc/
RUN chmod 644 /etc/motd

# Copy jupyter_notebook_config.py to /etc/jupyter (TODO: delete; should be handled by pangeo's ONBUILD)
# RUN echo "Found jupyter_notebook_config.py; copying to /etc/jupyter/..." && \
#     mkdir -p /etc/jupyter && \
#     cp /app/jupyter_notebook_config.py /etc/jupyter/

# Create the conda environment (using mamba) from environment.yml and activate it, then cleanup (TODO: delete; should be handled by pangeo's ONBUILD)
# ENV MAMBA_ROOT_PREFIX=/opt/conda

# RUN mamba env create -f /app/environment.yml \
#     && echo "source activate pyhc-all" > ~/.bashrc \
#     && conda clean -afy

# ENV PATH /opt/conda/envs/pyhc-all/bin:$PATH

# Install PyHC packages with pip (Kamodo separately) - explicitly use the right environment by activating it (TODO: delete; should be handled by pangeo's ONBUILD)
# SHELL ["/bin/bash", "-c"]
# RUN source activate pyhc-all && \
#     pip install --no-cache-dir git+https://github.com/nasa/Kamodo.git && \
#     pip install --use-pep517 --retries 5 --no-cache-dir -r /app/requirements.txt

# Cleanup environment files after their use
# RUN rm /app/environment.yml /app/requirements.txt /app/apt.txt /app/jupyter_notebook_config.py

# Change ownership of home dir and Python env using dynamic Python version (note: this recursive permission setting can apparently take a long time...)
RUN /bin/bash -c "source activate \$CONDA_ENV && \
    PYVERSION=\$(python -c 'import sys; print(\"python%d.%d\" % sys.version_info[:2])') && \
    echo \"Detected PYVERSION=\$PYVERSION\" && \
    chown -R jovyan:users /home/jovyan && \
    chmod -R u+w /home/jovyan && \
    chown -R jovyan:users /srv/conda/envs/\$CONDA_ENV/lib/\$PYVERSION/site-packages && \
    chmod -R u+w /srv/conda/envs/\$CONDA_ENV/lib/\$PYVERSION/site-packages"

# Make port 8888 available to the world outside this container
EXPOSE 8888

# Run Jupyter notebook when the container launches
CMD ["jupyter", "lab", "--ip='*'", "--port=8888", "--no-browser", "--allow-root"]
