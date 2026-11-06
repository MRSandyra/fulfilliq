import { describe, expect, it } from "vitest";
import { pageFromHash } from "./routes";

describe("dashboard hash routes", () => {
  it("opens a known page from the URL hash", () => {
    expect(pageFromHash("#quality")).toBe("quality");
  });

  it("falls back to overview for an absent or unknown hash", () => {
    expect(pageFromHash("")).toBe("overview");
    expect(pageFromHash("#unknown")).toBe("overview");
  });
});
