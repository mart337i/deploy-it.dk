#!/bin/bash
# Get the script's directory
SCRIPT_DIR=$(dirname "$(realpath "$0")")
USERNAME=$(whoami)
NAME=deploy-it
DIR=$SCRIPT_DIR
RunningDIR=$SCRIPT_DIR
WORKERS=3
WORKER_CLASS=uvicorn.workers.UvicornWorker
BIND_SUB=0.0.0.0:8000
LOG_LEVEL=info

# Change to the directory where the app runs
cd $RunningDIR

# Create logs directory if it doesn't exist
mkdir -p $DIR/logs
echo $(ls)

# Execute gunicorn using the path to the virtual environment
gunicorn clicx.cli.server:api \
  --name $NAME \
  --workers $WORKERS \
  --worker-class $WORKER_CLASS \
  -e KEEP_ALIVE="50" \
  --user=$USERNAME \
  --group=$USERNAME \
  --bind=$BIND_SUB \
  --log-level=$LOG_LEVEL \
  --log-file=$DIR/logs/application.log