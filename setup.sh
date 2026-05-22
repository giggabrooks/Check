#!/bin/bash

# Install Playwright browsers
python -m playwright install chromium

# Clean up
rm -rf /root/.cache/pip
