#!/usr/bin/env bash
set -eux
rm -rf venv
python3.9 -m venv venv
./venv/bin/python -m pip install pip --upgrade --no-cache-dir
./venv/bin/python -m pip install -r requirements.txt --no-cache-dir
