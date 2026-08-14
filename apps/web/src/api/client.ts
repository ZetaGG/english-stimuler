import type {
  EvaluationRecord,
  EvaluationResult,
  EvaluationsPage,
  HealthStatus,
  Stats,
  VocabularyItem,
} from "../types";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export const API_BASE: string = import.meta.env.VITE_API_URL ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      /* keep statusText */
    }
    throw new ApiError(detail, response.status);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const api = {
  health(): Promise<HealthStatus> {
    return request<HealthStatus>("/health");
  },

  stats(): Promise<Stats> {
    return request<Stats>("/v1/stats");
  },

  listEvaluations(limit = 20, offset = 0): Promise<EvaluationsPage> {
    return request<EvaluationsPage>(`/v1/evaluations?limit=${limit}&offset=${offset}`);
  },

  getEvaluation(id: string): Promise<EvaluationRecord> {
    return request<EvaluationRecord>(`/v1/evaluations/${id}`);
  },

  deleteEvaluation(id: string): Promise<void> {
    return request<void>(`/v1/evaluations/${id}`, { method: "DELETE" });
  },

  listVocabulary(): Promise<{ items: VocabularyItem[] }> {
    return request<{ items: VocabularyItem[] }>("/v1/vocabulary");
  },

  removeVocabulary(word: string): Promise<void> {
    return request<void>(`/v1/vocabulary/${encodeURIComponent(word)}`, { method: "DELETE" });
  },

  async evaluate(expectedText: string, audio: Blob): Promise<EvaluationResult> {
    const form = new FormData();
    form.append("expected_text", expectedText);
    const extension = audio.type.includes("webm") ? "webm" : "wav";
    form.append("audio", audio, `recording.${extension}`);
    return request<EvaluationResult>("/v1/evaluate", { method: "POST", body: form });
  },
};
