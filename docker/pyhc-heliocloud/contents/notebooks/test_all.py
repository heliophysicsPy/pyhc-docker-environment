import pytest
import importlib
import os.path
import sys

def test_config_paths():
    assert os.path.exists('/etc/profile.d/init_conda.sh')
    assert os.path.exists('/srv/conda/.condarc')
    assert os.path.exists('/srv/start')
    assert os.path.exists('/etc/profile.d/show_motd.sh')


def test_environment_variables():
    # These are required for jupyterhub and binderhub compatibility
    assert os.environ['NB_USER'] == 'jovyan'
    assert os.environ['NB_UID'] == '1000'
    assert 'NB_PYTHON_PREFIX' in os.environ


def test_default_conda_environment():
    assert sys.prefix == '/srv/conda/envs/notebook'

packages = [
    # included in panhelio-notebook metapackage
    # https://github.com/conda-forge/panhelio-notebook-feedstock/blob/master/recipe/meta.yaml
    'distributed', 'dask_gateway', 'dask_labextension', 
    'dask', 'distributed', 'dask_gateway', 'dask_labextension', 
    'jupytext',
    # key HelioCloud packages
    'cloudcatalog',
    # jupyterhub and related utilities
    'ipykernel',
    'jupyterhub', 'jupyterlab', 
    'nbgitpuller', 
    'smart_open',
    # 'nbzip',
    # aws/storage stuff
    'boto3', 's3fs', 'kerchunk', 'h5py', 'xarray', 'zarr',
    # pyhc core 
    'hapiclient',
    'hapiplot',
    'kamodo',
    'plasmapy', 
    'pyspedas', 
    'spacepy', 
    'sunpy', 'sunpy_soar', 'sunkit_image', 
#    'pysat', 
    # other critical packages 
    'astroquery',
    'apexpy', 'aacgmv2', 
    'ccdproc',
    'cdflib',
    'fiasco',
    'geospacepy',
    'netCDF4',
    'ocbpy',
    #'OMMBV',
    'solarmach',
#    'speasy',
    'tensorflow',
    'viresclient',
    ]

@pytest.mark.parametrize('package_name', packages, ids=packages)
def test_import(package_name):
    importlib.import_module(package_name)

def test_dask_config():
    import dask
    assert '/srv/conda/etc' in dask.config.paths
    assert dask.config.config['labextension']['factory']['class'] == 'LocalCluster'

# Works locally but hanging on GitHub Actions, possibly due to:
# Unclosed client session client_session: <aiohttp.client.ClientSession object at 0x7ff7a2931950>
#@pytest.fixture(scope='module')
#def client():
#    from dask.distributed import Client
#    with Client(n_workers=4) as dask_client:
#        yield dask_client
#
#def test_check_dask_version(client):
#    print(client)
#    versions = client.get_versions(check=True)
