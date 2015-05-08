#!/usr/bin/env python

from distutils.core import setup
from efl.utils.setup import build_extra, build_edc, build_fdo, uninstall


setup(
    name = 'eluminance',
    version = '0.8',
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

