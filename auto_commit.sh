#!/bin/bash

# Navigate to your repository directory
cd /home/pi/danish_data_project

# Pull remote changes
git pull origin main

# Add changes to git
git add index.html graph_html.py auto_commit.sh .gitignore

# Commit changes with a timestamp
git commit -m "Automated update: $(date '+%Y-%m-%d %H:%M:%S')"

# Push changes to GitHub
git push origin main
