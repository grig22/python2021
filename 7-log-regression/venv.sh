#!/usr/bin/env bash
set -eux
rm -rf venv
python3.9 -m venv venv
set +u
source ./venv/bin/activate
set -u
ncd='--no-cache-dir'
python -m pip install $ncd pip --upgrade
python -m pip install $ncd wheel
python -m pip install $ncd -r requirements.txt
# https://janakiev.com/blog/jupyter-virtual-envs/
python -m ipykernel install --name=myeenv --user
echo '---> sequence completed'