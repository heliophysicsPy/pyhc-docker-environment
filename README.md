# PyHC Environment Pipeline
[![Binder](https://binder.opensci.2i2c.cloud/badge_logo.svg)](https://binder.opensci.2i2c.cloud/v2/gh/heliophysicsPy/science-platforms-coordination/pyhc)

## Overview
The PyHC Environment Pipeline automates the creation of Docker images with Python environments that come pre-loaded with the latest versions of all published PyHC ([Python in Heliophysics Community](https://pyhc.org/projects)) packages. The GitHub Actions workflow rebuilds and pushes the Docker images to [Docker Hub](https://hub.docker.com/u/spolson) each time a PyHC package releases a new update. It also keeps the source files in this repo in-sync with what's in Docker Hub, and updates a Binder build.

## Features
- **Automated Docker Builds**: Automatically builds Docker images with updated Python environments using GitHub Actions.
- **Daily Updates**: Runs daily to check for and include the latest versions of PyHC packages.
- **Docker Hub Hosting**: Docker images are readily available on Docker Hub for easy access and deployment.
- **Dependency Spreadsheet**: An intermediate step of the pipeline is to generate an Excel spreadsheet showing a matrix of allowed version range requirements.
- **Binder Deployment**: For ease of use, the `pyhc-environment` Docker image is deployed in Binder and continually updated (use the "launch binder" badge above to access it). 

## Docker Images
The pipeline creates and maintains the following Docker images:
- [pyhc-environment](https://hub.docker.com/r/spolson/pyhc-environment) (the base env)
- [pyhc-gallery](https://hub.docker.com/r/spolson/pyhc-gallery) (base env with notebooks from PyHC's gallery)

## Usage
Click the "launch binder" badge at the top of this README to launch the latest `pyhc-environment` in Binder.

Alternatively, you may run the Docker images locally by pulling them from Docker Hub:

```bash
docker pull spolson/pyhc-environment:vYYYY.MM.DD
docker pull spolson/pyhc-gallery:vYYYY.MM.DD
```
(Replace `vYYYY.MM.DD` with the actual image version.)

## PyHC Package Versions in Current Environment
Package | Version
---|---
aacgmv2 | 2.7.0
aiapy | 0.10.1
aidapy | 0.0.4
amisrsynthdata | 1.1.8
apexpy | 2.1.0
astrometry-azel | 1.3.0
ccsdspy | 1.3.3
cdflib | 1.3.3
cloudcatalog | 1.0.2
dascutils | 2.3.0
dbprocessing | 0.1.0
dmsp | 0.6.0
enlilviz | 0.2.0
fiasco | 0.4.0
gcmprocpy | 1.1.0
geopack | 1.0.11
georinex | 1.16.2
geospacelab | 0.8.15
goesutils | 1.0.8
hapiclient | 0.2.6
hapiplot | 0.2.2
heliopy | 0.15.4
hissw | 2.3
igrf | 13.0.2
iri2016 | 1.11.1
irispy-lmsal | 0.2.1
kamodo | 23.3.0
lofarSun | 0.3.32
lowtran | 3.1.0
madrigalWeb | 3.3.1
maidenhead | 1.7.0
mcalf | 1.0.0
msise00 | 1.11.1
ndcube | 2.3.1
nexradutils | 1.0.0
ocbpy | 0.5.0
plasmapy | 2024.10.0
pyaurorax | 1.15.0
pycdfpp | 0.7.6
pydarn | 4.1
pyflct | 0.3.1
pyhc-core[tests] | 0.0.6
pymap3d | 3.1.0
pysat | 3.2.1
pyspedas | 1.7.4
pytplot | 1.7.28
pytplot-mpl-temp | 2.2.54
pyzenodo3 | 1.0.2
reesaurora | 1.0.5
regularizepsf | 1.0.2
sammi-cdf | 1.0.0
savic | 1.1.0
sciencedates | 1.5.0
SciQLop | 0.8.1
SkyWinder | 0.0.3
solarmach | 0.5.0
solo-epd-loader | 0.4.1
space-packet-parser | 5.0.1
spacepy | 0.7.0
speasy | 1.4.0
spiceypy | 6.0.0
sunkit-image | 0.6.0
sunkit-instruments | 0.5.0
sunpy | 6.0.4
sunraster | 0.5.1
themisasi | 1.2.0
viresclient | 0.12.1
wmm2015 | 1.1.1
wmm2020 | 1.1.1
