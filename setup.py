#!/usr/bin/env python

import os
from setuptools import setup, find_packages

README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

with open("requirements.txt", "r") as f:
    install_requires = [x.strip() for x in f.readlines() if not x.strip().startswith("#")]

setup(name="curious",
      version="0.1",
      author="Benjie Chen, Ginkgo Bioworks",
      author_email="benjie@ginkgobioworks.com",
      description="Data exploration tool",
      license="MIT",
      packages=['curious'],
      include_package_data=True,
      zip_safe=True,
      install_requires=install_requires)
