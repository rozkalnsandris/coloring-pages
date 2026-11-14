# Topic Landing v1 artwork gate (#567)

The owner approved the exact ImageGen rendition `dae01964-7ae9-4899-9663-9823c2602e24`
for the `Herbst` website Topic hero in this project conversation (2026-11-14).

- Approved artwork: original illustration with the brown-and-white Ausmalwiese dog in a red harness, orange pumpkins, leaves and a **small `Ausmalwiese.de` logo at the lower-right**. This is a website illustration, **not** a coloring-page print original.
- Original generated PNG: RGB, `1755×896`, `1,782,097` bytes, SHA-256 `b64df1cfcc5884cc129b726d8684b1ed0fedbd6d2da2946f8d4bf743614a4190`.
- Prepared candidate WebP (Pillow WebP quality 82, method 6, no resize): RGB, `1755×896`, `119,446` bytes, SHA-256 `d077de2efb5b291cf41140722958aa771fea6bd716da387a37458af700b0ad74`.
- Artwork and brand provenance: generated under the owner-supplied mascot and logo references in this conversation; approved by the owner. No third-party licensed raster source.
- **Verified GitHub handoff (2026-11-14):** owner uploaded the approved WebP to `assets/herbst-topic-hero.webp` on the issue branch in commit `97baa144badb96aa2505f692234047b292353230`. The GitHub blob SHA-1 `3b935fac2d9c817ff2d0fb8f004a539c8683bbf3` exactly matches the local approved WebP's Git object ID; this verifies identical file bytes. Its SHA-256, dimensions and byte count are as listed above.
- The validated WebP is now referenced by a real HTML `<img>` on `/herbst` and through the reviewed manifest for the `?topic=herbst` browse fallback. No unrelated Topic media were invented or linked.
- The image is 1755×896 at 119,446 bytes; responsive CSS uses `object-fit: contain` to keep the dog and the small bottom-right `Ausmalwiese.de` logo visible without cropping. HTML `width`/`height` reserve aspect ratio, and the main illustration loads eagerly with high priority.
- Editorial texts, canonical, sitemap and six static crawlable /herbst seed cards must remain unchanged. Other runtime-managed Topics get only a safe label-based browse fallback until their separate asset/editorial approval.
- Explicit owner `MERGE` remains mandatory. No LIVE, content staging/import, GSC mutation, mass SEO pages or other Topics are covered here.

References: https://developers.google.com/search/docs/appearance/google-images ; https://www.w3.org/WAI/tutorials/images/decorative/ ; https://web.dev/articles/optimize-cls/ .
