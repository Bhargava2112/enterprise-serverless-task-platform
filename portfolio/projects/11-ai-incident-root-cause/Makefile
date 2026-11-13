PYTHON ?= python3
.PHONY: test smoke
test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v
smoke:
	PYTHONPATH=src $(PYTHON) src/app.py
