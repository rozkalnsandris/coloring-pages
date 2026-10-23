import test from "node:test";
import assert from "node:assert/strict";
import { deflateSync } from "node:zlib";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { buildPrintPngZip, MAX_ZIP_INPUT_BYTES } from "../js/print-zip-store.mjs";

// Construct valid synthetic A4 RGB PNGs in memory; never commit test image binaries.
function crc32(bytes) {
  let crc = -1;
  for (const byte of bytes) {
    crc ^= byte;
    for (let i = 0; i < 8; i++) crc = (crc >>> 1) ^ ((crc & 1) ? 0xedb88320 : 0);
  }
  return (crc ^ -1) >>> 0;
}
function chunk(type, data) {
  const result = Buffer.alloc(12 + data.length);
  result.writeUInt32BE(data.length, 0);
  Buffer.from(type, "ascii").copy(result, 4);
  Buffer.from(data).copy(result, 8);
  result.writeUInt32BE(crc32(result.subarray(4, 8 + data.length)), 8 + data.length);
  return result;
}
function png(width = 2480, height = 3508) {
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0);
  ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8; ihdr[9] = 2;
  const stride = width * 3 + 1;
  const raw = Buffer.alloc(stride * height, 255);
  for (let row = 0; row < height; row++) raw[row * stride] = 0;
  return Buffer.concat([
    Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]),
    chunk("IHDR", ihdr),
    chunk("IDAT", deflateSync(raw, { level: 1 })),
    chunk("IEND", Buffer.alloc(0)),
  ]);
}
const page = (id, index = 1, count = 1) => ({
  activityId: id, pageIndex: index, pageCount: count,
  printUrl: "/media/" + id + "/" + (count === 1 ? "print" : "print-" + index) + ".png",
});
const download = (p, data) => ({ url: p.printUrl, bytes: data });
const little = (bytes, offset) => new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength).getUint32(offset, true);
const short = (bytes, offset) => new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength).getUint16(offset, true);

function extractedLocalEntries(archive) {
  const files = [];
  let pos = 0;
  while (little(archive, pos) === 0x04034b50) {
    assert.equal(short(archive, pos + 8), 0, "ZIP STORE, no compression");
    const crc = little(archive, pos + 14);
    const size = little(archive, pos + 18);
    assert.equal(size, little(archive, pos + 22));
    const nameLength = short(archive, pos + 26);
    const name = Buffer.from(archive.subarray(pos + 30, pos + 30 + nameLength)).toString("ascii");
    const start = pos + 30 + nameLength;
    const data = archive.subarray(start, start + size);
    assert.equal(crc32(data), crc);
    files.push({ name, content: data });
    pos = start + size;
  }
  assert.equal(little(archive, pos), 0x02014b50, "central directory follows local entries");
  return files;
}

test("portrait and landscape multi-page sheets remain exact bytes and ordered in STORE ZIP", () => {
  const pages = [page("cut-1", 1, 2), page("cut-1", 2, 2), page("0000003")];
  const images = [png(), png(3508, 2480), png()];
  const result = buildPrintPngZip(pages, pages.map((p, i) => download(p, images[i])));
  assert.deepEqual(result.filenames, ["01-cut-1.png", "02-cut-1.png", "03-0000003.png"]);
  const files = extractedLocalEntries(result.bytes);
  assert.deepEqual(files.map(f => f.name), result.filenames);
  files.forEach((f, i) => assert.deepEqual(Buffer.from(f.content), images[i]));
  assert.equal(little(result.bytes, result.bytes.length - 22), 0x06054b50);
  assert.equal(short(result.bytes, result.bytes.length - 12), 3);
  const repeated = buildPrintPngZip(pages, pages.map((p, i) => download(p, images[i])));
  assert.deepEqual(result.bytes, repeated.bytes, "deterministic output");
});

test("accepts typed-array views with offsets without modifying any input", () => {
  const sheet = png();
  const padded = Buffer.concat([Buffer.alloc(5), sheet, Buffer.alloc(7)]);
  const view = padded.subarray(5, 5 + sheet.length);
  const input = Buffer.from(view);
  const p = page("001");
  const out = buildPrintPngZip([p], [download(p, view)]);
  assert.deepEqual(Buffer.from(extractedLocalEntries(out.bytes)[0].content), input);
  assert.deepEqual(view, input);
});

test("missing, empty, misaligned and over-five selections reject before building ZIP", () => {
  const p = page("1"), valid = png();
  const invalid = [
    [[], []], [[p], []], [[p], [null]],
    [[p], [{ url: "/media/2/print.png", bytes: valid }]],
    [[p], [{ url: p.printUrl, bytes: new Uint8Array() }]],
    [Array(6).fill(p), Array(6).fill(download(p, valid))],
  ];
  for (const [pages, fetched] of invalid) assert.throws(() => buildPrintPngZip(pages, fetched));
});

test("rejects duplicate, unsafe, mismatched and noncanonical page metadata", () => {
  const good = png(), p = page("1");
  const wrong = [
    { ...p, activityId: "../1" },
    { ...p, pageIndex: 0 },
    { ...p, pageCount: 0 },
    { ...p, printUrl: "//external/media/1/print.png" },
    { ...p, printUrl: "/media/1/preview.webp" },
    { ...p, printUrl: "/media/2/print.png" },
    { ...p, printUrl: "/media/1/print.png?cache=1" },
    { ...p, printUrl: "/media/1/../2/print.png" },
  ];
  for (const value of wrong) assert.throws(() => buildPrintPngZip([value], [download(value, good)]));
  assert.throws(() => buildPrintPngZip([p, p], [download(p, good), download(p, good)]));
});

test("rejects truncated, non-A4, non-RGB, tampered or mislabeled PNG data", () => {
  const p = page("1"), good = png();
  const tampered = Buffer.from(good); tampered[21] ^= 1;
  const badIend = good.subarray(0, good.length - 12);
  const truncated = good.subarray(0, good.length - 2);
  const trailing = Buffer.concat([good, Buffer.from("junk")]);
  const rgba = Buffer.from(good); rgba[25] = 6;
  for (const item of [Buffer.from("error"), png(200, 300), tampered, badIend, truncated, trailing, rgba]) {
    assert.throws(() => buildPrintPngZip([p], [download(p, item)]));
  }
});

test("bounded memory budget rejects excessive bytes before PNG parsing", () => {
  assert.equal(MAX_ZIP_INPUT_BYTES, 64 * 1024 * 1024);
  const p = page("1");
  const tooLarge = new Uint8Array(MAX_ZIP_INPUT_BYTES + 1);
  assert.throws(() => buildPrintPngZip([p], [download(p, tooLarge)]), /memory guard/);
});

test("standard Python zipfile extracts identical ordered PNG SHA-256 without recompression", () => {
  const pages = [page("42"), page("cut-2", 1, 2), page("cut-2", 2, 2)];
  const images = [png(), png(3508, 2480), png()];
  const { bytes, filenames } = buildPrintPngZip(pages, pages.map((p, i) => download(p, images[i])));
  const hashes = images.map(p => createHash("sha256").update(p).digest("hex"));
  const script = [
    "import hashlib, io, json, sys, zipfile",
    "names = json.loads(sys.argv[1])",
    "hashes = json.loads(sys.argv[2])",
    "with zipfile.ZipFile(io.BytesIO(sys.stdin.buffer.read())) as z:",
    "    assert z.namelist() == names",
    "    assert all(f.compress_type == zipfile.ZIP_STORED for f in z.infolist())",
    "    assert [hashlib.sha256(z.read(name)).hexdigest() for name in names] == hashes",
  ].join("\n");
  const result = spawnSync("python3", ["-c", script, JSON.stringify(filenames), JSON.stringify(hashes)], {
    input: Buffer.from(bytes), encoding: "utf8", maxBuffer: 1024 * 1024,
  });
  assert.equal(result.status, 0, result.stderr || result.error?.message);
});
