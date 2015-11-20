# -*- coding: utf-8 -*-
from __future__ import print_function
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import codecs
import os
import sys
import re


def read(*parts):
    here = os.path.abspath(os.path.dirname(__file__))
    # intentionally *not* adding an encoding option to open
    return codecs.open(os.path.join(here, *parts), 'r').read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)

setup(
    name='envparse',
    version=find_version('.', 'envparse.py'),
    url='https://github.com/rconradharris/envparse',
    license='MIT',
    author='Rick Harris',
    author_email='rconradharris@gmail.com',
    tests_require=['pytest'],
    install_requires=[''],
    cmdclass={'test': PyTest},
    description='Simple environment variable parsing',
    long_description=read('README.rst'),
    py_modules=['envparse'],
    platforms='any',
    zip_safe=False,
    classifiers = [
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        ],
    extras_require={
        'testing': ['pytest'],
      }
)
