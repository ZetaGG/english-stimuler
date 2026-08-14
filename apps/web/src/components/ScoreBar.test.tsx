import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ScoreBar } from "./ScoreBar";

describe("ScoreBar", () => {
  it("renders the label and the display value", () => {
    render(<ScoreBar label="Fluency" value={7.5} max={9} display="7.5" />);
    expect(screen.getByText("Fluency")).toBeInTheDocument();
    expect(screen.getByText("7.5")).toBeInTheDocument();
  });

  it("computes the fill width relative to max", () => {
    render(<ScoreBar label="Pronunciation" value={50} />);
    const fill = screen.getByLabelText("Pronunciation").firstElementChild as HTMLElement;
    expect(fill.style.width).toBe("50%");
  });

  it("clamps the fill width to 100", () => {
    render(<ScoreBar label="Grammar" value={999} />);
    const fill = screen.getByLabelText("Grammar").firstElementChild as HTMLElement;
    expect(fill.style.width).toBe("100%");
  });
});
