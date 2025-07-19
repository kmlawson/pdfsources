# pdfsources

pdfsources will be a tool for the extraction of citations (footnotes or bibliography) from a collection of PDFs or Ebpubs and will compile them into a markdown report.

# Deployment

- Save progress in a git repository
- Will eventually host on github user kmlawson as a repository
- Will eventually deploy to PyPI but only when the user indicates it is ready


# Features

- see the README.md for already implemented features
- see the DEVELOPMENT.md to get a better understanding of the project structure and tips for development.

# Installing 

- use the makefile to `make reinstall` when this exists
# Development Habits

- write unit tests for all new features before developing a feature
- use a Makefile (create it if it isn't in the main directory and add to gitignore) with:
	- reinstall - `uv tool uninstall [project name] && uv cache clean && uv tool install`
	- lint-fix - to use ruff for lint fix
    - lint - to use ruff to check files
	- test - to `uv run pytest` on the tests directory (using `PYTHONPATH=. uv run pytest tests/` internally)
    - test-verbose - to run tests with verbose mode
    - versionbump - to increment the version 0.0.1 in all the required places
     help - to show list of targets for make
- keep the code files small, divide things into different modular files and make sure new features and tasks that should be in their own file are separate from the main script.
- keep functions useful to various scripts in utils.py or, if that gets too big, similar files.
- keep all tests in the tests 
- keep DEVELOPMENT.md up to date on project structure, key development patterns, and deployment instructions. 
- **Style**: Follow PEP 8 style guide for Python code: https://peps.python.org/pep-0008/
- **Ruff**: Make use of `ruff check .`  (`make lint` and `make lint-fix`) as you go to find and fix small issues
- **Validation**: make use of `pydantic` python library (Documentation: https://docs.pydantic.dev/latest/llms.txt) to help with structured data validation and clean argument handling
- **Secrets:** make use of `gitleaks` 

# Version Control

- the project should have a repository and versions increment by 0.0.x as new features are added 
- CHANGELOG.md should be kept up to date as problems get fixed and new features added.
- confirm that any new features or functionality is accurately described in README.md and in the -h/--help for the tool
- when you have fixed a series of issues or added new features you can commit and push to github using gh, but only after:
	- reinstalling the tool (`make reinstall`), running ruff (`make lint`) and evaluating its output, fixing problems except for minor issues with tests
	- running tests
	- confirming that tests run and the feature functionality has been tested

# Deployment

- when the user wants you to deploy to PyPI:
	- increment the version by 0.0.1 point and update this in all files, as well as a blue PyPI badge at top of README.md
	- make sure the tests are all running, and run `ruff check .` to see if there are any small issues to resolve
	- that the CHANGELOG is up to date
	- **Clean and build**: `rm -rf dist/ && uv build`
	- Requires `.pypirc` file in home directory with PyPI API token
	- Package will appear at: https://pypi.org/project/[project-name]
	- use `twine upload`
		- do not use `uv publish` because of problems with credential set up.

# Security

# Documentation

- always keep documentation up to date in these places:
	- -h/--help - and make sure that this stays organized using, bolded **SECTION HEADERS** in the help to organize related features
	- README.md should have key documentation
	- docs folder can include one or more documents
	- user may ask you to 


# Key Files

- GEMINI.md - needs to be kept in memory - to be added to gitignore
- KEYFILES.md - will list key scripts to keep in memory - to be added to gitignore
- DEVELOPMENT.md - an overview of the development process and notes for LLMs to get oriented in the code base
- README.md - instructions for the user
- CHANGELOG.md - update this whenever new features have been added or a collection of problems have been fixed
- TODO.md - To keep a list of tasks to carry out and mark them as done when they are completed. Add this to gitignore
- info - a directory to keep some reference docs 
- info/llm-reports - a directory to keep some reports made by LLMs to evaluate progress; add to gitignore
- reference - a directory with some notes on other similar projects and how they work; add to gitignore

