#!/bin/bash

# Initialize and update all submodules
git submodule update --init --recursive

# Loop through each submodule
git submodule foreach 'git checkout main && git pull origin main'
