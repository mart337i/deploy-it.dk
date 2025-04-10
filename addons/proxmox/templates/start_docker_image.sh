#!/bin/bash
set -e
# Debug output to see what values are being used
echo "DEBUG: image_name='{{ image_name }}'"
echo "DEBUG: container_name='{{ container_name }}'"
echo "DEBUG: port_mapping='{{ port_mapping }}'"
echo "DEBUG: volume_mapping='{{ volume_mapping }}'"
echo "DEBUG: env_vars='{{ env_vars }}'"

# Simplest check - avoid format strings completely
RUNNING=$(docker ps -q -f name=^{{ container_name }}$)
if [ -n "$RUNNING" ]; then
    echo "Container {{ container_name }} is already running."
    exit 0
fi

# Simple check for stopped container
EXISTS=$(docker ps -a -q -f name=^{{ container_name }}$)
if [ -n "$EXISTS" ]; then
    echo "Starting existing container: {{ container_name }}"
    docker start "{{ container_name }}"
    exit 0
fi

# Create and start a new container
echo "Creating and starting new container {{ container_name }} from image {{ image_name }}"
# Add -p before port mapping if not already present
{% if port_mapping and not port_mapping.startswith('-p') %}
PORT_ARG="-p {{ port_mapping }}"
{% else %}
PORT_ARG="{{ port_mapping }}"
{% endif %}

docker run -d --name {{ container_name }} $PORT_ARG {% if volume_mapping %}{{ volume_mapping }}{% endif %} {% if env_vars %}{{ env_vars }}{% endif %} {{ image_name }}
echo "Successfully started Docker container: {{ container_name }}"