import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Dashboard } from "./Dashboard";
import { recordFixture, statsFixture, vocabularyFixture } from "../test/fixtures";

describe("Dashboard", () => {
  it("shows the loading state", () => {
    render(<Dashboard stats={null} recent={[]} vocabulary={[]} loading error={null} onStartPractice={() => {}} onViewEvaluation={() => {}} onRemoveWord={() => {}} />);
    expect(screen.getByText(/connecting to your coach/i)).toBeInTheDocument();
  });

  it("shows an error banner when the server is unreachable", () => {
    render(<Dashboard stats={null} recent={[]} vocabulary={[]} loading={false} error="fetch failed" onStartPractice={() => {}} onViewEvaluation={() => {}} onRemoveWord={() => {}} />);
    expect(screen.getByText(/fetch failed/i)).toBeInTheDocument();
  });

  it("renders the overall band and weekly averages", () => {
    render(<Dashboard stats={statsFixture} recent={[]} vocabulary={[]} loading={false} error={null} onStartPractice={() => {}} onViewEvaluation={() => {}} onRemoveWord={() => {}} />);
    expect(screen.getByText("overall band")).toBeInTheDocument();
    expect(screen.getAllByText("6.0").length).toBeGreaterThan(0);
    expect(screen.getByText("this week")).toBeInTheDocument();
  });

  it("starts practice from the hero CTA", () => {
    const onStartPractice = vi.fn();
    render(<Dashboard stats={statsFixture} recent={[]} vocabulary={[]} loading={false} error={null} onStartPractice={onStartPractice} onViewEvaluation={() => {}} onRemoveWord={() => {}} />);
    fireEvent.click(screen.getByRole("button", { name: /start practice/i }));
    expect(onStartPractice).toHaveBeenCalledTimes(1);
  });

  it("lists recent sessions and opens their detail", () => {
    const onViewEvaluation = vi.fn();
    render(<Dashboard stats={statsFixture} recent={[recordFixture]} vocabulary={[]} loading={false} error={null} onStartPractice={() => {}} onViewEvaluation={onViewEvaluation} onRemoveWord={() => {}} />);
    expect(screen.getByText(/favorite place to relax/i)).toBeInTheDocument();
    fireEvent.click(screen.getByText(/favorite place to relax/i));
    expect(onViewEvaluation).toHaveBeenCalledWith("abc123");
  });

  it("removes a word from the dictionary", () => {
    const onRemoveWord = vi.fn();
    render(<Dashboard stats={statsFixture} recent={[]} vocabulary={vocabularyFixture} loading={false} error={null} onStartPractice={() => {}} onViewEvaluation={() => {}} onRemoveWord={onRemoveWord} />);
    fireEvent.click(screen.getByRole("button", { name: /remove beach/i }));
    expect(onRemoveWord).toHaveBeenCalledWith("beach");
  });
});
