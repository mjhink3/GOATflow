"use client";

import { useEffect } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";

export default function AuthCallback() {
  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    console.log("[AuthCallback] status:", status, "session:", session);
    if (status === "loading") return;
    if (session && (session as any).goatflow_token) {
      console.log("[AuthCallback] token found, redirecting to dashboard");
      localStorage.setItem("goatflow_token", (session as any).goatflow_token);
      router.replace("/dashboard");
    } else if (status === "authenticated") {
      // Session exists but goatflow_token missing — signIn callback likely failed
      console.error("[AuthCallback] authenticated but no goatflow_token:", session);
      router.replace("/login?error=token_missing");
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
