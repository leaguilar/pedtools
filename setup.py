# -*- coding: utf-8 -*-

from setuptools import setup, find_packages  # type: ignore
from pedtools import __version__

with open("README.md", "r") as fh:
    README = fh.read()

# The main source of truth for install requirements of this project is the requirements.txt file.
with open("requirements.txt", "r") as f:
    REQUIREMENTS = f.readlines()

setup(
    name='pedtools',
    version=__version__+".dev.2",
    description='Client library used to communicate with the ease.ml service.',
    long_description=README,
    long_description_content_type="text/markdown",
    author='Francesco Zanlungo, Claudio Feliciani, Leonel Aguilar',
    author_email='leonel.aguilar.m@gmail.com',
    url='https://github.com/leaguilar/pedtools',
    license='MIT',
    install_requires=REQUIREMENTS,
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ],
    entry_points={"console_scripts": ["pedtools=pedtools.commands.main:main"],
                  "crowd": ["congestion_number = pedtools.metrics.crowd.congestion_number.congestion_number:calc_cn"],
                  },
)
