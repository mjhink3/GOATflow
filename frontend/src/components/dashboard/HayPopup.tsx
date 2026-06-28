"use client";

import { useEffect, useRef, useState } from "react";
import Image from "next/image";
import type { CompletionResult } from "@/lib/types";
import { HAY_PUNS, GOAT_PUNS, LEVEL_IMAGES, pasture_name } from "@/lib/gamification";

const CONFETTI_COLORS = [
  "#6100ff", "#a78bfa", "#f59e0b", "#53c660", "#ef4444", "#F5F5F5", "#fbbf24", "#c4b5fd",
];

interface HayPopupProps {
  result: CompletionResult;
  onConfirm: () => void;
}

export function HayPopup({ result, onConfirm }: HayPopupProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [hayPun] = useState(() => HAY_PUNS[Math.floor(Math.random() * HAY_PUNS.length)]);
  const [goatPun] = useState(() => GOAT_PUNS[Math.floor(Math.random() * GOAT_PUNS.length)]);

  const showMult = result.difficulty_multiplier !== 1.0;
  const oldLevel = result.new_level - 1;
  const oldPasture = pasture_name(oldLevel);
  const levelImg = LEVEL_IMAGES[Math.min(result.new_level, 7)] ?? LEVEL_IMAGES[7];

  // Confetti canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    type Particle = {
      x: number; y: number; vx: number; vy: number;
      r: number; rSpeed: number; color: string;
      w: number; h: number; alpha: number;
    };

    const particles: Particle[] = Array.from({ length: 90 }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height * -0.6,
      vx: (Math.random() - 0.5) * 3.5,
      vy: Math.random() * 3.5 + 1.5,
      r: Math.random() * 360,
      rSpeed: (Math.random() - 0.5) * 7,
      color: CONFETTI_COLORS[Math.floor(Math.random() * CONFETTI_COLORS.length)],
      w: Math.random() * 9 + 4,
      h: Math.random() * 5 + 2,
      alpha: 0.9 + Math.random() * 0.1,
    }));

    let rafId: number;
    let alive = true;

    function draw() {
      if (!alive) return;
      ctx!.clearRect(0, 0, canvas!.width, canvas!.height);
      let anyVisible = false;
      for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;
        p.vy += 0.06;
        p.r += p.rSpeed;
        p.alpha -= 0.0035;
        if (p.alpha <= 0) continue;
        anyVisible = true;
        ctx!.save();
        ctx!.globalAlpha = p.alpha;
        ctx!.fillStyle = p.color;
        ctx!.translate(p.x, p.y);
        ctx!.rotate((p.r * Math.PI) / 180);
        ctx!.fillRect(-p.w / 2, -p.h / 2, p.w, p.h);
        ctx!.restore();
      }
      if (anyVisible) rafId = requestAnimationFrame(draw);
    }

    rafId = requestAnimationFrame(draw);
    return () => {
      alive = false;
      cancelAnimationFrame(rafId);
    };
  }, []);

  return (
    <div className="fixed inset-0" style={{ zIndex: 55 }}>
      {/* Backdrop */}
      <div className="absolute inset-0" style={{ background: "rgba(8,8,15,0.88)" }} />

      {/* Confetti canvas — renders over backdrop, under card */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 pointer-events-none"
        style={{ width: "100%", height: "100%", zIndex: 1 }}
      />

      {/* Modal card — centered via animate-gf-pop-in (translate -50/-50 in keyframe) */}
      <div
        className="absolute animate-gf-pop-in"
        style={{
          left: "50%", top: "50%", zIndex: 2,
          width: 400, maxWidth: "calc(100vw - 32px)",
        }}
      >
        <div
          className="rounded-2xl border border-goat-border flex flex-col gap-4"
          style={{ background: "rgba(13,13,26,0.98)", padding: "28px 28px 24px" }}
        >
          {/* Hay pun headline */}
          <p className="font-syne font-bold text-center" style={{ fontSize: 13, color: "#f59e0b", letterSpacing: "0.05em" }}>
            {hayPun}
          </p>

          {/* Hay amount */}
          <div className="flex flex-col items-center gap-1">
            <span className="font-syne font-black" style={{ fontSize: 52, color: "#f59e0b", lineHeight: 1 }}>
              +{result.hay_earned} Hay 🌾
            </span>

            {showMult && (
              <span style={{ fontSize: 11, color: "#f59e0b", fontWeight: 600 }}>
                {result.difficulty_multiplier.toFixed(2)}x difficulty multiplier
              </span>
            )}
          </div>

          {/* Task name */}
          <p className="text-center" style={{ fontSize: 12, color: "#C0C0C0", fontStyle: "italic" }}>
            &ldquo;{result.task_name}&rdquo;
          </p>

          {/* Goat pun */}
          <p className="text-center" style={{ fontSize: 11, color: "#8B5CF6", fontStyle: "italic" }}>
            {goatPun}
          </p>

          {/* Level-up celebration panel */}
          {result.leveled_up && (
            <div
              className="animate-fence-sequence rounded-xl border flex flex-col items-center gap-3 py-5 px-4"
              style={{ borderColor: "rgba(139,92,246,0.5)", background: "rgba(97,0,255,0.12)" }}
            >
              <p className="font-syne font-black animate-fence-shake" style={{ fontSize: 18, color: "#a78bfa", letterSpacing: "0.15em" }}>
                🚧 FENCE BROKEN! 🚧
              </p>

              <Image
                src={levelImg}
                alt={`Level ${result.new_level}`}
                width={96}
                height={96}
                className="rounded-full border-2"
                style={{ borderColor: "rgba(139,92,246,0.6)" }}
              />

              <div className="flex items-center gap-3 text-sm">
                <span style={{ color: "#6b7280", fontSize: 11 }}>{oldPasture}</span>
                <span style={{ color: "#a78bfa" }}>→</span>
                <span className="font-syne font-bold" style={{ color: "#a78bfa", fontSize: 11 }}>{result.pasture_name}</span>
              </div>

              <p className="font-syne font-black" style={{ fontSize: 22, color: "#F5F5F5" }}>
                Level {result.new_level}
              </p>
            </div>
          )}

          {/* Confirm button */}
          <button
            onClick={onConfirm}
            className="w-full py-3 rounded-xl font-bold uppercase tracking-widest"
            style={{
              fontSize: 13, background: "rgba(245,158,11,0.25)",
              border: "1px solid rgba(245,158,11,0.55)", color: "#f59e0b",
              cursor: "pointer",
            }}
          >
            Stack the Hay 🌾
          </button>
        </div>
      </div>
    </div>
  );
}
