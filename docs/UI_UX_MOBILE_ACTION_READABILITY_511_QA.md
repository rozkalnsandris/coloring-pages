# UI/UX audit #511 — final QA: mobile action readability

Date: 2026-11-13. Baseline source: `0dfeb67578baf72fbe3f3c760ffeb9793c9996f4`.

The original audit noted that important `.outline-link` actions become unusually small on narrow screens. Current source confirmed a cascade from 12 px at the main mobile breakpoint to 11 px at `<=430px` and 10 px at `<=360px`.

This is documented as a readability/consistency defect, not as a claim that WCAG defines a universal minimum text size. The existing controls already retain their touch target sizing; this correction keeps the narrow-screen action text at 12 px and allows wrapping below 430 px so longer German labels do not need to be compressed to fit.

Scope is intentionally limited to `.outline-link` actions. Badge/count typography and the broader visual system are unchanged. All 19 public HTML consumers keep exact `app.css` content-hash references.
