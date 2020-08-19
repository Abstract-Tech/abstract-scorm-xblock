.PHONY: help
SHELL=/bin/bash

build:
	rm -r abstract_scorm_xblock/dist/*; cd abstract_scorm_xblock/ && python setup.py sdist bdist_wheel

PYPI_SERVER ?= testpypi
release-upload: build
	@ if [ "$(PYPI_SERVER)" == "testpypi" ]; then echo -e 'To release to the production pypi index run with\nmake release PYPI_SERVER=pypi'; fi
	twine upload -r $(PYPI_SERVER) abstract_scorm_xblock/dist/*

help: ## display this help message
	@echo "Please use \`make <target>' where <target> is one of"
	@grep '^[a-zA-Z]' $(MAKEFILE_LIST) | sort | awk -F ':.*?## ' 'NF==2 {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}'
