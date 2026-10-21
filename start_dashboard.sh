#!/bin/bash
echo "Starting Dashboard System..."
cd "$(dirname "$0")"
source dashboard_env/bin/activate
python app.py
