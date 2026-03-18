/**
 * Manual (no-library) Code 39 renderer using Canvas2D.
 *
 * Returns a `data:image/png;base64,...` string that can be used directly in an <img>.
 */

/**
 * Code 39 is a barcode symbology that encodes 43 different characters, including digits, uppercase letters, and special characters.
 * It is a self-checking code, meaning that the barcode can be scanned and verified without the need for a checksum.
 * It is a linear barcode and is often used in industrial applications.
 * It is a 1D barcode and is often used in industrial applications.
 * 0-9, A-Z, -, ., $, /, +, %, * are the supported characters.
 * * is the start/stop character and must not be part of the input.
 * The barcode is encoded as a sequence of bars and spaces.
 * The bars are encoded as "w" for wide and "n" for narrow.
 * The spaces are encoded as "n" for narrow and "w" for wide.
 * The barcode is encoded as a sequence of bars and spaces.
 * The bars are encoded as "w" for wide and "n" for narrow.
 * The spaces are encoded as "n" for narrow and "w" for wide.
 * The barcode is encoded as a sequence of bars and spaces.
 */

export const CODE39_PATTERNS: Record<string, string> = {
  "0": "nnnwwnwnn",
  "1": "wnnwnnnnw",
  "2": "nnwwnnnnw",
  "3": "wnwwnnnnn",
  "4": "nnnwwnnnw",
  "5": "wnnwwnnnn",
  "6": "nnwwwnnnn",
  "7": "nnnwnnwnw",
  "8": "wnnwnnwnn",
  "9": "nnwwnnwnn",

  A: "wnnnnwnnw",
  B: "nnwnnwnnw",
  C: "wnwnnwnnn",
  D: "nnnnwwnnw",
  E: "wnnnwwnnn",
  F: "nnwnwwnnn",
  G: "nnnnnwwnw",
  H: "wnnnnwwnn",
  I: "nnwnnwwnn",
  J: "nnnnwwwnn",

  K: "wnnnnnnww",
  L: "nnwnnnnww",
  M: "wnwnnnnwn",
  N: "nnnnwnnww",
  O: "wnnnwnnwn",
  P: "nnwnwnnwn",
  Q: "nnnnnnwww",
  R: "wnnnnnwwn",
  S: "nnwnnnwwn",
  T: "nnnnwnwwn",

  U: "wwnnnnnnw",
  V: "nwwnnnnnw",
  W: "wwwnnnnnn",
  X: "nwnnwnnnw",
  Y: "wwnnwnnnn",
  Z: "nwwnwnnnn",

  "-": "nwnnnnwnw",
  ".": "wwnnnnwnn",
  " ": "nwwnnnwnn",
  "$": "nwnwnwnnn",
  "/": "nwnwnnnwn",
  "+": "nwnnnwnwn",
  "%": "nnnwnwnwn",
  "*": "nwnnwnwnn", // start/stop (should not be present in input)
};

export type Code39RenderOptions = {
  width: number;
  wideToNarrowRatio?: number;
  barHeightRatio?: number;
  barHeightMin?: number;
  textHeight?: number;
  fontSize?: number;
  paddingX?: number;
  paddingTop?: number;
  paddingBottom?: number;
  interCharGapNarrowUnits?: number;
  backgroundColor?: string;
  barColor?: string;
  textColor?: string;
};

const DEFAULT_OPTIONS: Required<Code39RenderOptions> = {
  width: 320,
  wideToNarrowRatio: 2.5,
  barHeightRatio: 0.32,
  barHeightMin: 80,
  textHeight: 28,
  fontSize: 18,
  paddingX: 16,
  paddingTop: 12,
  paddingBottom: 12,
  interCharGapNarrowUnits: 1,
  backgroundColor: "#ffffff",
  barColor: "#000000",
  textColor: "#000000",
};

type BarcodeElement = {
  isBar: boolean;
  units: number;
};

// Code 39 can be use to encode any string, but it is most commonly used to encode numbers and uppercase letters.
function normalizeCode39Token(token: string): string {
  const normalized = token.trim().toUpperCase();

  if (!normalized) {
    throw new Error("Code 39 token is empty.");
  }

  for (const ch of normalized) {
    // `*` is reserved for start/stop and must not be part of the input.
    if (ch === "*") throw new Error('Code 39 input must not contain "*"');
    if (!(ch in CODE39_PATTERNS)) {
      throw new Error(`Unsupported Code 39 character: "${ch}"`);
    }
  }

  return normalized;
}

// Builds the barcode sequence from the normalized token.
// For text returns sequence of bars and spaces. Every element has width in "narrow units".
//
// Code 39: Every character has 9 elements (bar/space/bar/space/bar/space/bar/space/bar).
// Between characters there is a 1-unit narrow space gap.

function buildCode39Sequence(
  normalizedToken: string,
  wideToNarrowRatio: number,
  interCharGapNarrowUnits: number,
): BarcodeElement[] {
  const fullText = `*${normalizedToken}*`;
  const sequence: BarcodeElement[] = [];

  for (let charIndex = 0; charIndex < fullText.length; charIndex += 1) {
    const ch = fullText[charIndex];
    const pattern = CODE39_PATTERNS[ch];
    if (!pattern) throw new Error(`Missing Code 39 pattern for "${ch}"`);

    for (let i = 0; i < pattern.length; i += 1) {
      const isBar = i % 2 === 0;
      const isWide = pattern[i] === "w";

      sequence.push({
        isBar,
        units: isWide ? wideToNarrowRatio : 1,
      });
    }

    // Narrow space gap between characters (not after last char).
     // međukarakterni gap, osim posle poslednjeg karaktera
    if (charIndex < fullText.length - 1) {
      sequence.push({
        isBar: false,
        units: interCharGapNarrowUnits,
      });
    }
  }

  return sequence;
}

/**
 * Generates Code 39 barcode PNG as a data URL.
 * Draws bars + the token text below the barcode.
 */
export function generateCode39BarcodeImage(
  token: string,
  width: number,
  options?: Omit<Code39RenderOptions, "width">,
): string {
  // Prevent SSR rendering attempts.
  if (typeof document === "undefined") return "";

  const opts: Required<Code39RenderOptions> = {
    ...DEFAULT_OPTIONS,
    ...options,
    width,
  };

  const normalizedToken = normalizeCode39Token(token);

  const barHeight = Math.max(
    opts.barHeightMin,
    Math.floor(opts.width * opts.barHeightRatio),
  );

  const imageHeight =
    opts.paddingTop + barHeight + opts.textHeight + opts.paddingBottom;

  const canvas = document.createElement("canvas");
  canvas.width = Math.max(1, Math.round(opts.width));
  canvas.height = Math.max(1, Math.round(imageHeight));

  const ctx = canvas.getContext("2d");
  if (!ctx) return "";

  ctx.imageSmoothingEnabled = false;

  // Background color
  ctx.fillStyle = opts.backgroundColor;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  const sequence = buildCode39Sequence(
    normalizedToken,
    opts.wideToNarrowRatio,
    opts.interCharGapNarrowUnits,
  );

  const totalUnits = sequence.reduce((sum, item) => sum + item.units, 0);
  const drawableWidth = canvas.width - opts.paddingX * 2;

  if (drawableWidth <= 0 || totalUnits <= 0) return "";

  const unitWidth = drawableWidth / totalUnits;
  const barTop = opts.paddingTop;
  const barBottom = opts.paddingTop + barHeight;

  let currentX = opts.paddingX;

  // Bars/spaces
  for (const item of sequence) {
    const rawWidth = item.units * unitWidth;
    const nextX = currentX + rawWidth;

    // Round only for drawing to keep the overall scale consistent.
    const drawX = Math.round(currentX);
    const drawNextX = Math.round(nextX);
    const drawWidth = Math.max(1, drawNextX - drawX);

    if (item.isBar) {
      ctx.fillStyle = opts.barColor;
      ctx.fillRect(drawX, barTop, drawWidth, barBottom - barTop);
    }

    currentX = nextX;
  }

  // Human-readable text under bars
  ctx.fillStyle = opts.textColor;
  ctx.font = `${opts.fontSize}px monospace`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";

  const textY = opts.paddingTop + barHeight + opts.textHeight / 2;
  ctx.fillText(normalizedToken, canvas.width / 2, textY);

  return canvas.toDataURL("image/png");
}

