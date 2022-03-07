#!/usr/bin/env bash
set -eux
rm -rf venv
python3.9 -m venv venv
set +u
source ./venv/bin/activate
set -u
python -m pip install --no-cache-dir pip --upgrade
python -m pip install --no-cache-dir -r requirements.txt
# https://janakiev.com/blog/jupyter-virtual-envs/
python -m ipykernel install --name=myeenv --user