#!/bin/bash

# Navigate to your repository directory
cd /home/pi/danish_data_project || exit

# Log start of script
echo "Running auto_commit.sh at $(date)" >> /home/pi/danish_data_project/git_log.txt

# Pull remote changes
/usr/bin/git pull origin main >> /home/pi/danish_data_project/git_log.txt 2>&1

# Add changes to git
/usr/bin/git add index.html graph_html.py auto_commit.sh .gitignore >> /home/pi/danish_data_project/git_log.txt 2>&1

# Commit changes with a timestamp (no --allow-empty)
/usr/bin/git commit -m "Automated update: $(date '+%Y-%m-%d %H:%M:%S')" >> /home/pi/danish_data_project/git_log.txt 2>&1

# Push changes to GitHub
/usr/bin/git push origin main >> /home/pi/danish_data_project/git_log.txt 2>&1
