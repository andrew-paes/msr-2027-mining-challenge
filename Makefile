# MSR 2027 Mining Challenge - Makefile (cross-platform)
#
# Python: "py" on Windows, "python3" on Linux/macOS.
# Override with:  make PYTHON=python run

ifeq ($(OS),Windows_NT)
PYTHON := py
else
PYTHON := python3
endif

.PHONY: help install run test clean

help:
	@echo "Targets: install | run | test | clean"

install:
	$(PYTHON) -m pip install -r requirements.txt

run:
	$(PYTHON) -m streamlit run app.py

test:
	$(PYTHON) test_app.py

clean:
	$(PYTHON) -c "import shutil,pathlib;[shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__') if p.is_dir()]"
