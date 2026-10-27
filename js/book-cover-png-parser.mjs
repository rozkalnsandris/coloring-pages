// #199 independent PNG chunk parser for future personalized cover export.
// This module validates PNG byte framing, critical chunk order and CRCs, and
// extracts IHDR/pHYs metadata for book-cover-a4-contract.mjs. It deliberately
// does NOT decompress IDAT data, inspect pixels, verify the 177 px white frame,
// validate font/glyph layout, encode/download a PNG, or prove print quality.

const PNG_SIGNATURE = Object.freeze([137, 80, 78, 71, 13, 10, 26, 10]);
const KNOWN_CRITICAL = new Set(["IHDR", "PLTE", "IDAT", "IEND"]);
const VALID_BIT_DEPTHS = Object.freeze({
  0: Object.freeze([1, 2, 4, 8, 16]),
  2: Object.freeze([8, 16]),
  3: Object.freeze([1, 2, 4, 8]),
  4: Object.freeze([8, 16]),
  6: Object.freeze([8, 16]),
});

function asBytes(value) {
  if (value instanceof Uint8Array) return value;
  if (value instanceof ArrayBuffer) return new Uint8Array(value);
  if (ArrayBuffer.isView(value)) {
    return new Uint8Array(value.buffer, value.byteOffset, value.byteLength);
  }
  throw new TypeError("PNG bytes must be an ArrayBuffer or typed-array view");
}

function readU32(bytes, offset) {
  return (
    (bytes[offset] * 0x1000000) +
    (bytes[offset + 1] << 16) +
    (bytes[offset + 2] << 8) +
    bytes[offset + 3]
  ) >>> 0;
}

function chunkType(bytes, offset) {
  const chars = [];
  for (let index = 0; index < 4; index++) {
    const code = bytes[offset + index];
    const isLetter = (code >= 65 && code <= 90) || (code >= 97 && code <= 122);
    if (!isLetter) throw new Error("PNG chunk type must contain ASCII letters");
    chars.push(String.fromCharCode(code));
  }
  return chars.join("");
}

function crc32(bytes, start, end) {
  let crc = 0xffffffff;
  for (let index = start; index < end; index++) {
    crc ^= bytes[index];
    for (let bit = 0; bit < 8; bit++) {
      crc = (crc >>> 1) ^ (0xedb88320 & -(crc & 1));
    }
  }
  return (crc ^ 0xffffffff) >>> 0;
}

function validateIhdr(fields) {
  if (fields.width < 1 || fields.height < 1) {
    throw new Error("PNG dimensions must be positive");
  }
  const validDepths = VALID_BIT_DEPTHS[fields.colorType];
  if (!validDepths || !validDepths.includes(fields.bitDepth)) {
    throw new Error("PNG IHDR bit depth/color type combination is invalid");
  }
  if (fields.compressionMethod !== 0 || fields.filterMethod !== 0) {
    throw new Error("PNG IHDR compression/filter method is invalid");
  }
  if (fields.interlaceMethod !== 0 && fields.interlaceMethod !== 1) {
    throw new Error("PNG IHDR interlace method is invalid");
  }
}

export function parseBookCoverPngStructure(input) {
  const bytes = asBytes(input);
  if (bytes.length < PNG_SIGNATURE.length + 12 + 13 + 12) {
    throw new Error("PNG is too short");
  }
  for (let index = 0; index < PNG_SIGNATURE.length; index++) {
    if (bytes[index] !== PNG_SIGNATURE[index]) {
      throw new Error("Invalid PNG signature");
    }
  }

  let offset = PNG_SIGNATURE.length;
  let chunkIndex = 0;
  let ihdr = null;
  let phys = null;
  let seenPlte = false;
  let seenIdat = false;
  let idatEnded = false;
  let idatChunkCount = 0;
  let seenIend = false;

  while (offset < bytes.length) {
    if (seenIend) throw new Error("Trailing bytes after IEND");
    if (bytes.length - offset < 12) throw new Error("Truncated PNG chunk");

    const length = readU32(bytes, offset);
    if (length > 0x7fffffff) throw new Error("PNG chunk length exceeds specification");
    if (length > bytes.length - offset - 12) throw new Error("Truncated PNG chunk data");

    const typeOffset = offset + 4;
    const dataOffset = offset + 8;
    const crcOffset = dataOffset + length;
    const type = chunkType(bytes, typeOffset);
    const storedCrc = readU32(bytes, crcOffset);
    const computedCrc = crc32(bytes, typeOffset, crcOffset);
    if (storedCrc !== computedCrc) throw new Error(`PNG CRC mismatch in ${type}`);

    const critical = bytes[typeOffset] >= 65 && bytes[typeOffset] <= 90;
    if (critical && !KNOWN_CRITICAL.has(type)) {
      throw new Error(`Unsupported critical PNG chunk ${type}`);
    }

    if (chunkIndex === 0 && type !== "IHDR") {
      throw new Error("IHDR must be the first PNG chunk");
    }

    if (type === "IHDR") {
      if (ihdr || chunkIndex !== 0 || length !== 13) {
        throw new Error("PNG must contain exactly one 13-byte IHDR first");
      }
      ihdr = {
        width: readU32(bytes, dataOffset),
        height: readU32(bytes, dataOffset + 4),
        bitDepth: bytes[dataOffset + 8],
        colorType: bytes[dataOffset + 9],
        compressionMethod: bytes[dataOffset + 10],
        filterMethod: bytes[dataOffset + 11],
        interlaceMethod: bytes[dataOffset + 12],
      };
      validateIhdr(ihdr);
    } else {
      if (!ihdr) throw new Error("PNG chunk encountered before IHDR");

      if (type === "PLTE") {
        if (seenPlte || seenIdat) throw new Error("PLTE must appear at most once before IDAT");
        if (ihdr.colorType === 0 || ihdr.colorType === 4) {
          throw new Error("PLTE is forbidden for this PNG color type");
        }
        if (length === 0 || length % 3 !== 0 || length > 768) {
          throw new Error("PLTE length is invalid");
        }
        seenPlte = true;
      }

      if (type === "pHYs") {
        if (seenIdat) throw new Error("pHYs must appear before IDAT");
        if (phys) throw new Error("pHYs must not appear more than once");
        if (length !== 9) throw new Error("pHYs must be exactly 9 bytes");
        phys = {
          x: readU32(bytes, dataOffset),
          y: readU32(bytes, dataOffset + 4),
          unit: bytes[dataOffset + 8],
        };
      }

      if (type === "IDAT") {
        if (idatEnded) throw new Error("IDAT chunks must be consecutive");
        seenIdat = true;
        idatChunkCount++;
      } else if (seenIdat && type !== "IEND") {
        idatEnded = true;
      }

      if (type === "IEND") {
        if (length !== 0) throw new Error("IEND must have zero length");
        if (!seenIdat) throw new Error("PNG must contain IDAT before IEND");
        if (ihdr.colorType === 3 && !seenPlte) {
          throw new Error("Indexed-color PNG requires PLTE");
        }
        seenIend = true;
      }
    }

    offset = crcOffset + 4;
    chunkIndex++;
  }

  if (!seenIend) throw new Error("PNG is missing IEND");
  if (offset !== bytes.length) throw new Error("PNG chunk parsing did not consume all bytes");

  return Object.freeze({
    width: ihdr.width,
    height: ihdr.height,
    bitDepth: ihdr.bitDepth,
    colorType: ihdr.colorType,
    compressionMethod: ihdr.compressionMethod,
    filterMethod: ihdr.filterMethod,
    interlaceMethod: ihdr.interlaceMethod,
    physX: phys?.x ?? null,
    physY: phys?.y ?? null,
    physUnit: phys?.unit ?? null,
    physChunkCount: phys ? 1 : 0,
    idatChunkCount,
    chunkCount: chunkIndex,
    hasPlte: seenPlte,
  });
}
