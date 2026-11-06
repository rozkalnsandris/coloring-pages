# GoatCounter SIMPLE (#442) — consent-gated activation source

Purpose: estimate visits/sessions, acquisition sources, Instagram campaigns and most-viewed catalog pages while keeping existing Like/Print engagement separate.

## Current application contract

- Public index.html and detail.html load only the local js/goatcounter-simple.js wrapper.
- The wrapper is in data-goatcounter-simple="consent" mode. Without an explicit "Analyse erlauben" choice it does not request gc.zgo.at/count.v5.js and does not send /count traffic.
- The first-party preference key is ausmalwiese.analytics-consent.v1 with only granted/denied values. "Analyse-Einstellungen" reopens the choice; withdrawal prevents future page analytics. Website browsing, printing and Likes remain available without consent.
- After consent, the pinned upstream count.v5.js is loaded with SRI and manual no_onload/no_events. The wrapper sends at most one page attempt per document: / for the homepage or /ausmalbild/<7-digit-id> after the catalog-confirmed detail page is ready.
- Raw location.search is never forwarded. Only the exact allowlisted Instagram UTM source/medium/campaign triple may enter q. Referrer is reduced to the origin or the allowlisted Instagram label.
- datenschutz.html describes the actual optional flow, consent choice, Cloudflare transport, external script load, normalized event fields, transient IP/User-Agent use for session estimation and withdrawal.
- The application does not expose GoatCounter admin/report/API routes and does not persist raw visitor IP addresses in browser code.

## Runtime boundary

GitHub source does not prove the current RPi5/Cloudflare runtime. The public /count ingress, GoatCounter Collect configuration and private admin isolation remain runtime facts that must be independently current before owner merge/activation. A source merge does not authorize unrelated Cloudflare, DB, credential or host mutations.

## Release gate

This change is an application-image input. Exact owner MERGE authorization is required. If merged, only the repository's existing bounded coloring-pages application auto-LIVE flow may run. After deployment, verify that denial creates no count request, consent creates one expected normalized event, revocation prevents future analytics and normal browse/print/Like behavior is unchanged.
