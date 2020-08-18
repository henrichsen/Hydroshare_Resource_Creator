from setuptools import setup, find_namespace_packages
from tethys_apps.app_installation import find_resource_files

### Apps Definition ###
app_package = 'hydroshare_resource_creator'
release_package = 'tethysapp-' + app_package

### Python Dependencies ###
dependencies = ['simplejson','xmltodict','pandas','lxml']
# -- Get Resource File -- #
resource_files = find_resource_files('tethysapp/' + app_package + '/templates', 'tethysapp/' + app_package)
resource_files += find_resource_files('tethysapp/' + app_package + '/public', 'tethysapp/' + app_package)
resource_files += find_resource_files('tethysapp/' + app_package + '/workspaces', 'tethysapp/' + app_package)



setup(
    name=release_package,
    version='1',
    description='Creates a HydroShare resource from the CUAHSI data client',
    long_description='',
    keywords='',
    author='Matthew Bayles',
    author_email='mmbayles@gmail.com',
    url='',
    license='',
    packages=find_namespace_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
    zip_safe=False,
    install_requires=dependencies,
)
