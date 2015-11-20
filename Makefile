SHELL := /bin/bash

help:
	@echo 'Makefile for envparse'
	@echo ''
	@echo 'Usage:'
	@echo '   make release      push to the PyPI'
	@echo '   make test         run the test suite'
	@echo ''

release:
	python setup.py register sdist bdist_wheel upload

test:
	tox
