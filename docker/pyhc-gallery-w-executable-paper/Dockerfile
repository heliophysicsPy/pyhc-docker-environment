# Use an official Anaconda runtime as a parent image
FROM continuumio/miniconda3

# Set the working directory in the container to /app
WORKDIR /app

# Update the packages in the base image and install the necessary compilers
RUN apt-get update && apt-get install -y gcc g++ gfortran ncurses-dev build-essential cmake wget unzip

# Add the "contents" directory contents into the container at /app
ADD contents/ /app

# Check for "executable-paper" directory and download if not present using wget
# (https://drive.google.com/file/d/1Zw5oDCXBxZlwU_BLqeAPflUzXKJGgtzp/view?usp=sharing)
RUN if [ ! -d "/app/executable-paper" ]; then \
        wget --no-check-certificate --save-cookies cookies.txt --keep-session-cookies --no-verbose -O /dev/null 'https://drive.google.com/uc?export=download&id=1Zw5oDCXBxZlwU_BLqeAPflUzXKJGgtzp' && \
        wget --load-cookies cookies.txt --no-check-certificate --no-verbose 'https://drive.google.com/uc?export=download&confirm='$(wget --quiet --save-cookies cookies.txt --keep-session-cookies --no-verbose --output-document - 'https://drive.google.com/uc?export=download&id=1Zw5oDCXBxZlwU_BLqeAPflUzXKJGgtzp' | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')'&id=1Zw5oDCXBxZlwU_BLqeAPflUzXKJGgtzp' -O executable-paper.zip && \
        unzip executable-paper.zip -d /app && \
        rm executable-paper.zip && \
        rm cookies.txt; \
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
