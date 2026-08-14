import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { EvaluationResult } from "../types";
import { Waveform } from "./Waveform";

const DEFAULT_PROMPTS = [
  "Describe your favorite place to relax and explain why you like it.",
  "Talk about a skill you would like to learn this year and why.",
  "What is the most useful technology you use every day? Explain how it changed your life.",
  "Describe a memorable trip you have taken and what you learned from it.",
  "Talk about a person who has influenced you and the qualities you admire in them.",
  "What do you think makes a good friend? Give reasons and examples.",
];

function pickPrompt(prompts: string[]): string {
  return prompts[Math.floor(Math.random() * prompts.length)];
}

type Status = "idle" | "recording" | "recorded" | "submitting" | "error";

interface PracticeProps {
  onSubmit: (result: EvaluationResult) => void;
  prompts?: string[];
}

function formatSeconds(total: number): string {
  const minutes = Math.floor(total / 60);
  const seconds = (total % 60).toFixed(0).padStart(2, "0");
  return `${minutes}:${seconds}`;
}

export function Practice({ onSubmit, prompts = DEFAULT_PROMPTS }: PracticeProps) {
  const [prompt, setPrompt] = useState(() => pickPrompt(prompts));
  const [status, setStatus] = useState<Status>("idle");
  const [elapsed, setElapsed] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [blob, setBlob] = useState<Blob | null>(null);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);

  const clearTimer = useCallback(() => {
    if (timerRef.current !== null) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  useEffect(() => () => clearTimer(), [clearTimer]);

  const startRecording = useCallback(async () => {
    setError(null);
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      setError("Audio recording is not supported in this browser. Try Chrome, Edge or Firefox.");
      setStatus("error");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onstop = () => {
        const audio = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        setBlob(audio);
        setStatus("recorded");
        stream.getTracks().forEach((track) => track.stop());
      };
      recorderRef.current = recorder;
      recorder.start();
      setStatus("recording");
      setElapsed(0);
      const startedAt = Date.now();
      timerRef.current = window.setInterval(() => {
        setElapsed((Date.now() - startedAt) / 1000);
      }, 250);
    } catch {
      setError("Microphone permission was denied. Allow access to record your voice.");
      setStatus("error");
    }
  }, []);

  const stopRecording = useCallback(() => {
    clearTimer();
    recorderRef.current?.stop();
  }, [clearTimer]);

  const newPrompt = useCallback(() => {
    setBlob(null);
    setError(null);
    setElapsed(0);
    setStatus("idle");
    setPrompt((current) => {
      const next = pickPrompt(prompts);
      return next === current ? pickPrompt(prompts) : next;
    });
  }, [prompts]);

  const submit = useCallback(async () => {
    if (!blob) return;
    setStatus("submitting");
    try {
      const result = await api.evaluate(prompt, blob);
      onSubmit(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Evaluation failed. Please try again.");
      setStatus("error");
    }
  }, [blob, prompt, onSubmit]);

  return (
    <div className="practice-card card">
      <div className="section-head">
        <h2>Impromptu speaking</h2>
        <span className="muted">Speak for about 30 seconds</span>
      </div>

      <p className="prompt">{prompt}</p>

      {status === "recording" ? (
        <>
          <Waveform />
          <div className="timer">{formatSeconds(elapsed)}</div>
          <button className="record-btn recording" onClick={stopRecording}>
            Stop
          </button>
          <p className="hint">Read the prompt aloud. Stop when you finish.</p>
        </>
      ) : (
        <>
          <button className="record-btn" onClick={startRecording}>
            {status === "idle" ? "Record" : "Re-record"}
          </button>
          <p className="hint">{status === "recorded" ? "Recording ready — evaluate it below." : "Tap to start recording your answer."}</p>
        </>
      )}

      {error && <div className="error-banner">{error}</div>}

      <div className="section-head">
        <button className="btn-ghost btn" onClick={newPrompt} disabled={status === "recording" || status === "submitting"}>
          New topic
        </button>
        <button
          className="btn btn-teal"
          onClick={submit}
          disabled={status !== "recorded"}
          aria-busy={status === "submitting"}
        >
          {status === "submitting" ? "Analyzing…" : "Evaluate speech"}
        </button>
      </div>
    </div>
  );
}
