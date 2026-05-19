FROM nginx:stable-alpine
COPY frontend/index.html /usr/share/nginx/html/index.html
COPY frontend/app.js /usr/share/nginx/html/app.js
COPY frontend/styles.css /usr/share/nginx/html/styles.css
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf
