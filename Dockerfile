FROM nginxinc/nginx-unprivileged:1.29.1-alpine

USER root
RUN apk add --no-cache python3 py3-pillow
COPY tools/coloring-pages-import /usr/local/bin/coloring-pages-import
COPY tools/coloring-pages-regenerate-derivatives /usr/local/bin/coloring-pages-regenerate-derivatives
COPY metadata/categories.json /usr/local/share/coloring-pages/categories.json
COPY deploy/existing-derivative-regeneration-v1.json /usr/local/share/coloring-pages/existing-derivative-regeneration-v1.json
RUN chmod 0555 /usr/local/bin/coloring-pages-import /usr/local/bin/coloring-pages-regenerate-derivatives \
    && test -x /usr/local/bin/coloring-pages-regenerate-derivatives \
    && test -f /usr/local/share/coloring-pages/existing-derivative-regeneration-v1.json
USER 101

COPY deploy/nginx.conf /etc/nginx/nginx.conf
COPY index.html detail.html print.html /usr/share/nginx/html/
COPY css /usr/share/nginx/html/css
COPY js /usr/share/nginx/html/js
COPY assets /usr/share/nginx/html/assets

EXPOSE 8080
