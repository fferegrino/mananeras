init:
	pipenv install --dev

patch:
	pipenv run bumpversion patch --verbose

minor:
	pipenv run bumpversion minor --verbose

major:
	pipenv run bumpversion major --verbose

style:
	pipenv run black .
	pipenv run isort .

lint:
	pipenv run pflake8 .
	pipenv run isort . --check-only
	pipenv run black . --check

test:
	pipenv run pytest -vv --cov-report term:skip-covered --cov=. tests/unit/api