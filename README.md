# PyHC Environment Pipeline

## Overview
The PyHC Environment Pipeline automates the creation of Docker images with Python environments that come pre-loaded with the latest versions of all published PyHC ([Python in Heliophysics Community](https://pyhc.org/projects)) packages. The GitHub Actions workflow rebuilds and pushes the Docker images to [Docker Hub](https://hub.docker.com/u/spolson) each time a PyHC package releases a new update. It also keeps the source files in this repo in-sync with what's in Docker Hub.  

## Features
- **Automated Docker Builds**: Automatically builds Docker images with updated Python environments using GitHub Actions.
- **Daily Updates**: Runs daily to check for and include the latest versions of PyHC packages.
- **Docker Hub Hosting**: Docker images are readily available on Docker Hub for easy access and deployment.
- **Dependency Spreadsheet**: An intermediate step of the pipeline is to generate an Excel spreadsheet showing a matrix of allowed version range requirements.

## Docker Images
The pipeline creates and maintains the following Docker images:
- [pyhc-environment](https://hub.docker.com/r/spolson/pyhc-environment) (the base env)
- [pyhc-gallery](https://hub.docker.com/r/spolson/pyhc-gallery) (base env with notebooks from PyHC's gallery)
- [pyhc-gallery-w-executable-paper](https://hub.docker.com/r/spolson/pyhc-gallery-w-executable-paper) (base env with notebooks from PyHC's gallery _and_ an executable paper)

## Usage
Pull the Docker images from Docker Hub to start with a pre-configured Python environment tailored for heliophysics research and development.

```bash
docker pull spolson/pyhc-environment:vYYYY.MM.DD
docker pull spolson/pyhc-gallery:vYYYY.MM.DD
docker pull spolson/pyhc-gallery-w-executable-paper:vYYYY.MM.DD
```
(Replace `vYYYY.MM.DD` with the actual image version.)

## PyHC Package Versions in Current Environment
