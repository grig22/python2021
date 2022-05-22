#!/bin/bash
set -eux
rm -rf venv
python3.10 -m venv venv
venv/bin/python -m pip install -r requirements.txt
echo УСПЕХ
