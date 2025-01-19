#!/bin/bash

while true; do
  # Check current hour
  current_hour=$(date +%H)

  # Run scrapy crawl only between 8AM and 11PM
  if [[ $current_hour -ge 8 ]] && [[ $current_hour -lt 23 ]]; then
    scrapy crawl argenprop

    if [ $? -eq 0 ]; then
      echo "Scrapy finished successfully, running sync_notion.py"
      python3 sync_notion.py
    else
      echo "Scrapy failed, skipping sync_notion.py"
      exit 1
    fi
  fi

  # Sleep for 20 minutes regardless of time check
  sleep 1200
done
