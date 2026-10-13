# Webfont delivery (Baloo 2 + Nunito)

The site retains its original display and body typefaces. Before this change each public page
requested a Google Fonts CSS stylesheet, then downloaded the font files cross-origin.
Now `css/fonts.css` declares two self-hosted, Latin variable WOFF2 files under
`assets/fonts/`. Their content SHA-256 prefixes are part of filenames; nginx serves
these immutable resources with a one-year public cache policy.

The HTML preloads both visible families with `as="font"`, `type="font/woff2"` and
`crossorigin` on normal pages. The print page preloads only Nunito; unused Baloo 2 stays lazy.
`font-display: optional` avoids visible late font swapping, but on an exceptionally slow
first visit a fallback can remain for that navigation. Do not promise identical first paint
under all network conditions; trading that guarantee for immediate visible fallback is intentional.

Source/provenance: fontsource/font-files exact commit
`c3f4e3e5a664d2c3002e800050ce809a790d7281`; SIL Open Font License 1.1
stored with each font in `assets/fonts/OFL-*.txt`. The two fonts were extracted without
editing their binary content from the existing legal Draft PR #158's base64 WOFF2 sources.
The Latin subset includes German umlauts and ß.

Verification after merge: cold + warm network runs, slow 3G/mobile and desktop,
Firefox and Chrome, external font blocking and reload/back navigation. Measure FCP/CLS,
font requests and calculated font family. These browser tests are not proven by unit CI.
Review compatibility before merging Draft PR #158, which contains an older embedded-font
delivery scheme for the same names and files.
