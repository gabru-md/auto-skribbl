#!/bin/bash

source ./.venv/bin/activate
export FLASK_DEBUG=1
export FLASK_APP=server.py
flask run