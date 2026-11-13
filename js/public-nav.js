(() => {
  "use strict";
  const button = document.querySelector(".menu-button");
  const nav = document.querySelector("#mobile-nav");
  if (!button || !nav) return;
  function setOpen(open) { button.setAttribute("aria-expanded", String(open)); nav.hidden = !open; const label = button.querySelector(".sr-only"); if (label) label.textContent = open ? "Menü schließen" : "Menü öffnen"; }
  button.addEventListener("click", () => setOpen(button.getAttribute("aria-expanded") !== "true"));
  nav.addEventListener("click", (event) => { if (event.target.closest("a")) setOpen(false); });
  document.addEventListener("keydown", (event) => { if (event.key === "Escape" && !nav.hidden) { setOpen(false); button.focus(); } });
})();
