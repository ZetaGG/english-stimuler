import { describe, expect, it, vi } from "vitest";
import { api } from "./client";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("api client", () => {
  it("fetches health status", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ status: "ok" }));
    vi.stubGlobal("fetch", fetchMock);

    const result = await api.health();

    expect(result).toEqual({ status: "ok" });
    expect(fetchMock).toHaveBeenCalledWith("/health", undefined);
    vi.unstubAllGlobals();
  });

  it("lists evaluations with limit and offset", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ items: [], total: 0 }));
    vi.stubGlobal("fetch", fetchMock);

    await api.listEvaluations(30, 10);

    expect(fetchMock).toHaveBeenCalledWith("/v1/evaluations?limit=30&offset=10", undefined);
    vi.unstubAllGlobals();
  });

  it("deletes an evaluation and returns undefined on 204", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(api.deleteEvaluation("abc")).resolves.toBeUndefined();
    expect(fetchMock).toHaveBeenCalledWith("/v1/evaluations/abc", { method: "DELETE" });
    vi.unstubAllGlobals();
  });

  it("throws ApiError with detail on failure", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ detail: "evaluation not found" }, 404));
    vi.stubGlobal("fetch", fetchMock);

    await expect(api.getEvaluation("missing")).rejects.toMatchObject({
      name: "ApiError",
      status: 404,
      message: "evaluation not found",
    });
    vi.unstubAllGlobals();
  });

  it("posts audio as multipart form with webm filename", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ id: "xyz" }));
    vi.stubGlobal("fetch", fetchMock);

    const audio = new Blob(["fake-audio"], { type: "audio/webm" });
    const result = await api.evaluate("Say this", audio);

    expect(result).toEqual({ id: "xyz" });
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/v1/evaluate");
    expect(init.method).toBe("POST");
    const form = init.body as FormData;
    expect(form.get("expected_text")).toBe("Say this");
    const file = form.get("audio") as File;
    expect(file.name).toBe("recording.webm");
    vi.unstubAllGlobals();
  });
});
