#!/bin/bash

# Initialize and update all submodules
git submodule update --init --recursive

# Loop through each submodule with custom branch handling
git submodule foreach '
  if [ "$path" = "packages/get-nwbfile-info" ]; then
    git checkout jfm-dev && git pull origin jfm-dev
  else
    git checkout main && git pull origin main
  fi
'
