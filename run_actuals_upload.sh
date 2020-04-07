#!/bin/bash

# environment setup
source $HOME/.bash_profile
cd $(dirname "$0")

# make predictions
python add_actuals.py
