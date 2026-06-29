"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/lib/hooks/useAuth";
import { signIn } from "next-auth/react";

/* ── Terrain layer data (exact from app.py) ────────────────────────────────── */
const TERRAIN_LAYERS = [
  {
    top: "0",
    height: "30%",
    bg: "#0e0e1e",
    clip: "polygon(0% 100%,0% 75%,8% 45%,15% 60%,22% 20%,30% 55%,38% 10%,47% 50%,55% 30%,63% 55%,72% 15%,80% 45%,88% 35%,95% 55%,100% 40%,100% 100%)",
  },
  {
    top: "18%",
    height: "25%",
    bg: "#0f0f20",
    clip: "polygon(0% 100%,0% 50%,5% 45%,5% 20%,12% 18%,12% 45%,25% 40%,35% 35%,35% 15%,45% 12%,45% 35%,60% 30%,70% 28%,70% 10%,80% 8%,80% 28%,90% 32%,100% 28%,100% 100%)",
  },
  {
    top: "35%",
    height: "22%",
    bg: "#101022",
    clip: "polygon(0% 100%,0% 60%,10% 45%,20% 50%,35% 35%,50% 40%,65% 30%,80% 42%,90% 38%,100% 45%,100% 100%)",
  },
  {
    top: "52%",
    height: "20%",
    bg: "#111124",
    clip: "polygon(0% 100%,0% 65%,15% 55%,30% 60%,45% 50%,60% 58%,75% 48%,90% 55%,100% 52%,100% 100%)",
  },
  {
    top: "68%",
    height: "18%",
    bg: "#121226",
    clip: "polygon(0% 100%,0% 72%,20% 68%,40% 72%,60% 67%,80% 71%,100% 68%,100% 100%)",
  },
  {
    top: "82%",
    height: "20%",
    bg: "#13132a",
    clip: "polygon(0% 100%,0% 80%,100% 80%,100% 100%)",
  },
];

const TERRAIN_LABELS = [
  { top: "8%",  label: "The Summit" },
  { top: "24%", label: "The High Cliffs" },
  { top: "40%", label: "The Ridgeline" },
  { top: "56%", label: "The Foothills" },
  { top: "72%", label: "The Grazing Grounds" },
  { top: "86%", label: "The Pen" },
];

/* ── Deterministic particles (seeded so SSR matches client) ─────────────────── */
const PARTICLES = Array.from({ length: 12 }, (_, i) => {
  const seed = i / 12;
  return {
    left:  `${(seed * 98 + i * 7.3) % 98}%`,
    top:   `${(seed * 95 + i * 8.1) % 95}%`,
    dur:   `${4 + (seed * 4)}s`,
    delay: `${(seed * 4)}s`,
    ty:    `-${15 + Math.floor(seed * 15)}px`,
  };
});

export default function LoginPage() {
  const router = useRouter();
  const { login, signup, isAuthenticated } = useAuth();

  const [tab, setTab] = useState<"login" | "signup">("login");
  const [pending, setPending] = useState(false);
  const [loginError, setLoginError] = useState("");
  const [emailInput, setEmailInput] = useState("");
  const [emailSent, setEmailSent] = useState(false);
  const [emailPending, setEmailPending] = useState(false);
  const [emailError, setEmailError] = useState("");

  // Login form
  const [loginUsername, setLoginUsername] = useState("");
  const [loginPassword, setLoginPassword] = useState("");

  // Signup form
  const [signupUsername, setSignupUsername] = useState("");
  const [signupPassword, setSignupPassword] = useState("");
  const [signupDisplay,  setSignupDisplay]  = useState("");

  useEffect(() => {
    if (isAuthenticated) router.replace("/dashboard");
  }, [isAuthenticated, router]);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    if (!loginUsername.trim() || !loginPassword.trim()) return;
    setLoginError("");
    console.log("[login] submitting for:", loginUsername.trim());
    setPending(true);
    try {
      await login(loginUsername.trim(), loginPassword);
      console.log("[login] success — redirecting to /dashboard");
      window.location.href = "/dashboard";
    } catch (err: unknown) {
      console.error("[login] failed:", err);
      const axiosErr = err as { response?: { data?: { detail?: string | { msg: string }[] } } };
      const detail = axiosErr?.response?.data?.detail;
      const msg = typeof detail === "string"
        ? detail
        : Array.isArray(detail)
        ? detail[0]?.msg ?? "Login failed."
        : "Login failed. Check your Goatname and Paaassword.";
      setLoginError(msg);
    } finally {
      setPending(false);
    }
  }

  async function handleSignup(e: React.FormEvent) {
    e.preventDefault();
    if (!signupUsername.trim() || !signupPassword.trim() || !signupDisplay.trim()) return;
    setLoginError("");
    console.log("[signup] submitting for:", signupUsername.trim());
    setPending(true);
    try {
      await signup(signupUsername.trim(), signupPassword, signupDisplay.trim());
      console.log("[signup] success — redirecting to /dashboard");
      window.location.href = "/dashboard";
    } catch (err: unknown) {
      console.error("[signup] failed:", err);
      const axiosErr = err as { response?: { data?: { detail?: string | { msg: string }[] } } };
      const detail = axiosErr?.response?.data?.detail;
      const msg = typeof detail === "string"
        ? detail
        : Array.isArray(detail)
        ? detail[0]?.msg ?? "Sign up failed."
        : "Sign up failed. That Goatname may already be taken.";
      setLoginError(msg);
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="relative min-h-screen w-full overflow-hidden bg-goat-black flex flex-col items-center justify-center">

      {/* ── Terrain background layers ── */}
      <div className="fixed inset-0 z-[1] pointer-events-none overflow-hidden">
        {TERRAIN_LAYERS.map((layer, i) => (
          <div
            key={i}
            style={{
              position: "absolute",
              width: "100%",
              height: layer.height,
              top: layer.top,
              background: layer.bg,
              opacity: 0.25,
              clipPath: layer.clip,
              pointerEvents: "none",
            }}
          />
        ))}
      </div>

      {/* ── Terrain labels ── */}
      <div className="fixed inset-0 z-[2] pointer-events-none">
        {TERRAIN_LABELS.map(({ top, label }) => (
          <span
            key={label}
            style={{
              position: "fixed",
              right: "12px",
              top,
              fontFamily: "'DM Sans', sans-serif",
              fontSize: "8px",
              color: "rgba(255,255,255,0.06)",
              letterSpacing: "0.2em",
              textTransform: "uppercase",
            }}
          >
            {label}
          </span>
        ))}
      </div>

      {/* ── Ambient particles ── */}
      <div className="fixed inset-0 z-[3] pointer-events-none overflow-hidden">
        {PARTICLES.map((p, i) => (
          <div
            key={i}
            style={{
              position: "absolute",
              width: "3px",
              height: "3px",
              borderRadius: "50%",
              background: "rgba(124,58,237,0.4)",
              left: p.left,
              top: p.top,
              animation: `gfParticleFloat ${p.dur} ease-in-out ${p.delay} infinite`,
              ["--ty" as string]: p.ty,
            }}
          />
        ))}
      </div>

      {/* ── Main content ── */}
      <main className="relative z-10 flex flex-col items-center w-full max-w-sm px-4 pt-6 pb-8">

        {/* Logo */}
        <div className="animate-gf-fade-slide-down mb-0 flex justify-center">
          <Image
            src="/icons/goatflow_main_screen_logo.webp"
            alt="GOATflow"
            width={200}
            height={200}
            priority
            style={{ width: 200, height: "auto", objectFit: "contain" }}
          />
        </div>

        {/* Tagline */}
        <p
          className="animate-gf-fade-slide-up text-center mb-4"
          style={{
            fontFamily: "'DM Sans', sans-serif",
            fontSize: "16px",
            color: "rgba(255,255,255,0.55)",
            letterSpacing: "0.05em",
            animationDelay: "400ms",
            marginTop: 4,
          }}
        >
          Grab life by the horns. Leave the bull behind.
        </p>

        {/* Auth card */}
        <div
          className="w-full rounded-xl border border-goat-border p-4 animate-gf-fade-in"
          style={{
            background: "rgba(13,13,26,0.85)",
            backdropFilter: "blur(12px)",
            animationDelay: "200ms",
          }}
        >
          {/* ── OAuth providers ── */}
          <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 12 }}>
            <button
              onClick={() => signIn("google", { callbackUrl: "/auth/callback" })}
              style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 10, width: "100%", padding: "8px 16px", borderRadius: 10, border: "1px solid rgba(255,255,255,0.12)", background: "rgba(255,255,255,0.05)", color: "#F5F5F5", fontSize: 13, fontWeight: 600, cursor: "pointer" }}
            >
              <svg width="18" height="18" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
              Continue with Google
            </button>
            <button
              onClick={() => signIn("github", { callbackUrl: "/auth/callback" })}
              style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 10, width: "100%", padding: "8px 16px", borderRadius: 10, border: "1px solid rgba(255,255,255,0.12)", background: "rgba(255,255,255,0.05)", color: "#F5F5F5", fontSize: 13, fontWeight: 600, cursor: "pointer" }}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="#F5F5F5"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z"/></svg>
              Continue with GitHub
            </button>
            <button
              onClick={() => signIn("azure-ad", { callbackUrl: "/auth/callback" })}
              style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 10, width: "100%", padding: "8px 16px", borderRadius: 10, border: "1px solid rgba(255,255,255,0.12)", background: "rgba(255,255,255,0.05)", color: "#F5F5F5", fontSize: 13, fontWeight: 600, cursor: "pointer" }}
            >
              <svg width="18" height="18" viewBox="0 0 23 23"><path fill="#f3f3f3" d="M0 0h23v23H0z"/><path fill="#f35325" d="M1 1h10v10H1z"/><path fill="#81bc06" d="M12 1h10v10H12z"/><path fill="#05a6f0" d="M1 12h10v10H1z"/><path fill="#ffba08" d="M12 12h10v10H12z"/></svg>
              Continue with Microsoft
            </button>

            {/* ── Email magic link ── */}
            {emailSent ? (
              <div style={{ padding: "12px 16px", borderRadius: 10, border: "1px solid rgba(83,198,96,0.3)", background: "rgba(83,198,96,0.08)", textAlign: "center" }}>
                <p style={{ fontSize: 13, color: "#53c660", fontWeight: 600 }}>Check your inbox 📬</p>
                <p style={{ fontSize: 11, color: "#9ca3af", marginTop: 4 }}>Magic link sent to {emailInput}</p>
              </div>
            ) : (
              <>
                <input
                  type="email"
                  value={emailInput}
                  onChange={e => setEmailInput(e.target.value)}
                  placeholder="Enter your email"
                  style={{ width: "100%", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 10, padding: "8px 14px", fontSize: 13, color: "#F5F5F5", outline: "none", boxSizing: "border-box" }}
                />
                {emailError && (
                  <p style={{ fontSize: 11, color: "#ef4444", textAlign: "center", margin: 0 }}>{emailError}</p>
                )}
                <button
                  onClick={async () => {
                    if (!emailInput.trim() || emailPending) return;
                    setEmailError("");
                    setEmailPending(true);
                    try {
                      const result = await signIn("email", {
                        email: emailInput.trim(),
                        callbackUrl: "/auth/callback",
                        redirect: false,
                      });
                      if (result?.ok) {
                        setEmailSent(true);
                      } else {
                        setEmailError(result?.error ?? "Failed to send link. Check your email and try again.");
                      }
                    } catch {
                      setEmailError("Something went wrong. Please try again.");
                    } finally {
                      setEmailPending(false);
                    }
                  }}
                  disabled={!emailInput.trim() || emailPending}
                  style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 10, width: "100%", padding: "8px 16px", borderRadius: 10, border: "1px solid rgba(255,255,255,0.12)", background: "rgba(255,255,255,0.05)", color: (!emailInput.trim() || emailPending) ? "#6b7280" : "#F5F5F5", fontSize: 13, fontWeight: 600, cursor: (emailInput.trim() && !emailPending) ? "pointer" : "not-allowed", opacity: (emailInput.trim() && !emailPending) ? 1 : 0.5 }}
                >
                  {emailPending ? "Sending…" : "Continue with Email ✉️"}
                </button>
              </>
            )}
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
            <div style={{ flex: 1, height: 1, background: "rgba(255,255,255,0.08)" }} />
            <span style={{ fontSize: 11, color: "#4b5563" }}>or</span>
            <div style={{ flex: 1, height: 1, background: "rgba(255,255,255,0.08)" }} />
          </div>

          <Tabs value={tab} onValueChange={(v) => setTab(v as "login" | "signup")}>
            <TabsList className="w-full mb-3 bg-goat-card border border-goat-border">
              <TabsTrigger value="login"  className="flex-1 text-xs font-semibold uppercase tracking-widest data-[state=active]:bg-goat-button data-[state=active]:text-white">
                Login
              </TabsTrigger>
              <TabsTrigger value="signup" className="flex-1 text-xs font-semibold uppercase tracking-widest data-[state=active]:bg-goat-button data-[state=active]:text-white">
                Create Account
              </TabsTrigger>
            </TabsList>

            {/* ── Login tab ── */}
            <TabsContent value="login">
              <form onSubmit={handleLogin} className="flex flex-col gap-2">
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="login-username" className="text-xs uppercase tracking-widest text-goat-silver">
                    Goatname
                  </Label>
                  <Input
                    id="login-username"
                    autoComplete="username"
                    placeholder="yourgoatname"
                    value={loginUsername}
                    onChange={(e) => setLoginUsername(e.target.value)}
                    className="bg-goat-black border-goat-border text-goat-white placeholder:text-goat-border focus:border-goat-violet"
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="login-password" className="text-xs uppercase tracking-widest text-goat-silver">
                    Paaassword
                  </Label>
                  <Input
                    id="login-password"
                    type="password"
                    autoComplete="current-password"
                    placeholder="••••••••"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    className="bg-goat-black border-goat-border text-goat-white placeholder:text-goat-border focus:border-goat-violet"
                  />
                </div>
                {loginError && (
                  <p className="text-xs text-goat-red text-center">{loginError}</p>
                )}
                <Button
                  type="submit"
                  disabled={pending || !loginUsername.trim() || !loginPassword.trim()}
                  className="mt-1 w-full bg-goat-button hover:bg-goat-purple text-white font-bold uppercase tracking-widest text-xs py-2.5"
                >
                  {pending ? "Entering the Pasture…" : "Enter the Pasture →"}
                </Button>
              </form>
            </TabsContent>

            {/* ── Signup tab ── */}
            <TabsContent value="signup">
              <form onSubmit={handleSignup} className="flex flex-col gap-2">
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="signup-username" className="text-xs uppercase tracking-widest text-goat-silver">
                    Goatname
                  </Label>
                  <Input
                    id="signup-username"
                    autoComplete="username"
                    placeholder="yourgoatname"
                    value={signupUsername}
                    onChange={(e) => setSignupUsername(e.target.value)}
                    className="bg-goat-black border-goat-border text-goat-white placeholder:text-goat-border focus:border-goat-violet"
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="signup-password" className="text-xs uppercase tracking-widest text-goat-silver">
                    Paaassword
                  </Label>
                  <Input
                    id="signup-password"
                    type="password"
                    autoComplete="new-password"
                    placeholder="••••••••"
                    value={signupPassword}
                    onChange={(e) => setSignupPassword(e.target.value)}
                    className="bg-goat-black border-goat-border text-goat-white placeholder:text-goat-border focus:border-goat-violet"
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="signup-display" className="text-xs uppercase tracking-widest text-goat-silver">
                    Display Name
                  </Label>
                  <Input
                    id="signup-display"
                    autoComplete="name"
                    placeholder="The name your legend is known by"
                    value={signupDisplay}
                    onChange={(e) => setSignupDisplay(e.target.value)}
                    className="bg-goat-black border-goat-border text-goat-white placeholder:text-goat-border focus:border-goat-violet"
                  />
                </div>
                {loginError && (
                  <p className="text-xs text-goat-red text-center">{loginError}</p>
                )}
                <Button
                  type="submit"
                  disabled={pending || !signupUsername.trim() || !signupPassword.trim() || !signupDisplay.trim()}
                  className="mt-1 w-full bg-goat-button hover:bg-goat-purple text-white font-bold uppercase tracking-widest text-xs py-2.5"
                >
                  {pending ? "Building Your Legacy…" : "Claim Your Pasture →"}
                </Button>
              </form>
            </TabsContent>
          </Tabs>
        </div>
      </main>

      {/* ── Global footer ── */}
      <footer
        className="fixed bottom-0 left-0 right-0 z-10 py-3 text-center animate-gf-fade-in"
        style={{ animationDelay: "1100ms" }}
      >
        <p
          style={{
            fontFamily: "'DM Sans', sans-serif",
            fontSize: "9px",
            color: "rgba(255,255,255,0.18)",
            letterSpacing: "0.08em",
          }}
        >
          GOATflow is a subsidiary of the WorkGOAT Ecosystem.{" "}
          Build your legacy at{" "}
          <span style={{ color: "rgba(139,92,246,0.5)" }}>workgoat.vip</span>
        </p>
      </footer>
    </div>
  );
}
