#!/bin/bash
# manifestme.sh

# Write a manifest.json file for a Shiny Python app,
# for deploying to Posit Connect.

# Install rsconnect package for Python (use python3 -m pip so it works when pip is not on PATH)
python3 -m pip install rsconnect-python
# Write a manifest.json file for the Shiny Python app (run with venv activated so rsconnect is on PATH)
rsconnect write-manifest shiny 04_deployment/positconnectcloud/shinypy