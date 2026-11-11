# MSR 2027 Mining Challenge - Makefile (cross-platform)
#
# Python: "py" on Windows, "python3" on Linux/macOS.
# Override with:  make PYTHON=python run

ifeq ($(OS),Windows_NT)
PYTHON := py
else
PYTHON := python3
endif

.PHONY: help install run test check charts clone classify clean

help:
	@echo "Targets: install | run | test | check | charts | clone | classify | clean"

install:
	$(PYTHON) -m pip install -r requirements.txt

run:
	$(PYTHON) -m streamlit run app.py

# Headless validation: chart rules first (alt text, dpi, contrast, no hardcoded
# numbers), then the dashboard must build without exceptions.
test: check
	$(PYTHON) test_app.py

# Chart rules only — fast, no Streamlit involved.
check:
	$(PYTHON) check_charts.py

# Pre-clone every repo in the clone-classify sample (slow, network-bound). Runs the
# materialize + draw-sample steps first if their CSVs are missing. Skipped on
# repos already cloned under clones/ — safe to re-run.
clone:
	$(PYTHON) clone_classify.py --clone-only

# Full clone-classify run: clone-if-needed + classify -> data/classification_results.csv.
classify:
	$(PYTHON) clone_classify.py

# Regenerate all derived CSVs + chart PNGs from the SpecMine dataset.
# Run after updating the data (parquet / specs.jsonl). Order matters:
#   taxonomy_e0.csv feeds classify; accessibility feeds the bridge chart.
# Slow steps: extract_accessibility (streams specs.jsonl) and clone-classify
# (git-clones repos). The chart_*.py steps are fast.
charts:
	$(PYTHON) taxonomy.py
	$(PYTHON) extract_accessibility.py
	$(PYTHON) clone_classify.py
	$(PYTHON) chart_m0.py
	$(PYTHON) chart_m0_tools.py
	$(PYTHON) chart_m1.py
	$(PYTHON) chart_m1_tools.py
	$(PYTHON) chart_m2.py
	$(PYTHON) chart_census.py
	$(PYTHON) chart_m4.py
	$(PYTHON) chart_taxonomy.py
	$(PYTHON) chart_accessibility.py
	$(PYTHON) chart_m7.py
	$(PYTHON) chart_by_bucket.py
	$(PYTHON) chart_outcomes.py
	$(PYTHON) chart_bridge.py
	$(PYTHON) chart_bridge_repo.py

clean:
	$(PYTHON) -c "import shutil,pathlib;[shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__') if p.is_dir()]"
