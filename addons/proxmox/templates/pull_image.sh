#!/bin/bash
set -e

# Pull the specified Docker image
docker pull "{{ image_name }}"
echo "Successfully pulled Docker image: {{ image_name }}"