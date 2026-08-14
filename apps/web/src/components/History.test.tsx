import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { History } from "./History";
import { recordFixture } from "../test/fixtures";

describe("History", () => {
  it("lists sessions and opens the detail view", () => {
    render(<History items={[recordFixture]} total={1} loading={false} error={null} onDelete={vi.fn()} onBack={() => {}} />);

    expect(screen.getByText("History (1)")).toBeInTheDocument();
    fireEvent.click(screen.getByText(/favorite place to relax/i));
    expect(screen.getByText(/you said/i)).toBeInTheDocument();
    expect(screen.getByText(/my favorite place is the beach/i)).toBeInTheDocument();
  });

  it("deletes a session from the detail view", async () => {
    const onDelete = vi.fn().mockResolvedValue(undefined);
    render(<History items={[recordFixture]} total={1} loading={false} error={null} onDelete={onDelete} onBack={() => {}} />);

    fireEvent.click(screen.getByText(/favorite place to relax/i));
    fireEvent.click(screen.getByRole("button", { name: /delete session/i }));
    await waitFor(() => expect(onDelete).toHaveBeenCalledWith("abc123"));
  });

  it("shows an empty state", () => {
    render(<History items={[]} total={0} loading={false} error={null} onDelete={vi.fn()} onBack={() => {}} />);
    expect(screen.getByText(/no sessions recorded yet/i)).toBeInTheDocument();
  });

  it("shows the loading state", () => {
    render(<History items={[]} total={0} loading error={null} onDelete={vi.fn()} onBack={() => {}} />);
    expect(screen.getByText(/loading your history/i)).toBeInTheDocument();
  });
});
