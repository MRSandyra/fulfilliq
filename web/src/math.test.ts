import { describe, expect, it } from "vitest";
import { triage } from "./math";

describe("triage scenario", () => {
  it("uses the documented non-causal formula", () => {
    expect(triage(10, .5, .2, 8, 40)).toEqual({ avoided: 1, net: -40 });
  });
});
