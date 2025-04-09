#!/bin/bash
set -e

# Check if container exists using filter instead of format+grep
EXISTS=$(docker ps -a -q -f name=^{{ container_name }}$)
if [ -z "$EXISTS" ]; then
    echo "Container {{ container_name }} does not exist."
    exit 0
fi

# Check if container is running using filter instead of format+grep
RUNNING=$(docker ps -q -f name=^{{ container_name }}$)
if [ -n "$RUNNING" ]; then
    docker stop "{{ container_name }}"
    echo "Container {{ container_name }} stopped."
fi

# Remove container if requested
if {{ 'true' if remove_container else 'false' }}; then
    docker rm -f "{{ container_name }}"
    echo "Container {{ container_name }} removed."
fi