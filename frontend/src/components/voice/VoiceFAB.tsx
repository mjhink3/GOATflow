"use client";

import { useState, useRef, useEffect, useCallback } from "react";

type VoiceState = "idle" | "recording" | "complete";

// Append text to the Track Sieve textarea via React's synthetic event
function appendToSieve(transcript: string) {
  const textarea = document.querySelector(
    "textarea[placeholder*='Paste emails']"
  ) as HTMLTextAreaElement | null;
  if (!textarea) return;

  const existing = textarea.value;
  const next = existing ? `${existing}\n${transcript}` : transcript;

  // Use the native setter so React's onChange fires
  const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value")?.set;
  setter?.call(textarea, next);
  textarea.dispatchEvent(new Event("input", { bubbles: true }));
}

export function VoiceFAB() {
  const [state, setState] = useState<VoiceState>("idle");
  const [timer, setTimer] = useState(0);
  const [showLabel, setShowLabel] = useState(true);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const recognitionRef = useRef<any>(null);
  const timerRef       = useRef<ReturnType<typeof setInterval> | null>(null);
  const stateRef       = useRef<VoiceState>("idle");

  // Keep ref in sync so closure callbacks see current state
  useEffect(() => { stateRef.current = state; }, [state]);

  useEffect(() => {
    const t = setTimeout(() => setShowLabel(false), 3000);
    return () => {
      clearTimeout(t);
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  const stopTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setTimer(0);
  }, []);

  function startRecording() {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const SpeechRecognitionAPI = (window as any).SpeechRecognition ?? (window as any).webkitSpeechRecognition;
    if (!SpeechRecognitionAPI) {
      alert("Voice input not supported in this browser. Try Chrome or Edge.");
      return;
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const recognition: any = new SpeechRecognitionAPI();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";
    recognitionRef.current = recognition;

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    recognition.onresult = (event: any) => {
      const transcript = event.results[0]?.[0]?.transcript ?? "";
      if (transcript) appendToSieve(transcript);
      stopTimer();
      setState("complete");
      setTimeout(() => setState("idle"), 800);
    };

    recognition.onerror = () => {
      stopTimer();
      setState("idle");
    };

    recognition.onend = () => {
      stopTimer();
      setState((prev) => (prev === "recording" ? "idle" : prev));
    };

    recognition.start();
    setState("recording");
    setTimer(0);
    timerRef.current = setInterval(() => setTimer((t) => t + 1), 1000);
  }

  function stopRecording() {
    recognitionRef.current?.stop();
    stopTimer();
    setState("idle");
  }

  function handleClick() {
    if (state === "idle") startRecording();
    else if (state === "recording") stopRecording();
  }

  const fmtTimer = `${String(Math.floor(timer / 60)).padStart(2, "0")}:${String(timer % 60).padStart(2, "0")}`;

  // Style by state
  const bgColor =
    state === "idle"      ? "rgba(97,0,255,0.85)"
    : state === "recording" ? "rgba(239,68,68,0.9)"
    :                         "rgba(83,198,96,0.9)";

  const pulseClass =
    state === "idle"      ? "animate-gf-mic-pulse"
    : state === "recording" ? ""
    :                         "";

  return (
    <div
      className="fixed flex flex-col items-center gap-1"
      style={{ bottom: 84, right: 18, zIndex: 40 }}
    >
      {/* "Voice Drop" label */}
      <span
        style={{
          fontSize: 9, color: "#a78bfa", fontWeight: 600, textTransform: "uppercase",
          letterSpacing: "0.12em", opacity: showLabel ? 1 : 0,
          transition: "opacity 0.6s ease",
          pointerEvents: "none",
        }}
      >
        Voice Drop
      </span>

      {/* Recording pulse rings (behind button) */}
      {state === "recording" && (
        <>
          <span className="animate-gf-ring-pulse absolute rounded-full" style={{ inset: -4, background: "rgba(239,68,68,0.25)" }} />
          <span className="animate-gf-ring-pulse absolute rounded-full" style={{ inset: -4, background: "rgba(239,68,68,0.15)", animationDelay: "0.4s" }} />
        </>
      )}

      {/* FAB button */}
      <button
        onClick={handleClick}
        className={`relative rounded-full flex items-center justify-center ${pulseClass}`}
        style={{
          width: 52, height: 52,
          background: bgColor,
          border: "none",
          cursor: "pointer",
          boxShadow: "0 4px 20px rgba(97,0,255,0.4)",
          transition: "background 0.2s ease",
          flexShrink: 0,
        }}
        aria-label={state === "idle" ? "Start voice input" : "Stop recording"}
      >
        {state === "idle" && (
          <svg width="22" height="22" viewBox="0 0 24 24" fill="white">
            <path d="M12 1a4 4 0 0 0-4 4v7a4 4 0 0 0 8 0V5a4 4 0 0 0-4-4z"/>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2H3v2a9 9 0 0 0 8 8.94V23h2v-2.06A9 9 0 0 0 21 12v-2h-2z"/>
          </svg>
        )}
        {state === "recording" && (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="white">
            <rect x="6" y="6" width="12" height="12" rx="2"/>
          </svg>
        )}
        {state === "complete" && (
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
        )}
      </button>

      {/* Timer during recording */}
      {state === "recording" && (
        <span style={{ fontSize: 9, color: "#ef4444", fontFamily: "monospace", fontWeight: 700 }}>
          {fmtTimer}
        </span>
      )}
    </div>
  );
}
