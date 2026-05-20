#!/bin/sh
set -eu

normalize_path() {
  value="${1:-/}"
  if [ -z "$value" ]; then
    value="/"
  fi
  case "$value" in
    /*) ;;
    *) value="/$value" ;;
  esac
  while [ "$value" != "/" ] && [ "${value%/}" != "$value" ]; do
    value="${value%/}"
  done
  printf '%s' "$value"
}

app_base_path="$(normalize_path "${APP_BASE_PATH:-/}")"
api_base_path="$(normalize_path "${API_BASE_PATH:-/api}")"
backend_upstream="${BACKEND_UPSTREAM:-http://backend:8000}"

cat >/usr/share/nginx/html/config.js <<EOF
window.__TODO_CONFIG__ = {
  appBasePath: "${app_base_path}",
  apiBasePath: "${api_base_path}"
};
EOF

cat >/etc/nginx/conf.d/default.conf <<EOF
server {
  listen 80;
  server_name _;

EOF

if [ "$app_base_path" = "/" ]; then
  cat >>/etc/nginx/conf.d/default.conf <<'EOF'
  location / {
    root /usr/share/nginx/html;
    try_files $uri $uri/ /index.html;
  }

EOF
else
  cat >>/etc/nginx/conf.d/default.conf <<EOF
  location = ${app_base_path} {
    return 301 ${app_base_path}/;
  }

  location ^~ ${app_base_path}/ {
    alias /usr/share/nginx/html/;
    try_files \$uri \$uri/ /index.html;
  }

  location = / {
    return 302 ${app_base_path}/;
  }

EOF
fi

cat >>/etc/nginx/conf.d/default.conf <<EOF
  location = ${api_base_path} {
    return 301 ${api_base_path}/;
  }

  location ^~ ${api_base_path}/ {
    proxy_pass ${backend_upstream}/;
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
  }
}
EOF

exec nginx -g 'daemon off;'