# Use an official Anaconda runtime as a parent image
FROM continuumio/miniconda3

# Set the working directory in the container to /app
WORKDIR /app

# Update the packages in the base image and install the necessary compilers, then cleanup
RUN apt-get update && apt-get install -y gcc g++ gfortran ncurses-dev build-essential cmake wget unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Add the "contents" directory contents into the container at /app
ADD contents/ /app

# Unzip "executable-paper.zip" if it's present, else fail
RUN if [ -f "/app/executable-paper.zip" ]; then \
        unzip /app/executable-paper.zip -d /app && \
        rm /app/executable-paper.zip; \
        rm -rf /app/__MACOSX; \
    else \
        echo "ERROR: executable-paper.zip not found (note, this file is tracked by Git LFS)." >&2; \
        exit 1; \
    fi

# Configure CDF library and package data directories
RUN mv /app/executable-paper/dependencies/cdf38_0-dist /usr/lib/ && \
    mkdir -p /root/.sunpy /root/heliopy/data /root/Geospacelab/Data /root/.spacepy/data && \
    mv /app/executable-paper/pydata/spacepy/data/* /root/.spacepy/data/

ENV CDF_BASE=/usr/lib/cdf38_0-dist
ENV CDF_LIB=$CDF_BASE/lib

# Create the conda environment using environment.yml and activate it, then cleanup
RUN conda env create -f /app/environment.yml && \
    echo "source activate pyhc-all" > ~/.bashrc && \
    conda clean -afy

ENV PATH /opt/conda/envs/pyhc-all/bin:$PATH

# Install PyHC packages with pip (SpacePy, Kamodo, and pySPEDAS separately)
RUN pip install --no-cache-dir numpy==1.24.3 && \
    pip install --no-cache-dir spacepy --no-build-isolation && \
    pip install --use-pep517 --retries 5 --no-cache-dir -r /app/requirements.txt && \
    pip install --no-cache-dir git+https://github.com/nasa/Kamodo.git && \
    pip install --no-cache-dir pytplot-mpl-temp && \
    pip install --no-cache-dir pyspedas

# Cleanup environment.yml and requirements.txt after their use
RUN rm /app/environment.yml /app/requirements.txt

# Make port 8888 available to the world outside this container
EXPOSE 8888

# Run Jupyter notebook when the container launches
CMD ["jupyter", "lab", "--ip='*'", "--port=8888", "--no-browser", "--allow-root"]
