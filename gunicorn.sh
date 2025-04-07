#!/bin/bash

# Get the script's directory
SCRIPT_DIR=$(dirname "$(realpath "$0")")

NAME=deploy-it
DIR=$SCRIPT_DIR/  # Adjust based on your relative structure
RunningDIR=$SCRIPT_DIR/  # Assuming the script is in the backend directory
USER=$USER
GROUP=$USER
WORKERS=3
WORKER_CLASS=uvicorn.workers.UvicornWorker
VENV=$DIR.venv/bin/activate

# Switch to 0.0.0.0:8000 if you want the service to be accessible to anyone outside localhost
BIND_SUB=127.0.0.1:8000
LOG_LEVEL=info

# Change to the directory where the app runs
cd $RunningDIR
source $VENV

exec gunicorn clicx.cli.server:api \
  --name $NAME \
  --workers $WORKERS \
  --worker-class $WORKER_CLASS \
  -e KEEP_ALIVE="50" \
  --user=$USER \
  --group=$GROUP \
  --bind=$BIND_SUB \
  --log-level=$LOG_LEVEL \
  --log-file=$DIR/logs/application.log