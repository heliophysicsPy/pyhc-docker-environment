# Use an official Anaconda runtime as a parent image
FROM continuumio/miniconda3

# Set the working directory in the container to /app
WORKDIR /app

# Update the packages in the base image and install the necessary compilers, then cleanup
RUN apt-get update && apt-get install -y gcc g++ gfortran ncurses-dev build-essential cmake libgl1-mesa-glx \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Add the "contents" directory contents into the container at /app
ADD contents/ /app

# Configure CDF library and package data directories
RUN mv /app/cdf38_0-dist /usr/lib/ && \
    mkdir -p /root/.sunpy /root/heliopy/data /root/Geospacelab/Data /root/.spacepy/data

ENV CDF_BASE=/usr/lib/cdf38_0-dist
ENV CDF_LIB=$CDF_BASE/lib

# Create the conda environment using environment.yml and activate it
RUN conda env create -f /app/environment.yml && \
    echo "source activate pyhc-all" > ~/.bashrc && \
    conda clean -afy

ENV PATH /opt/conda/envs/pyhc-all/bin:$PATH

# Install PyHC packages with pip (Kamodo separately)
RUN pip install --use-pep517 --retries 5 --no-cache-dir -r /app/requirements.txt && \
    pip install --no-cache-dir git+https://github.com/nasa/Kamodo.git

# Cleanup environment.yml and requirements.txt after their use
RUN rm /app/environment.yml /app/requirements.txt

# Make port 8888 available to the world outside this container
EXPOSE 8888

# Run Jupyter notebook when the container launches
CMD ["jupyter", "lab", "--ip='*'", "--port=8888", "--no-browser", "--allow-root"]
