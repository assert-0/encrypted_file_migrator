lint:
	flake8 --ignore=F541 encrypted_file_migrator

type-check:
	mypy encrypted_file_migrator
