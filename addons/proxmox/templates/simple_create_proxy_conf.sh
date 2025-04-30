#!/bin/bash

# Exit on any error
set -e

# Check if script is run as root
if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: This script must be run as root" >&2
    exit 1
fi

TEMPLATE_PATH="/etc/nginx/sites-available/include/{{ hostname }}.conf"
mkdir -p $(dirname $TEMPLATE_PATH) 2>/dev/null || { echo "ERROR: Failed to create template directory"; exit 1; }

cat > "$TEMPLATE_PATH" << 'EOF'
server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name {{ hostname }}.deploy-it.dk;
    # SSL configuration - using the wildcard certificate
    ssl_certificate /etc/letsencrypt/live/deploy-it.dk/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/deploy-it.dk/privkey.pem;
   
    # Proxy to ubuntu-cloud backend
    location / {
        proxy_pass http://{{ ip }}:{{ port }};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
EOF

systemctl reload nginx
exit 0