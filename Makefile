.PHONY: clean clean-pyc clean-build \
	test test-tox \
	bump/major bump/minor bump/patch \
	start \
	release

CURIOUS_HOME ?= /usr/src/curious
MANAGE = python ${CURIOUS_HOME}/tests/manage.py
SETUP = python ${CURIOUS_HOME}/setup.py

all: test-tox

clean: clean-build clean-pyc

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

test:
	${MANAGE} test

test-tox:
	tox

bump/major bump/minor bump/patch:
	bumpversion --verbose $(@F)


release: clean sdist bdist_wheel
	twine upload dist/*

sdist:
	python setup.py sdist
	ls -l dist

bdist_wheel:
	python setup.py bdist_wheel
	ls -l dist

start:
	${MANAGE} runserver ${SERVER_IP}:${SERVER_PORT}

MAKE_EXT = docker-compose run --rm curious make -C ${CURIOUS_HOME}

# Generically execute make targets from outside the Docker container
%-ext: image
	${MAKE_EXT} $*

# Build the image
image:
	docker-compose build --pull
