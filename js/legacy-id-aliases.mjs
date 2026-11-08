const SCHEMA = "rozkalns.coloring-pages.legacy-id-aliases.v1";
const SHA256 = /^[a-f0-9]{64}$/;
const OLD_ID = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const NEW_ID = /^[0-9]{7}$/;
const TOP_KEYS = ["aliases","aliases_sha256","issue","schema","source_catalog_count","source_catalog_sha256","source_legacy_count","source_plan_manifest_sha256"].sort().join(",");
const ALIAS_KEYS = ["new_id","old_id"].sort().join(",");
export function validateLegacyIdAliases(doc) {
  if (!doc || typeof doc !== "object" || Array.isArray(doc) || Object.keys(doc).sort().join(",") !== TOP_KEYS ||
      doc.schema !== SCHEMA || doc.issue !== 457 || !SHA256.test(doc.source_catalog_sha256) ||
      !SHA256.test(doc.source_plan_manifest_sha256) || !SHA256.test(doc.aliases_sha256) ||
      !Number.isSafeInteger(doc.source_catalog_count) || doc.source_catalog_count < 1 ||
      !Number.isSafeInteger(doc.source_legacy_count) || !Array.isArray(doc.aliases) ||
      doc.aliases.length !== doc.source_legacy_count || doc.aliases.length < 1 || doc.aliases.length > 200) {
    throw new TypeError("Invalid legacy ID alias document");
  }
  const oldIds=new Set(), newIds=new Set();
  for (const item of doc.aliases) {
    if (!item || typeof item !== "object" || Array.isArray(item) || Object.keys(item).sort().join(",") !== ALIAS_KEYS ||
        typeof item.old_id !== "string" || !OLD_ID.test(item.old_id) || NEW_ID.test(item.old_id) ||
        typeof item.new_id !== "string" || !NEW_ID.test(item.new_id) || oldIds.has(item.old_id) || newIds.has(item.new_id)) {
      throw new TypeError("Invalid legacy ID alias entry");
    }
    oldIds.add(item.old_id); newIds.add(item.new_id);
  }
  return doc;
}
export async function loadLegacyIdAliases(fetchImpl = globalThis.fetch) {
  if (typeof fetchImpl !== "function") throw new TypeError("fetch unavailable");
  const response = await fetchImpl("/legacy-id-aliases.json", { cache:"no-store", credentials:"same-origin" });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error("legacy ID aliases unavailable");
  return validateLegacyIdAliases(await response.json());
}
export function translateLegacyBasketIds(savedIds, catalog, aliasDocument = null) {
  if (!Array.isArray(savedIds)) throw new TypeError("Basket IDs must be an array");
  if (!Array.isArray(catalog)) throw new TypeError("Fresh catalogue array required");
  if (aliasDocument === null) return { ids:[...savedIds], changed:false };
  const doc=validateLegacyIdAliases(aliasDocument);
  const aliases=new Map(doc.aliases.map((item)=>[item.old_id,item.new_id]));
  const counts=new Map();
  for (const entry of catalog) if (typeof entry?.id === "string") counts.set(entry.id,(counts.get(entry.id)||0)+1);
  const ids=[], seen=new Set(); let changed=false;
  for (const id of savedIds) {
    const target=aliases.get(id);
    const candidate=target && counts.get(target)===1 ? target : id;
    if (candidate !== id) changed=true;
    if (seen.has(candidate)) { changed=true; continue; }
    seen.add(candidate); ids.push(candidate);
  }
  return { ids, changed };
}
