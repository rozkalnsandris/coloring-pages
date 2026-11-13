let catalogPromise = null;

export function loadCatalog() {
  if (!catalogPromise) {
    catalogPromise = (async () => {
      const response = await fetch("/catalog.json", {
        cache: "no-store",
        credentials: "same-origin",
      });
      if (!response.ok) throw new Error("catalog unavailable");
      const payload = await response.json();
      if (!Array.isArray(payload)) throw new Error("invalid catalog");
      return payload;
    })().catch((error) => {
      catalogPromise = null;
      throw error;
    });
  }
  return catalogPromise;
}
