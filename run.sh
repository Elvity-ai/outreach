#!/usr/bin/env bash

# Source the assume_role.sh script to load the temporary path-restricted AWS credentials
source ./assume_role.sh

# If the assume_role script succeeded, start Gemini CLI with the specified model
if [ $? -eq 0 ]; then
    # Parse optional session ID parameter (if first argument does not start with '-')
    SESSION_ARG=""
    if [ -n "$1" ] && [[ "$1" != -* ]]; then
        SESSION_ID="$1"
        SESSION_ARG="--resume $SESSION_ID"
        shift
        echo "🔄 Resuming session: $SESSION_ID"
    fi

    echo "🚀 Starting Gemini CLI with model gemini-3.5-flash..."
    echo "--------------------------------------------------------"
    export NANOBANANA_MODEL=gemini-3.1-flash-image
    exec gemini -m gemini-3.5-flash $SESSION_ARG "$@"
else
    echo "❌ Error: Failed to load credentials. Aborting."
    exit 1
fi
