import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { BandBadge, bandColor, bandTone } from "./BandBadge";

describe("bandTone", () => {
  it("returns good for 7+", () => expect(bandTone(8)).toBe("good"));
  it("returns fair for 5-6.5", () => expect(bandTone(5.5)).toBe("fair"));
  it("returns bad below 5", () => expect(bandTone(4.5)).toBe("bad"));
});

describe("bandColor", () => {
  it("returns green, gold or red tones", () => {
    expect(bandColor(8)).toBe("var(--green)");
    expect(bandColor(6)).toBe("var(--gold-bright)");
    expect(bandColor(3)).toBe("var(--red)");
  });
});

describe("BandBadge", () => {
  it("shows the band value", () => {
    render(<BandBadge value={7.5} />);
    expect(screen.getByText("Band 7.5")).toBeInTheDocument();
  });
});
