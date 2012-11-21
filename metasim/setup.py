from setuptools import setup, find_packages

setup(
    name='metasim',
    version='0.1',
    long_description=__doc__,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[]
	description='Game simulation application',
	author='Michael Sobczak',
	author_email='michaelsobczak54@gmail.com',
	url='',
    entry_points = {
        'console_scripts': [
        'metasim-run = core.engine:RunEngine',
        ],
    }
)