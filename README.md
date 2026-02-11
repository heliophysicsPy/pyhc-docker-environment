# PyHC Environment Pipeline
[![Binder](https://binder.opensci.2i2c.cloud/badge_logo.svg)](https://binder.opensci.2i2c.cloud/v2/gh/heliophysicsPy/science-platforms-coordination/pyhc?urlpath=lab/tree/Welcome.ipynb)

## Overview
The PyHC Environment Pipeline automates the creation of a Docker image with a Python environment that comes pre-loaded with the latest versions of all published PyHC ([Python in Heliophysics Community](https://pyhc.org/projects)) packages. The GitHub Actions workflow rebuilds and pushes the Docker image to [Docker Hub](https://hub.docker.com/u/spolson) each time a PyHC package releases a new update. It also keeps the source files in this repo in-sync with what's in Docker Hub, and updates a Binder build.

## Features
- **Binder Deployment**: For ease of use, the `pyhc-environment` Docker image is deployed in Binder and continually updated (use the "launch binder" badge above to access it).
- **Automated Docker Builds**: Automatically builds the Docker image with an updated Python environment using GitHub Actions.
- **Daily Updates**: Runs daily to check for and include the latest versions of PyHC packages.
- **Docker Hub Hosting**: Docker image is readily available on Docker Hub for easy access and deployment.
- **Dependency Spreadsheet**: An intermediate step of the pipeline is to generate an Excel spreadsheet showing a matrix of allowed version range requirements.

## Workflow Parameters

The pipeline workflow supports the following manual trigger parameters:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `skip_checks` | Skip auto-pin and compile (quick deploy mode) | `false` |
| `force_build` | Force build even if no changes detected | `false` |
| `generate_spreadsheet` | Generate dependency spreadsheet | `true` |
| `spreadsheet_workers` | Number of workers for spreadsheet generation | `2` |
| `docker_tag_suffix` | Optional suffix appended to date tag (e.g., `-temp`) | `` |

### Trigger Behavior

The pipeline triggers a Docker rebuild when any of the following conditions are met:
- **PyHC package version update**: A PyHC package has a newer version on PyPI
- **Package set change**: A package is added to or removed from `packages.txt`
- **Force build**: The `force_build` parameter is set to `true`
- **Quick deploy**: The `skip_checks` parameter is set to `true` (skips validation)

### Quick Deploy Mode

Use `skip_checks=true` for emergency deployments when you need to rebuild the Docker image without running the full validation pipeline. This mode:
- Skips auto-pin (fetching latest versions from PyPI)
- Skips dependency resolution (uv compile)
- Skips spreadsheet generation
- Goes directly to Docker build with current `packages.txt` content

## Docker Image
The pipeline creates and maintains the following Docker image:
- [pyhc-environment](https://hub.docker.com/r/spolson/pyhc-environment)

## Usage
Click the "launch binder" badge at the top of this README to launch the latest `pyhc-environment` in Binder.

Alternatively, you may run the Docker image locally by pulling it from Docker Hub:

```bash
docker pull spolson/pyhc-environment:vYYYY.MM.DD
```
(Replace `vYYYY.MM.DD` with the actual image version.)

## PyHC Package Versions in Current Environment
Package | Version
---|---
aacgmv2 | 2.7.0
aiapy | 0.11.0
apexpy | 2.1.0
asilib | 0.29.2
astrometry-azel | 1.3.0
ccsdspy | 1.4.3
cdflib | 1.3.8
cloudcatalog | 1.1.0
dascutils | 2.3.0
dbprocessing | 0.1.0
dmsp | 0.6.0
enlilviz | 0.2.0
EUVpy | 1.0.0
fiasco | 0.7.0
gcmprocpy | 1.2.1
geopack | 1.0.12
georinex | 1.16.2
geospacelab | 0.12.3
goesutils | 1.0.8
hapiclient | 0.2.6
hapiplot | 0.2.2
hissw | 2.3
igrf | 13.0.2
iri2016 | 1.11.1
irispy-lmsal | 0.6.0
kaipy | 1.1.4
lofarSun | 0.3.32
lowtran | 3.1.0
madrigalWeb | 3.3.6
maidenhead | 1.8.0
mcalf | 1.0.0
msise00 | 1.11.1
ndcube | 2.4.0
nexradutils | 1.0.0
ocbpy | 0.6.0
OMMBV | 1.1.0
plasmapy | 2025.10.0
pyaurorax | 1.22.0
pycdfpp | 0.8.6
pydarn | 4.2
pyflct | 0.3.1
pyhc-core[tests] | 0.0.7
pymap3d | 3.2.0
pyrfu | 2.4.20
pysat | 3.2.2
pyspedas | 2.0.7
pytplot | 1.7.28
pytplot-mpl-temp | 2.2.79
pyzenodo3 | 1.0.2
reesaurora | 1.0.5
regularizepsf | 1.1.1
sammi-cdf | 1.0.2
savic | 1.2.7
sciencedates | 1.5.0
SciQLop | 0.10.4
SkyWinder | 0.0.3
solarmach | 0.5.2
solo-epd-loader | 0.4.4
space-packet-parser | 6.1.0
spacepy | 0.7.0
speasy | 1.7.1
spiceypy | 8.0.1
sunkit-image | 0.6.1
sunkit-instruments | 0.6.2
sunpy | 7.1.0
sunraster | 0.7.0
swxsoc | 0.2.3
themisasi | 1.2.0
viresclient | 0.14.1
wmm2015 | 1.1.1
wmm2020 | 1.1.1
