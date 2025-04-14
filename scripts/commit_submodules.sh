#!/bin/bash

# Get current timestamp for commit message
timestamp=$(date '+%Y-%m-%d %H:%M:%S')

# Loop through each submodule
git submodule foreach '
    # Add all changes
    git add -A

    # Only commit and push if there are changes
    if [ -n "$(git status --porcelain)" ]; then
        git commit -m "Auto-commit: $timestamp"
        git push origin HEAD
        echo "Changes pushed for $(basename $(pwd))"
    else
        echo "No changes in $(basename $(pwd)). Trying push"
        git push origin HEAD
    fi
'
