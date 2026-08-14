import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import { recordFixture, statsFixture, vocabularyFixture } from "./test/fixtures";

vi.mock("./api/client", () => ({
  api: {
    stats: vi.fn(),
    listEvaluations: vi.fn(),
    listVocabulary: vi.fn(),
    deleteEvaluation: vi.fn(),
    removeVocabulary: vi.fn(),
    evaluate: vi.fn(),
    getEvaluation: vi.fn(),
    health: vi.fn(),
  },
}));

import { api } from "./api/client";

const mockApi = api as unknown as {
  stats: ReturnType<typeof vi.fn>;
  listEvaluations: ReturnType<typeof vi.fn>;
  listVocabulary: ReturnType<typeof vi.fn>;
  removeVocabulary: ReturnType<typeof vi.fn>;
  deleteEvaluation: ReturnType<typeof vi.fn>;
};

describe("App", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApi.stats.mockResolvedValue(statsFixture);
    mockApi.listEvaluations.mockResolvedValue({ items: [recordFixture], total: 1 });
    mockApi.listVocabulary.mockResolvedValue({ items: vocabularyFixture });
    mockApi.removeVocabulary.mockResolvedValue(undefined);
    mockApi.deleteEvaluation.mockResolvedValue(undefined);
  });

  it("shows the brand and loads the dashboard", async () => {
    render(<App />);
    expect(screen.getByText("Stimuler")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("overall band")).toBeInTheDocument());
    expect(screen.getByText("beach")).toBeInTheDocument();
  });

  it("navigates to practice and back", async () => {
    render(<App />);
    await waitFor(() => expect(screen.getByText("overall band")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: "Practice" }));
    expect(screen.getByText(/impromptu speaking/i)).toBeInTheDocument();
  });

  it("navigates to history and lists sessions", async () => {
    render(<App />);
    await waitFor(() => expect(screen.getByText("overall band")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: "History" }));
    await waitFor(() => expect(screen.getByText("History (1)")).toBeInTheDocument());
  });

  it("removes a vocabulary word from the dashboard", async () => {
    render(<App />);
    await waitFor(() => expect(screen.getByText("beach")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: /remove beach/i }));
    await waitFor(() => expect(mockApi.removeVocabulary).toHaveBeenCalledWith("beach"));
  });
});
