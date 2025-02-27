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
RUN apt-get update && apt-get install -y build-essential libhdf5-dev libnetcdf-dev capnproto libcapnp-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Tell the system to use the system C compiler
ENV CC=/usr/bin/cc

# Install PyHC packages with pip (Kamodo separately; fails to resolve when included in requirements.txt because it needs pandas<2 while we use pandas>2)
RUN pip install --no-cache-dir git+https://github.com/nasa/Kamodo.git && \
    pip install --use-pep517 --retries 5 --no-cache-dir -r /app/requirements.txt

# Ensure SQLite is installed correctly (TODO: try removing this to see if specifying better sqlite/libsqlite versions in environment.yml fixed the issue!) 
# RUN mamba install -y libsqlite --force-reinstall

# Configure CDF library and package data directories
RUN mv /app/cdf38_0-dist /usr/lib/ && \
    mkdir -p /root/.sunpy /root/heliopy/data /root/Geospacelab/Data /root/.spacepy/data

ENV CDF_BASE=/usr/lib/cdf38_0-dist
ENV CDF_LIB=$CDF_BASE/lib

# Install Message Of The Day (motd)
RUN echo "cat /etc/motd" > /etc/profile.d/show_motd.sh
COPY --chown=1000:1000 motd /etc/
RUN chmod 644 /etc/motd

# Copy notebooks and README to jovyan's home directory
RUN mkdir -p /home/jovyan/notebooks && \
    if [ -d "/app/notebooks" ]; then \
        cp -r /app/notebooks/* /home/jovyan/notebooks/; \
    fi && \
    if [ -f "/app/README.md" ]; then \
        cp /app/README.md /home/jovyan/; \
    fi

# Cleanup environment files after their use
RUN rm -rf /app/environment.yml /app/requirements.txt /app/apt.txt /app/jupyter_notebook_config.py /app/motd /app/start /app/Dockerfile /app/contents

RUN rm -rf /home/jovyan/environment.yml /home/jovyan/requirements.txt /home/jovyan/apt.txt /home/jovyan/jupyter_notebook_config.py /home/jovyan/motd /home/jovyan/start /home/jovyan/Dockerfile /home/jovyan/contents

# Set comprehensive permissions to allow package installation/modification (note: this recursive permission setting can take a long time... ~2 mins in GitHub Actions)
RUN chown -R jovyan:users /app && \
    chown -R jovyan:users /home/jovyan && \
    chmod -R u+w /home/jovyan && \
    chown -R jovyan:users /srv/conda && \
    chmod -R u+w /srv/conda

WORKDIR /home/jovyan

# Make port 8888 available to the world outside this container
EXPOSE 8888

# Run Jupyter notebook when the container launches
CMD ["jupyter", "lab", "--ip='*'", "--port=8888", "--no-browser", "--allow-root"]
