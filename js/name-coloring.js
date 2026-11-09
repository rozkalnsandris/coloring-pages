const WIDTH = 2480;
const HEIGHT = 3508;
const SAFE = 177;
const PX_PER_METRE = 11811;
const FONT = '"Baloo 2"';
const ALLOWED = /^[A-Za-zÄÖÜäöüß]+(?:[ -][A-Za-zÄÖÜäöüß]+)?$/u;

const form = document.querySelector("[data-name-form]");
const input = document.querySelector("[data-name-input]");
const canvas = document.querySelector("[data-name-canvas]");
const error = document.querySelector("[data-name-error]");
const status = document.querySelector("[data-name-status]");
const downloadButton = document.querySelector("[data-name-download]");
const printButton = document.querySelector("[data-name-print]");
const clearButton = document.querySelector("[data-name-clear]");
const menuButton = document.querySelector(".menu-button");
const mobileNav = document.querySelector("#mobile-nav");

let renderedText = "";
let exportBlob = null;
let exportUrl = "";

function normalizeValue(value) {
  return value.normalize("NFC").trim().replace(/\s+/gu, " ");
}

function lettersOnlyCount(value) {
  return Array.from(value).filter((char) => /[A-Za-zÄÖÜäöüß]/u.test(char)).length;
}

function validateValue(raw) {
  const value = normalizeValue(raw);
  if (!value) return { ok: false, value, message: "Bitte gib einen Namen oder ein kurzes Wort ein." };
  if (!ALLOWED.test(value)) {
    return { ok: false, value, message: "Erlaubt sind Buchstaben, Ä, Ö, Ü, ß sowie höchstens ein Leerzeichen oder Bindestrich." };
  }
  const count = lettersOnlyCount(value);
  if (count < 1 || count > 18) {
    return { ok: false, value, message: "Bitte verwende höchstens 18 Buchstaben." };
  }
  return { ok: true, value };
}

function setError(message = "") {
  error.textContent = message;
  error.hidden = !message;
  input.setAttribute("aria-invalid", message ? "true" : "false");
}

function clearExport() {
  exportBlob = null;
  downloadButton.disabled = true;
  if (exportUrl) URL.revokeObjectURL(exportUrl);
  exportUrl = "";
}

function clearCanvas() {
  const ctx = canvas.getContext("2d", { alpha: false });
  ctx.fillStyle = "#FFFFFF";
  ctx.fillRect(0, 0, WIDTH, HEIGHT);
  canvas.setAttribute("aria-label", "Noch keine Namensvorlage erstellt");
}

async function ensureFont(text) {
  if (!document.fonts || typeof document.fonts.load !== "function") {
    throw new Error("FONT_API_UNAVAILABLE");
  }
  await document.fonts.load(`800 240px ${FONT}`, text);
  if (!document.fonts.check(`800 240px ${FONT}`, text)) {
    throw new Error("FONT_NOT_AVAILABLE");
  }
}

function fitFontSize(ctx, text) {
  const maxWidth = WIDTH - SAFE * 2;
  const maxHeight = HEIGHT - SAFE * 2;
  let size = 1120;
  const minSize = 430;
  const strokeFor = (fontSize) => Math.max(18, Math.round(fontSize * 0.035));

  for (; size >= minSize; size -= 20) {
    ctx.font = `800 ${size}px ${FONT}`;
    const metrics = ctx.measureText(text);
    const left = metrics.actualBoundingBoxLeft || 0;
    const right = metrics.actualBoundingBoxRight || metrics.width;
    const ascent = metrics.actualBoundingBoxAscent || size * 0.8;
    const descent = metrics.actualBoundingBoxDescent || size * 0.2;
    const stroke = strokeFor(size);
    const width = left + right + stroke;
    const height = ascent + descent + stroke;
    if (width <= maxWidth && height <= maxHeight) return { size, stroke, metrics };
  }
  throw new Error("TEXT_DOES_NOT_FIT");
}

async function renderName(value) {
  clearExport();
  await ensureFont(value);

  const ctx = canvas.getContext("2d", { alpha: false, willReadFrequently: true });
  if (!ctx) throw new Error("CANVAS_UNAVAILABLE");

  ctx.fillStyle = "#FFFFFF";
  ctx.fillRect(0, 0, WIDTH, HEIGHT);
  ctx.textAlign = "center";
  ctx.textBaseline = "alphabetic";
  ctx.lineJoin = "round";
  ctx.lineCap = "round";

  const fit = fitFontSize(ctx, value);
  ctx.font = `800 ${fit.size}px ${FONT}`;
  const metrics = ctx.measureText(value);
  const ascent = metrics.actualBoundingBoxAscent || fit.size * 0.8;
  const descent = metrics.actualBoundingBoxDescent || fit.size * 0.2;
  const y = (HEIGHT - (ascent + descent)) / 2 + ascent;

  ctx.fillStyle = "#FFFFFF";
  ctx.strokeStyle = "#000000";
  ctx.lineWidth = fit.stroke;
  ctx.strokeText(value, WIDTH / 2, y);
  ctx.fillText(value, WIDTH / 2, y);

  const verify = ctx.measureText(value);
  const left = WIDTH / 2 - (verify.actualBoundingBoxLeft || verify.width / 2) - fit.stroke / 2;
  const right = WIDTH / 2 + (verify.actualBoundingBoxRight || verify.width / 2) + fit.stroke / 2;
  const top = y - (verify.actualBoundingBoxAscent || fit.size * 0.8) - fit.stroke / 2;
  const bottom = y + (verify.actualBoundingBoxDescent || fit.size * 0.2) + fit.stroke / 2;

  if (left < SAFE || top < SAFE || right > WIDTH - SAFE || bottom > HEIGHT - SAFE) {
    ctx.fillStyle = "#FFFFFF";
    ctx.fillRect(0, 0, WIDTH, HEIGHT);
    throw new Error("SAFE_MARGIN_FAILED");
  }

  renderedText = value;
  canvas.setAttribute("aria-label", `A4-Ausmalvorlage für ${value}`);
  printButton.disabled = false;
  status.textContent = "Vorschau ist bereit. Du kannst jetzt drucken oder eine geprüfte PNG-Datei erstellen.";

  try {
    exportBlob = await encodeRgbPng(canvas);
    downloadButton.disabled = false;
  } catch (err) {
    exportBlob = null;
    downloadButton.disabled = true;
    status.textContent = "Vorschau und Drucken sind bereit. PNG-Speichern ist auf diesem Gerät nicht verfügbar.";
    console.warn("Local PNG export unavailable", err);
  }
}

function u32(value) {
  return new Uint8Array([
    (value >>> 24) & 255,
    (value >>> 16) & 255,
    (value >>> 8) & 255,
    value & 255,
  ]);
}

const CRC_TABLE = (() => {
  const table = new Uint32Array(256);
  for (let n = 0; n < 256; n += 1) {
    let c = n;
    for (let k = 0; k < 8; k += 1) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
    table[n] = c >>> 0;
  }
  return table;
})();

function crc32(bytes) {
  let c = 0xFFFFFFFF;
  for (const byte of bytes) c = CRC_TABLE[(c ^ byte) & 0xFF] ^ (c >>> 8);
  return (c ^ 0xFFFFFFFF) >>> 0;
}

function concat(parts) {
  const length = parts.reduce((sum, part) => sum + part.length, 0);
  const out = new Uint8Array(length);
  let offset = 0;
  for (const part of parts) {
    out.set(part, offset);
    offset += part.length;
  }
  return out;
}

function chunk(type, data) {
  const typeBytes = new TextEncoder().encode(type);
  const body = concat([typeBytes, data]);
  return concat([u32(data.length), body, u32(crc32(body))]);
}

async function deflate(bytes) {
  if (typeof CompressionStream !== "function") throw new Error("COMPRESSION_STREAM_UNAVAILABLE");
  const stream = new Blob([bytes]).stream().pipeThrough(new CompressionStream("deflate"));
  return new Uint8Array(await new Response(stream).arrayBuffer());
}

async function encodeRgbPng(sourceCanvas) {
  const ctx = sourceCanvas.getContext("2d", { alpha: false, willReadFrequently: true });
  const image = ctx.getImageData(0, 0, WIDTH, HEIGHT);
  const rgba = image.data;
  const raw = new Uint8Array(HEIGHT * (1 + WIDTH * 3));

  let src = 0;
  let dst = 0;
  for (let y = 0; y < HEIGHT; y += 1) {
    raw[dst++] = 0;
    for (let x = 0; x < WIDTH; x += 1) {
      raw[dst++] = rgba[src++];
      raw[dst++] = rgba[src++];
      raw[dst++] = rgba[src++];
      src += 1;
    }
  }

  const compressed = await deflate(raw);
  const ihdr = concat([
    u32(WIDTH),
    u32(HEIGHT),
    new Uint8Array([8, 2, 0, 0, 0]),
  ]);
  const phys = concat([u32(PX_PER_METRE), u32(PX_PER_METRE), new Uint8Array([1])]);
  const signature = new Uint8Array([137, 80, 78, 71, 13, 10, 26, 10]);
  const bytes = concat([
    signature,
    chunk("IHDR", ihdr),
    chunk("pHYs", phys),
    chunk("IDAT", compressed),
    chunk("IEND", new Uint8Array()),
  ]);

  validatePngStructure(bytes);
  return new Blob([bytes], { type: "image/png" });
}

function validatePngStructure(bytes) {
  const signature = [137, 80, 78, 71, 13, 10, 26, 10];
  if (bytes.length < 64 || !signature.every((value, i) => bytes[i] === value)) throw new Error("PNG_SIGNATURE");

  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  let offset = 8;
  let ihdr = 0;
  let phys = 0;
  let idat = 0;
  let iend = 0;

  while (offset + 12 <= bytes.length) {
    const length = view.getUint32(offset);
    const typeStart = offset + 4;
    const dataStart = typeStart + 4;
    const dataEnd = dataStart + length;
    const crcAt = dataEnd;
    if (crcAt + 4 > bytes.length) throw new Error("PNG_BOUNDS");

    const type = String.fromCharCode(...bytes.slice(typeStart, typeStart + 4));
    const expected = view.getUint32(crcAt);
    const actual = crc32(bytes.slice(typeStart, dataEnd));
    if (expected !== actual) throw new Error("PNG_CRC");

    if (type === "IHDR") {
      ihdr += 1;
      if (length !== 13 || view.getUint32(dataStart) !== WIDTH || view.getUint32(dataStart + 4) !== HEIGHT) throw new Error("PNG_IHDR_SIZE");
      if (bytes[dataStart + 8] !== 8 || bytes[dataStart + 9] !== 2) throw new Error("PNG_NOT_RGB8");
    } else if (type === "pHYs") {
      phys += 1;
      if (length !== 9 || view.getUint32(dataStart) !== PX_PER_METRE || view.getUint32(dataStart + 4) !== PX_PER_METRE || bytes[dataStart + 8] !== 1) {
        throw new Error("PNG_PHYS");
      }
    } else if (type === "IDAT") {
      idat += 1;
    } else if (type === "IEND") {
      iend += 1;
      if (length !== 0) throw new Error("PNG_IEND");
      offset = crcAt + 4;
      break;
    }
    offset = crcAt + 4;
  }

  if (ihdr !== 1 || phys !== 1 || idat < 1 || iend !== 1 || offset !== bytes.length) throw new Error("PNG_STRUCTURE");
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  setError();
  status.textContent = "";
  const result = validateValue(input.value);
  input.value = result.value;
  if (!result.ok) {
    setError(result.message);
    printButton.disabled = true;
    clearExport();
    clearCanvas();
    input.focus();
    return;
  }

  try {
    status.textContent = "Vorlage wird erstellt …";
    await renderName(result.value);
  } catch (err) {
    console.warn("Local name rendering failed", err);
    renderedText = "";
    printButton.disabled = true;
    clearExport();
    clearCanvas();
    status.textContent = "";
    setError("Das Ausmalbild kann auf diesem Gerät gerade nicht erstellt werden. Bitte versuche es mit einem kürzeren Wort.");
  }
});

downloadButton.addEventListener("click", () => {
  if (!exportBlob || !renderedText) return;
  if (exportUrl) URL.revokeObjectURL(exportUrl);
  exportUrl = URL.createObjectURL(exportBlob);
  const anchor = document.createElement("a");
  anchor.href = exportUrl;
  anchor.download = "mein-name-a4.png";
  anchor.rel = "noopener";
  anchor.click();
  setTimeout(() => {
    if (exportUrl) URL.revokeObjectURL(exportUrl);
    exportUrl = "";
  }, 0);
});

printButton.addEventListener("click", () => {
  if (!renderedText) return;
  window.print();
});

clearButton.addEventListener("click", () => {
  input.value = "";
  renderedText = "";
  setError();
  status.textContent = "";
  printButton.disabled = true;
  clearExport();
  clearCanvas();
  input.focus();
});

if (menuButton && mobileNav) {
  menuButton.addEventListener("click", () => {
    const open = menuButton.getAttribute("aria-expanded") === "true";
    menuButton.setAttribute("aria-expanded", String(!open));
    mobileNav.hidden = open;
  });
}

window.addEventListener("beforeunload", () => {
  if (exportUrl) URL.revokeObjectURL(exportUrl);
});

clearCanvas();
