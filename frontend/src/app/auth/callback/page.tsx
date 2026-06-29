"use client";

import { useEffect } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";

export default function AuthCallback() {
  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (status === "loading") return;
    if (session && (session as any).goatflow_token) {
      localStorage.setItem("goatflow_token", (session as any).goatflow_token);
      router.replace("/dashboard");
    } else if (status === "unauthenticated") {
      router.replace("/login");
    }
  }, [session, status, router]);

  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh", background: "#08080f" }}>
      <p style={{ color: "#a78bfa", fontSize: 14, fontFamily: "var(--font-syne)" }}>
        Entering the pasture…
      </p>
    </div>
  );
}
