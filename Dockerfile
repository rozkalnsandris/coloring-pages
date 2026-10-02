FROM python:3.12.14-slim-bookworm@sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254 AS build
WORKDIR /src

COPY metadata ./metadata
COPY originals ./originals
COPY tools ./tools
COPY index.html detail.html print.html ./
COPY css ./css
COPY js ./js
COPY assets ./assets

RUN python3 tools/build_catalog.py --output /tmp/site/catalog.json \
    && mkdir -p /tmp/site/css /tmp/site/js /tmp/site/assets \
    && cp index.html detail.html print.html /tmp/site/ \
    && cp -R css/. /tmp/site/css/ \
    && cp -R js/. /tmp/site/js/ \
    && cp -R assets/. /tmp/site/assets/

FROM nginxinc/nginx-unprivileged:1.29.1-alpine
COPY deploy/nginx.conf /etc/nginx/nginx.conf
COPY --from=build /tmp/site /usr/share/nginx/html
EXPOSE 8080
