#!/bin/bash
set -euo pipefail
mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt
export PYTHONDONTWRITEBYTECODE=1
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
unset PYTEST_ADDOPTS PYTEST_PLUGINS
# pytest and pytest-json-ctrf are pinned in the image (environment/Dockerfile); the checks
# only read /app/output, so the run is offline.
if python3 -B -m pytest -p ctrf.main -p no:cacheprovider --rootdir=/tests \
     --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA
then echo 1 > /logs/verifier/reward.txt; exit 0
else te=$?; echo 0 > /logs/verifier/reward.txt; exit $te; fi
