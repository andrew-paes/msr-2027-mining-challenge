# MSR 2027 Mining Challenge - Makefile (cross-platform)
#
# Python: "py" on Windows, "python3" on Linux/macOS.
# Override with:  make PYTHON=python run

ifeq ($(OS),Windows_NT)
PYTHON := py
else
PYTHON := python3
endif

.PHONY: help install run test charts clone phase3 clean

help:
	@echo "Targets: install | run | test | charts | clone | phase3 | clean"

install:
	$(PYTHON) -m pip install -r requirements.txt

run:
	$(PYTHON) -m streamlit run app.py

test:
	$(PYTHON) test_app.py

# Pre-clone every repo in the Phase 3 sample (slow, network-bound). Runs the
# materialize + draw-sample steps first if their CSVs are missing. Skipped on
# repos already cloned under clones/ — safe to re-run.
clone:
	$(PYTHON) phase3.py --clone-only

# Full Phase 3 run: clone-if-needed + classify -> data/phase3_results.csv.
phase3:
	$(PYTHON) phase3.py

# Regenerate all derived CSVs + chart PNGs from the SpecMine dataset.
# Run after updating the data (parquet / specs.jsonl). Order matters:
#   taxonomy_e0.csv feeds phase3; accessibility feeds the bridge chart.
# Slow steps: extract_accessibility (streams specs.jsonl) and phase3
# (git-clones repos). The chart_*.py steps are fast.
charts:
	$(PYTHON) taxonomy.py
	$(PYTHON) extract_accessibility.py
	$(PYTHON) phase3.py
	$(PYTHON) chart_m0.py
	$(PYTHON) chart_m1.py
	$(PYTHON) chart_m2.py
	$(PYTHON) chart_census.py
	$(PYTHON) chart_m4.py
	$(PYTHON) chart_taxonomy.py
	$(PYTHON) chart_accessibility.py
	$(PYTHON) chart_m7.py
	$(PYTHON) chart_phase3.py
	$(PYTHON) chart_bridge.py

clean:
	$(PYTHON) -c "import shutil,pathlib;[shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__') if p.is_dir()]"
