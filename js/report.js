// Optional, privacy-minimal per-activity error reporting; never blocks printing.
(() => {
  const root = document.querySelector("[data-detail-root]");
  const openButton = document.querySelector("[data-report-open]");
  const panel = document.querySelector("[data-report-panel]");
  const closeButton = document.querySelector("[data-report-close]");
  const form = document.querySelector("[data-report-form]");
  const status = document.querySelector("[data-report-status]");
  const submit = document.querySelector("[data-report-submit]");
  if (!root || !openButton || !panel || !form || !status || !submit) return;

  let activityId = "";
  let page = 1;
  let busy = false;

  function say(message, state = "") {
    status.textContent = message;
    if (state) status.dataset.state = state;
    else delete status.dataset.state;
  }

  function close() {
    if (busy) return;
    panel.hidden = true;
    openButton.setAttribute("aria-expanded", "false");
    openButton.focus();
  }

  document.addEventListener("ausmalwiese:detail-loaded", (event) => {
    const id = event.detail?.id;
    if (typeof id !== "string" || !/^[a-z0-9][a-z0-9_-]{0,79}$/i.test(id)) return;
    activityId = id;
    page = Math.max(1, Number(root.dataset.pageIndex || 0) + 1);
    openButton.hidden = false;
  });

  document.addEventListener("ausmalwiese:page-change", (event) => {
    if (Number.isInteger(event.detail?.index)) page = event.detail.index + 1;
  });

  openButton.addEventListener("click", () => {
    if (!activityId) return;
    panel.hidden = false;
    openButton.setAttribute("aria-expanded", "true");
    say("");
    form.reset();
    form.querySelector('input[name="reason"]')?.focus();
  });

  closeButton?.addEventListener("click", close);
  panel.addEventListener("keydown", (event) => {
    if (event.key === "Escape") close();
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (busy || !activityId) return;
    const reason = form.elements.namedItem("reason")?.value;
    if (!reason) return;

    busy = true;
    submit.disabled = true;
    closeButton.disabled = true;
    say("");
    try {
      const response = await fetch("/api/report", {
        method: "POST",
        headers: { "content-type": "application/json", accept: "application/json" },
        credentials: "same-origin",
        cache: "no-store",
        body: JSON.stringify({ id: activityId, page, reason }),
      });
      const result = await response.json().catch(() => null);
      if (!response.ok || result?.ok !== true) throw new Error("not sent");
      panel.hidden = true;
      openButton.setAttribute("aria-expanded", "false");
      say("✓ Danke! Deine Meldung wurde gesendet.", "success");
      openButton.focus();
    } catch {
      say("Die Meldung konnte nicht gesendet werden. Bitte versuche es später erneut.", "error");
    } finally {
      busy = false;
      submit.disabled = false;
      closeButton.disabled = false;
    }
  });
})();
