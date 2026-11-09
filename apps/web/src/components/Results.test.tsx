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

  it("shows the prompt and transcript right after the attempt", () => {
    render(<Results result={resultFixture} onReset={() => {}} onHome={() => {}} />);

    expect(screen.getByText(/describe your favorite place to relax\./i)).toBeInTheDocument();
    expect(screen.getByText(/my favorite place is the beach/i)).toBeInTheDocument();
  });

  it("lists pronunciation and grammar issues", () => {
    render(<Results result={resultFixture} onReset={() => {}} onHome={() => {}} />);

    expect(screen.getByText("beach")).toBeInTheDocument();
    expect(screen.getByText(/possible missing article/i)).toBeInTheDocument();
    expect(screen.getByText("→ a")).toBeInTheDocument();
  });

  it("shows the pronunciation summary and the target sounds per word", () => {
    render(<Results result={resultFixture} onReset={() => {}} onHome={() => {}} />);

    expect(screen.getByText("You pronounced 1 of 2 words correctly.")).toBeInTheDocument();
    expect(screen.getByText("2 sounds off")).toBeInTheDocument();
    expect(screen.getByText("said a different sound · missed a sound")).toBeInTheDocument();
    expect(screen.getByText(/say it as:/i)).toBeInTheDocument();
    expect(screen.getByText('b (as in "be")')).toBeInTheDocument();
    expect(screen.getByText('ee (as in "see")')).toBeInTheDocument();
    expect(
      screen.getByText(
        'say ee (as in "see") instead of i (as in "sit") · add the missing sound ch (as in "cheese")',
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText(/\/IY\//)).not.toBeInTheDocument();
  });

  it("shows an empty state when there are no issues", () => {
    render(
      <Results
        result={{
          ...resultFixture,
          pronunciation: { overall_score: 92, words: [], issues: [] },
          grammar_issues: [],
        }}
        onReset={() => {}}
        onHome={() => {}}
      />,
    );

    expect(screen.getByRole("heading", { name: "Pronunciation" })).toBeInTheDocument();
    expect(screen.getByText(/pronunciation was clear/i)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Grammar" })).toBeInTheDocument();
    expect(screen.getByText(/no grammar issues detected/i)).toBeInTheDocument();
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
