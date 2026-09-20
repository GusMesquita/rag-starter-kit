import { describe, expect, it } from "vitest";
import { formatSourcesLabel } from "./formatSources";

describe("formatSourcesLabel", () => {
  it("pluralizes correctly at each boundary", () => {
    expect(formatSourcesLabel(0)).toBe("sem fontes no contexto");
    expect(formatSourcesLabel(1)).toBe("1 fonte usada");
    expect(formatSourcesLabel(3)).toBe("3 fontes usadas");
  });
});
