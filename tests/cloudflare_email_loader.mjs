const EMAIL_STUB = [
  "export class EmailMessage {",
  "  constructor(from, to, raw) {",
  "    this.from = from;",
  "    this.to = to;",
  "    this.raw = raw;",
  "  }",
  "}",
].join("\n");

export async function resolve(specifier, context, nextResolve) {
  if (specifier === "cloudflare:email") {
    return {
      url: "data:text/javascript," + encodeURIComponent(EMAIL_STUB),
      shortCircuit: true,
    };
  }
  return nextResolve(specifier, context);
}
