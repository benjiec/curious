.PHONY: clean clean-pyc clean-build clean-js \
	build_assets \
	test test-tox \
	bump/major bump/minor bump/patch \
	start \
	release

CURIOUS_HOME ?= /usr/src/curious
MANAGE = python tests/manage.py
SETUP = python setup.py

all: test-tox

build_assets:
	${SETUP} build_assets

clean: clean-build clean-pyc clean-js

clean-build:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

clean-js:
	rm -rf curious/static/curious/lib/*
	rm -rf curious/static/curious/dist/*

test:
	${MANAGE} test

test-tox:
	tox

bump/major bump/minor bump/patch:
	bumpversion --verbose $(@F)


release: clean sdist bdist_wheel
	twine upload dist/*

sdist:
	${SETUP} sdist
	ls -l dist

bdist_wheel:
	${SETUP} bdist_wheel
	ls -l dist

start: build_assets
	${MANAGE} runserver ${SERVER_IP}:${SERVER_PORT}


MAKE_EXT = docker-compose run --rm curious make -C ${CURIOUS_HOME}

# Generically execute make targets from outside the Docker container
%-ext: image
	${MAKE_EXT} $*

# Build the image
image:
	docker-compose build --pull
