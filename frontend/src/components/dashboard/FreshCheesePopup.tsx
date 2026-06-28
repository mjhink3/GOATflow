"use client";

import { useState } from "react";
import Image from "next/image";
import { FRESH_CHEESE_PUNS } from "@/lib/gamification";

interface FreshCheesePopupProps {
  count: number;
  total: number;
  onConfirm: () => void;
}

export function FreshCheesePopup({ count, total, onConfirm }: FreshCheesePopupProps) {
  const [pun] = useState(() => FRESH_CHEESE_PUNS[Math.floor(Math.random() * FRESH_CHEESE_PUNS.length)]);

  return (
    <div
      className="fixed inset-0 flex items-center justify-center"
      style={{ zIndex: 60, background: "rgba(8,8,15,0.90)" }}
    >
      <div
        className="animate-cheese-pulse rounded-2xl border border-goat-border flex flex-col items-center gap-4"
        style={{
          background: "rgba(13,13,26,0.98)", padding: "32px 28px 24px",
          width: 360, maxWidth: "calc(100vw - 32px)",
        }}
      >
        {/* Cheese icon */}
        <Image src="/icons/icon_fresh_cheese.webp" alt="Fresh Cheese" width={56} height={56} />

        {/* Pun headline */}
        <p className="font-syne font-bold text-center" style={{ fontSize: 13, color: "#22c55e", letterSpacing: "0.05em" }}>
          {pun}
        </p>

        {/* Count */}
        <p className="font-syne font-black text-center" style={{ fontSize: 42, color: "#22c55e", lineHeight: 1 }}>
          +{count} Fresh Cheese banked 🧀
        </p>

        {/* Total */}
        <p style={{ fontSize: 12, color: "#9ca3af", textAlign: "center" }}>
          You now hold <span style={{ color: "#22c55e", fontWeight: 700 }}>{total}</span> total Fresh Cheese
        </p>

        {/* Confirm */}
        <button
          onClick={onConfirm}
          className="w-full py-3 rounded-xl font-bold uppercase tracking-widest"
          style={{
            fontSize: 13, background: "rgba(34,197,94,0.2)",
            border: "1px solid rgba(34,197,94,0.5)", color: "#22c55e",
            cursor: "pointer",
          }}
        >
          Got It, GOAT!
        </button>
      </div>
    </div>
  );
}
