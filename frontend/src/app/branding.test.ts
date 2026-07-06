import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

describe("branding assets", () => {
  it("includes WM favicon asset", () => {
    const faviconPath = resolve(process.cwd(), "public", "favicon.svg");
    expect(existsSync(faviconPath)).toBe(true);

    const iconText = readFileSync(faviconPath, "utf8");
    expect(iconText).toContain("<svg");
    expect(iconText).toContain('fill="#42D2AA"');
  });

  it("wires favicon link in index.html", () => {
    const indexPath = resolve(process.cwd(), "index.html");
    const indexText = readFileSync(indexPath, "utf8");

    expect(indexText).toContain('rel="icon"');
    expect(indexText).toContain('href="/favicon.svg"');
  });
});
