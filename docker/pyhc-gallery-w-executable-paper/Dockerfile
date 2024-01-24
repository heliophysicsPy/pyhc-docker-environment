# Use an official Anaconda runtime as a parent image
FROM continuumio/miniconda3

# Set the working directory in the container to /app
WORKDIR /app

# Update the packages in the base image and install the necessary compilers
RUN apt-get update && apt-get install -y gcc g++ gfortran ncurses-dev build-essential cmake wget unzip

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

# Configure CDF library
RUN mv /app/executable-paper/dependencies/cdf38_0-dist /usr/lib/
ENV CDF_BASE=/usr/lib/cdf38_0-dist
ENV CDF_LIB=$CDF_BASE/lib

# Configure package data directories
RUN mkdir -p /root/.sunpy
RUN mkdir -p /root/heliopy/data
RUN mkdir -p /root/Geospacelab/Data
RUN mkdir -p /root/.spacepy/data
RUN mv /app/executable-paper/pydata/spacepy/data/* /root/.spacepy/data/

# Create the conda environment using environment.yml
RUN conda env create -f /app/environment.yml

# Activate the created environment
RUN echo "source activate pyhc-all" > ~/.bashrc
ENV PATH /opt/conda/envs/pyhc-all/bin:$PATH

# Install additional packages with pip (SpacePy first)
RUN pip install --no-cache-dir numpy==1.24.3
RUN pip install --no-cache-dir spacepy --no-build-isolation
RUN pip install --use-pep517 --retries 5 --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir git+https://github.com/nasa/Kamodo.git
RUN pip install --no-cache-dir pytplot-mpl-temp
RUN pip install --no-cache-dir pyspedas

# Delete cruft
RUN rm /app/environment.yml
RUN rm /app/requirements.txt

# Make port 8888 available to the world outside this container
EXPOSE 8888

# Run Jupyter notebook when the container launches
CMD ["jupyter", "lab", "--ip='*'", "--port=8888", "--no-browser", "--allow-root"]
