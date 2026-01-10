#!/bin/bash
# Simple Git Commit Helper

echo "=== Staging all changes ==="
git add .

echo "=== Enter commit message ==="
read -r commit_msg

if [ -z "$commit_msg" ]; then
    echo "No commit message provided. Aborting."
    exit 1
fi

echo "=== Committing changes ==="
git commit -m "$commit_msg"

echo "=== Do you want to push to remote? (y/n) ==="
read -r push_choice

if [ "$push_choice" = "y" ] || [ "$push_choice" = "Y" ]; then
    git push
    echo "Changes pushed to remote."
else
    echo "Commit complete. Not pushed."
fi
