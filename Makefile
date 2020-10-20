.PHONY: clean
clean:
        rm -r ./dist

.PHONY: init
## Initialize the development environment to enable running of build and test rules.
init:
        pipenv install -e . --dev


.PHONY: build
## Compiles the project and procudes PYC files.
build:
	pipenv run python -m compileall .


.PHONY: package
## Build the project and assemble a deployable package.
package: clean
	pipenv run python setup.py sdist -d ./dist
	pipenv run python setup.py bdist_wheel -d ./dist


.PHONY: publish
## Publish to the respective indexing service
publish: package
	pipenv run twine check ./dist/*
	pipenv run twine upload --non-interactive ./dist/*
