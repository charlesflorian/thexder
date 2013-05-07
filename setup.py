from distribute_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages

args = dict(
    name= 'Thexder',
    version = '0.0',
    packages = find_packages(),
    include_package_data = True,
    author = "Simon Rose",
    author_email = "simon.cfr@gmail.com",
    description = "Port of Thexder to Python",
#    install_requires = ['pygame==1.9.1release'],
    license = "BSD",
    keywords = "thexder abandonware pygame game",
    entry_points = {
        'console_scripts': [
            'thexder_edit = thexder.edit:cli',
        ],
    },
)
setup(**args)
