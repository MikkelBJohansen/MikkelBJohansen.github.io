#!/bin/bash

# Navigate to your repository directory
cd /home/pi/danish_data_project

# Add changes to git
git add index.html

# Commit changes with a timestamp
git commit -m "Automated update: $(date '+%Y-%m-%d %H:%M:%S')"

# Push changes to GitHub
git push origin main
