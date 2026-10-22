FROM nginxinc/nginx-unprivileged:1.29.1-alpine

USER root
RUN apk add --no-cache python3 py3-pillow
COPY tools/coloring-pages-import /usr/local/bin/coloring-pages-import
COPY tools/coloring-pages-regenerate-derivatives /usr/local/bin/coloring-pages-regenerate-derivatives
COPY tools/coloring-pages-print-master /usr/local/bin/coloring-pages-print-master
COPY metadata/categories.json /usr/local/share/coloring-pages/categories.json
COPY deploy/existing-derivative-regeneration-v1.json /usr/local/share/coloring-pages/existing-derivative-regeneration-v1.json
RUN chmod 0555 /usr/local/bin/coloring-pages-import /usr/local/bin/coloring-pages-regenerate-derivatives /usr/local/bin/coloring-pages-print-master \
    && test -x /usr/local/bin/coloring-pages-regenerate-derivatives \
    && test -x /usr/local/bin/coloring-pages-print-master \
    && python3 -c 'import json; p="/usr/local/share/coloring-pages/existing-derivative-regeneration-v1.json"; d=json.load(open(p, encoding="utf-8")); assert d["schema"] == "rozkalns.coloring-pages.existing-derivative-regeneration.v1"; assert d["issue"] == 74' \
    && python3 -c 'from PIL import ImageFont; ImageFont.load_default(size=24)' \
    && python3 -c 'import importlib.machinery, importlib.util; p="/usr/local/bin/coloring-pages-print-master"; l=importlib.machinery.SourceFileLoader("cp_print_master", p); s=importlib.util.spec_from_loader(l.name, l); m=importlib.util.module_from_spec(s); l.exec_module(m); assert m.TARGET_SIZE == (2480, 3508); assert m.OUTER_WHITE_BORDER == 1; assert m.PRINT_SAFE_MARGIN_PX == 177; assert m.PNG_COMPRESS_LEVEL == 6'
USER 101

COPY deploy/nginx.conf /etc/nginx/nginx.conf
COPY index.html detail.html print.html /usr/share/nginx/html/
COPY tiere.html fahrzeuge.html alphabet.html lernen.html figuren.html jahreszeiten.html essen-natur.html /usr/share/nginx/html/
COPY stats.html traffic.html kita.html kalender.html /usr/share/nginx/html/
COPY robots.txt sitemap.xml /usr/share/nginx/html/
COPY metadata/topics.json /usr/share/nginx/html/topics.json
COPY google7e69cee667102729.html /usr/share/nginx/html/
COPY css /usr/share/nginx/html/css
COPY js /usr/share/nginx/html/js
COPY assets /usr/share/nginx/html/assets

EXPOSE 8080
