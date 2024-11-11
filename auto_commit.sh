#!/bin/bash

# Navigate to your repository directory
cd /home/pi/danish_data_project || exit

# Log start of script
echo "Running auto_commit.sh at $(date)" >> /home/pi/danish_data_project/git_log.txt

# Add things to Git
git add .

# Commit changes with a timestamp (no --allow-empty)
git commit -m "Automated update: $(date '+%Y-%m-%d %H:%M:%S')" >> /home/pi/danish_data_project/git_log.txt 2>&1

# Push changes to GitHub
git push origin main >> /home/pi/danish_data_project/git_log.txt 2>&1

# Check if the push was successful and send a message
if [ $? -eq 0 ]; then
    echo "Push to GitHub succeeded."
else
    echo "Push to GitHub failed."
fi
