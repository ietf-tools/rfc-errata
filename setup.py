#!/usr/bin/env python
# -------------------------------------------------------
# Copyright The IETF Trust 2018-2022, All Rights Reserved
# -------------------------------------------------------

import re
from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(os.path.join(here, 'README.md'), encoding='utf-8') as file:
    long_description = file.read()

# Get the requirements from the local requirements.txt file
with open(path.join(here, 'requirements.txt'), encoding='utf-8') as file:
    requirements = file.read().splitlines()

import Rfc_Errata

setup(
    name='rfc-errata',
    description="Build html files from the text RFCs and the errata database.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    
    # The projects main homepage.
    url='https://github.com/ietf-tools/rfc-errata',
    download_url = "https://github.com/ietf-tools/rfc-errata/releases",

    # Author details
    author='Jim Schaad',
    author_email='tools-discuss@ietf.org',

    # Choose your license
    license='BSD-3-Clause',

    # Classifiers
    classifiers = [
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Other Audience',
        'Topic :: Text Processing',
        'Topic :: Text Processing :: Markup :: XML',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3.6',
        ],

    # What does your project relate to?
    keywords='RFC errata',

    #
    packages=find_packages(exclude=['contrib', 'docs', 'Tests']),

    # List run-time dependencies here.
    install_requires=requirements,
    python_requires='>=3.3',

    # List additional gorups of dependencies here.
    # extras_require=(
    #  'dev':['twine',],
    # ]

    package_data={
       'Rfc_Errata': ['templates/*', 'css/*']
       },
    include_package_data = True,

    entry_points={
        'console_scripts': [
            'rfc-errata=Rfc_Errata.run:main'
            ]
        },
    zip_safe=False
)
