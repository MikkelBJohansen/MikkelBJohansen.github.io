#!/bin/bash

# Navigate to your repository directory
cd /home/pi/danish_data_project || exit

# Log start of script
echo "Running auto_commit.sh at $(date)" >> /home/pi/danish_data_project/git_log.txt

# Pull remote changes
git pull origin main >> /home/pi/danish_data_project/git_log.txt 2>&1

# Add changes to git
git add index.html graph_html.py auto_commit.sh .gitignore >> /home/pi/danish_data_project/git_log.txt 2>&1

# Commit changes with a timestamp, even if there are no changes
git commit --allow-empty -m "Automated update: $(date '+%Y-%m-%d %H:%M:%S')" >> /home/pi/danish_data_project/git_log.txt 2>&1

# Push changes to GitHub
git push origin main >> /home/pi/danish_data_project/git_log.txt 2>&1
