#!/bin/bash
set -e

# Run the main app
python app.py

# Fix ownership of all files (including newly created ones)
if [ -n "$HOST_UID" ] && [ -n "$HOST_GID" ]; then
    echo "Changing ownership of /workspace to ${HOST_UID}:${HOST_GID}"
    chown -R ${HOST_UID}:${HOST_GID} /workspace || true
fi