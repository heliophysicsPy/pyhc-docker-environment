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
Package | Version
---|---
aacgmv2 | 2.6.3
aiapy | 0.7.4
aidapy | 0.0.4
apexpy | 2.0.1
astrometry-azel | 1.3.0
ccsdspy | 1.2.1
cdflib | 0.4.9
dascutils | 2.3.0
dbprocessing | 0.1.0
dmsp | 0.6.0
enlilviz | 0.2.0
fiasco | 0.2.3
geopack | 1.0.10
georinex | 1.16.2
geospacelab | 0.6.1
goesutils | 1.0.8
hapiclient | 0.2.5
heliopy | 0.15.4
hissw | 2.3
igrf | 13.0.2
iri2016 | 1.11.1
irispy-lmsal | 0.2.0
kamodo | 23.3.0
lowtran | 3.1.0
madrigalWeb | 3.3
maidenhead | 1.7.0
mcalf | 1.0.0
msise00 | 1.10.1
ndcube | 2.2.0
nexradutils | 1.0.0
ocbpy | 0.3.0
OMMBV | 1.0.1
plasmapy | 2024.2.0
pydarn | 4.0
pyflct | 0.2.3
pymap3d | 3.1.0
pysat | 3.2.0
pyspedas | 1.5.11
pytplot | 1.7.28
pytplot-mpl-temp | 2.2.20
pyzenodo3 | 1.0.2
reesaurora | 1.0.5
regularizepsf | 0.3.2
sciencedates | 1.5.0
SkyWinder | 0.0.3
solarmach | 0.3.3
solo-epd-loader | 0.3.7
space-packet-parser | 4.2.0
spacepy | 0.5.0
speasy | 1.2.7
spiceypy | 6.0.0
sunkit-image | 0.5.1
sunkit-instruments | 0.5.0
sunpy | 5.1.2
sunraster | 0.5.1
themisasi | 1.2.0
viresclient | 0.11.6
wmm2015 | 1.1.1
wmm2020 | 1.1.1
