#!/usr/bin/env python

from distutils.core import setup
from distutils.version import StrictVersion
from efl.utils.setup import build_extra, build_edc, build_fdo, uninstall
from efl import __version__ as efl_version

MIN_EFL = '1.14'
if StrictVersion(efl_version) < MIN_EFL:
    print('Your python-efl version is too old! Found: ' + efl_version)
    print('You need at least version ' + MIN_EFL)
    exit(1)

setup(
    name = 'eluminance',
    version = '0.9',
    description = 'Photo browser',
    long_description = 'A photo browser written in python-efl',
    license = "GNU GPL",
    author = 'Dave Andreoli',
    author_email = 'dave@gurumeditation.it',
    packages = ['eluminance'],
    requires = ['efl (>=1.14)'],
    provides = ['eluminance'],
    scripts = ['bin/eluminance'],
    cmdclass={
        'build': build_extra,
        'build_edc': build_edc,
        'build_fdo': build_fdo,
        'uninstall': uninstall,
    },
    command_options={
        'install': {'record': ('setup.py', 'installed_files.txt')}
    },
)

