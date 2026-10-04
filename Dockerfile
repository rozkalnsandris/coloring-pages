FROM nginxinc/nginx-unprivileged:1.29.1-alpine

USER root
RUN apk add --no-cache python3 py3-pillow
COPY tools/coloring-pages-import /usr/local/bin/coloring-pages-import
COPY tools/coloring-pages-migrate-png-only /usr/local/bin/coloring-pages-migrate-png-only
COPY metadata/categories.json /usr/local/share/coloring-pages/categories.json
COPY deploy/legacy-png-migration-v1.json /usr/local/share/coloring-pages/legacy-png-migration-v1.json
RUN chmod 0555 /usr/local/bin/coloring-pages-import /usr/local/bin/coloring-pages-migrate-png-only
USER 101

COPY deploy/nginx.conf /etc/nginx/nginx.conf
COPY index.html detail.html print.html /usr/share/nginx/html/
COPY css /usr/share/nginx/html/css
COPY js /usr/share/nginx/html/js
COPY assets /usr/share/nginx/html/assets

EXPOSE 8080
