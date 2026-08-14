import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { Practice } from "./Practice";
import { resultFixture } from "../test/fixtures";

vi.mock("../api/client", () => ({
  api: { evaluate: vi.fn() },
}));

import { api } from "../api/client";

class FakeMediaRecorder {
  static isTypeSupported = () => true;
  mimeType = "audio/webm";
  ondataavailable: ((event: { data: Blob }) => void) | null = null;
  onstop: (() => void) | null = null;
  start() {}
  stop() {
    this.onstop?.();
  }
}

function stubMedia() {
  const stream = { getTracks: () => [{ stop: vi.fn() }] };
  vi.stubGlobal("MediaRecorder", FakeMediaRecorder);
  Object.defineProperty(navigator, "mediaDevices", {
    configurable: true,
    value: { getUserMedia: vi.fn().mockResolvedValue(stream) },
  });
}

describe("Practice", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    stubMedia();
  });

  it("records, stops and submits the evaluation", async () => {
    const onSubmit = vi.fn();
    (api.evaluate as ReturnType<typeof vi.fn>).mockResolvedValue(resultFixture);
    const prompts = ["Describe your favorite place."];
    render(<Practice onSubmit={onSubmit} prompts={prompts} />);

    expect(screen.getByText("Describe your favorite place.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Record" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Stop" })).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: "Stop" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Evaluate speech" })).toBeEnabled());

    fireEvent.click(screen.getByRole("button", { name: "Evaluate speech" }));
    await waitFor(() => expect(onSubmit).toHaveBeenCalledWith(resultFixture));
    expect(api.evaluate).toHaveBeenCalledWith("Describe your favorite place.", expect.any(Blob));
  });

  it("shows an error when the microphone is denied", async () => {
    Object.defineProperty(navigator, "mediaDevices", {
      configurable: true,
      value: { getUserMedia: vi.fn().mockRejectedValue(new Error("denied")) },
    });
    const onSubmit = vi.fn();
    render(<Practice onSubmit={onSubmit} prompts={["A prompt."]} />);

    fireEvent.click(screen.getByRole("button", { name: "Record" }));
    await waitFor(() => expect(screen.getByText(/microphone permission was denied/i)).toBeInTheDocument());
  });

  it("warns when the browser does not support recording", () => {
    Object.defineProperty(navigator, "mediaDevices", { configurable: true, value: undefined });
    render(<Practice onSubmit={() => {}} prompts={["A prompt."]} />);

    fireEvent.click(screen.getByRole("button", { name: "Record" }));
    expect(screen.getByText(/audio recording is not supported/i)).toBeInTheDocument();
  });
});
