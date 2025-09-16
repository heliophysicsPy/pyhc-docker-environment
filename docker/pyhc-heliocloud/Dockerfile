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

# Extract notebooks from tar archive and copy Welcome.ipynb to user's home directory (default: /home/jovyan)
RUN mkdir -p /home/$NB_USER/notebooks && \
    if [ -f "/app/notebooks.tar.gz" ]; then \
        tar -xzf /app/notebooks.tar.gz -C /home/$NB_USER/notebooks; \
    fi && \
    if [ -f "/app/Welcome.ipynb" ]; then \
        cp /app/Welcome.ipynb /home/$NB_USER/; \
    fi

# Cleanup environment files after their use
RUN rm -rf /app/environment.yml /app/conda-lock.yml /app/requirements.txt /app/apt.txt /app/jupyter_notebook_config.py /app/motd /app/start /app/Dockerfile /app/contents

RUN rm -rf /home/$NB_USER/environment.yml /home/$NB_USER/conda-lock.yml /home/$NB_USER/requirements.txt /home/$NB_USER/apt.txt /home/$NB_USER/jupyter_notebook_config.py /home/$NB_USER/motd /home/$NB_USER/start /home/$NB_USER/Dockerfile /home/$NB_USER/contents

# Set comprehensive permissions to allow package installation/modification (note: this recursive permission setting can take a long time... ~2 mins in GitHub Actions)
RUN chown -R $NB_USER:users /app && \
    chown -R $NB_USER:users /home/$NB_USER && \
    chmod -R u+w /home/$NB_USER && \
    chown -R $NB_USER:users /srv/conda && \
    chmod -R u+w /srv/conda

WORKDIR /home/$NB_USER

# Make port 8888 available to the world outside this container
EXPOSE 8888

# Run Jupyter notebook when the container launches
CMD ["jupyter", "lab", "--ip='*'", "--port=8888", "--no-browser", "--allow-root"]
