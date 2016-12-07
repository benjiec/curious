#!/usr/bin/env python

import os
import sys
import subprocess
import setuptools

class BowerBuildCommand(setuptools.Command):
    description = "run bower commands."
    user_options = [
        ('bower-command=', 'c',
         'Bower command to run. Defaults to \'install\'.'),
        ('force-latest', 'F', 'Force latest version on conflict.'),
        ('production', 'p', 'Do not install project devDependencies.'),
    ]

    boolean_options = ['production', 'force-latest']

    def initialize_options(self):
        self.force_latest = False
        self.production = False
        self.bower_command = 'install'

    def finalize_options(self):
        pass

    def run(self):
        cmd = ['bower', self.bower_command]
        if self.force_latest:
            cmd.append('-F')
        if self.production:
            cmd.append('-p')
        self.spawn(cmd)

def collect_requirements():
    requirements_fn = os.path.join(SourceDir, "requirements.txt")
    with open(requirements_fn) as reqfh:
        return filter(lambda txt: txt and txt[0] != '#', map(str.strip, reqfh.readlines()))

SourceDir = os.path.split(os.path.abspath(__file__))[0]
SetupConfiguration = {
    "name": "curious",
    "version": "0.1",
    "author": "Benjie Chen, Ginkgo Bioworks",
    "author_email": "benjie@ginkgobioworks.com",
    "description": "Data exploration tool",
    "license": "MIT",
    "packages": ['curious'],
    "include_package_data": True,
    "zip_safe": True,
    "cmdclass": {
        "install_bower": BowerBuildCommand,
    },
}

if __name__ == "__main__":
    # allow setup.py to be run from any path
    os.chdir(SourceDir)
    conf = SetupConfiguration.copy()
    conf["install_requires"] = collect_requirements()
    setuptools.setup(**conf)
