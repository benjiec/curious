#!/usr/bin/env python
from __future__ import print_function
from subprocess import check_output, STDOUT
from setuptools import setup, Command


class BowerBuildCommand(Command):
  description = 'run bower commands.'
  user_options = [
    ('bower-command=', 'c', 'Bower command to run. Defaults to "install".'),
    ('force-latest', 'F', 'Force latest version on conflict.'),
    ('allow-root', 'R', 'Allow bower to be run as root.'),
    ('production', 'p', 'Do not install project devDependencies.'),
  ]

  boolean_options = ['production', 'force-latest']

  def initialize_options(self):
    self.force_latest = False
    self.production = False
    self.bower_command = 'install'
    self.allow_root = False

  def finalize_options(self):
    pass

  def run(self):
    cmd = ['bower', self.bower_command, '--no-color']
    if self.force_latest:
      cmd.append('-F')
    if self.production:
      cmd.append('-p')
    if self.allow_root:
      cmd.append('--allow-root')
    self.debug_print(check_output(cmd, stderr=STDOUT))


setup(
  name='curious',
  version='0.1.0',

  author='Benjie Chen, Ginkgo Bioworks',
  author_email='benjie@ginkgobioworks.com, devs@ginkgobioworks.com',

  description='Graph-based data exploration tool',
  long_description=open('README.rst').read(),
  url='https://github.com/ginkgobioworks/curious',

  license='MIT',
  keywords='graph query django sql curious database ginkgo',
  classifiers=[
    'Development Status :: 5 - Production',
    'Environment :: Web Environment',
    'Environment :: Other Environment',
    'Framework :: Django :: 1.6',
    'Intended Audience :: Developers',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: MIT License',
    'Natural Language :: English',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: JavaScript',
    'Programming Language :: SQL',
    'Topic :: Database',
    'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
    'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    'Topic :: Scientific/Engineering :: Information Analysis',
    'Topic :: Software Development :: Libraries',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: Text Processing :: General',
  ],

  cmdclass={
    'install_bower': BowerBuildCommand,
  },

  packages=['curious'],
  include_package_data=True,
  install_requires=[
    'Django < 1.7',
    'humanize',
    'parsimonious == 0.5',
    'parsedatetime ~= 1.0',
    'webassets',
    'jsmin',
  ],
  tests_require=[
    'tox',
    'nose',
    'django-nose < 1.4',
    'coverage',
  ],
  zip_safe=True,
)
