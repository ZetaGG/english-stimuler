import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Results } from "./Results";
import { resultFixture } from "../test/fixtures";

describe("Results", () => {
  it("shows the overall band, scores and fluency details", () => {
    render(<Results result={resultFixture} onReset={() => {}} onHome={() => {}} />);

    expect(screen.getByText("overall band")).toBeInTheDocument();
    expect(screen.getByText(/session complete/i)).toBeInTheDocument();
    expect(screen.getByText("wpm")).toBeInTheDocument();
    expect(screen.getByText("107")).toBeInTheDocument();
    expect(screen.getByText("fillers")).toBeInTheDocument();
    expect(screen.getByText('"um" ×2')).toBeInTheDocument();
  });

  it("lists pronunciation and grammar issues", () => {
    render(<Results result={resultFixture} onReset={() => {}} onHome={() => {}} />);

    expect(screen.getByText("beach")).toBeInTheDocument();
    expect(screen.getByText(/possible missing article/i)).toBeInTheDocument();
    expect(screen.getByText("→ a")).toBeInTheDocument();
  });

  it("renders the coach feedback report", () => {
    render(<Results result={resultFixture} onReset={() => {}} onHome={() => {}} />);

    expect(screen.getByText("Good fluency overall.")).toBeInTheDocument();
    expect(screen.getByText("Strengths")).toBeInTheDocument();
    expect(screen.getByText("Clear structure")).toBeInTheDocument();
    expect(screen.getByText("Reduce filler words")).toBeInTheDocument();
  });

  it("reacts to reset and home actions", () => {
    const onReset = vi.fn();
    const onHome = vi.fn();
    render(<Results result={resultFixture} onReset={onReset} onHome={onHome} />);

    fireEvent.click(screen.getByRole("button", { name: /practice again/i }));
    fireEvent.click(screen.getByRole("button", { name: /back to home/i }));
    expect(onReset).toHaveBeenCalledTimes(1);
    expect(onHome).toHaveBeenCalledTimes(1);
  });
});
