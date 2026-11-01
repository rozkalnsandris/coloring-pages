#!/usr/bin/env python3
"""Render a candidate origin mirror config to a NEW file; never activate it.

Default Dockerfile/Compose do not reference this tool or its output. The separate
opt-in Dockerfile.origin-counting bakes it in; activation requires explicit wiring.
"""
from __future__ import annotations

import argparse
from pathlib import Path

KEY = r"(?![iI][dD]=)[A-Za-z0-9_.~-]+"
VALUE = r"(?:[A-Za-z0-9_.~!$'()*+,:@/?=-]|%[0-9A-Fa-f]{2})*"
QUERY_RE = (r"^(?=.{1,2048}$)(?:" + KEY + "=" + VALUE + r"&)*"
            r"id=(?<origin_matched_id>[0-9]{7})(?:&" + KEY + "=" + VALUE + r")*$")

MAP = '''
    # No query values except a single literal seven-digit id leave this process.
    map $args $origin_query_id {
        default "";
        "~QUERY_RE" $origin_matched_id;
    }
'''.replace("QUERY_RE", QUERY_RE)

LOCATIONS = '''
        # Candidate only: ordinary HTML delivery retains its original cache policy.
        location = /detail.html {
            # The counting variant does not retain original detail request URLs.
            access_log off;
            # Mirror failures use the main connection log as well. The isolated
            # failure probe proves that suppressing only the mirror log leaks
            # original query/referrer; suppress detail-route error logs too.
            error_log /dev/null crit;
            set $origin_frozen_id $origin_query_id;
            set $origin_frozen_method $request_method;
            mirror /__origin_count;
            mirror_request_body off;
            add_header Cache-Control "no-cache" always;
            try_files $uri =404;
        }

        location = /__origin_count {
            internal;
            access_log off;
            # Nginx proxy errors can otherwise include the original query.
            error_log /dev/null crit;
            if ($origin_frozen_method != GET) { return 204; }
            if ($origin_frozen_id = "") { return 204; }
            # Clear the subrequest args explicitly; a ? in static proxy_pass
            # is a literal URI suffix and can still append inherited args.
            set $args "";
            proxy_method POST;
            proxy_pass_request_headers off;
            proxy_pass_request_body off;
            proxy_set_header Host origin-counter.invalid;
            proxy_set_header Content-Type application/json;
            proxy_set_header Content-Length 21;
            proxy_set_header Connection close;
            proxy_set_body '{"page_id":"$origin_frozen_id"}';
            proxy_http_version 1.0;
            proxy_cache off;
            proxy_next_upstream off;
            proxy_connect_timeout 100ms;
            proxy_send_timeout 100ms;
            proxy_read_timeout 200ms;
            proxy_buffering off;
            proxy_max_temp_file_size 0;
            proxy_pass http://unix:/run/ausmalwiese-pageview/origin.sock:/internal/origin-count;
        }
'''


def render(base: str) -> str:
    anchor = "        location = /health {"
    if (base.count("http {") != 1 or base.count(anchor) != 1
            or "origin_frozen_id" in base or "location = /detail.html" in base):
        raise ValueError("NGINX_BASE_DRIFT")
    return base.replace("http {", "http {\n" + MAP, 1).replace(
        anchor, LOCATIONS + "\n" + anchor, 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    text = render(args.base.read_text(encoding="utf-8"))
    with args.output.open("x", encoding="utf-8") as handle:
        handle.write(text)


if __name__ == "__main__":
    main()
