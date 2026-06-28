"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/lib/hooks/useAuth";

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
      <main className="relative z-10 flex flex-col items-center w-full max-w-sm px-4 pt-16 pb-24">

        {/* Logo */}
        <div className="animate-gf-fade-slide-down mb-2">
          <Image
            src="/icons/goatflow_main_screen_logo.webp"
            alt="GOATflow"
            width={190}
            height={190}
            priority
            style={{ width: 190, height: "auto" }}
          />
        </div>

        {/* Tagline */}
        <p
          className="animate-gf-fade-slide-up text-center mb-8"
          style={{
            fontFamily: "'DM Sans', sans-serif",
            fontSize: "13px",
            color: "rgba(255,255,255,0.55)",
            letterSpacing: "0.05em",
            animationDelay: "400ms",
          }}
        >
          Grab life by the horns. Leave the bull behind.
        </p>

        {/* Auth card */}
        <div
          className="w-full rounded-xl border border-goat-border p-6 animate-gf-fade-in"
          style={{
            background: "rgba(13,13,26,0.85)",
            backdropFilter: "blur(12px)",
            animationDelay: "200ms",
          }}
        >
          <Tabs value={tab} onValueChange={(v) => setTab(v as "login" | "signup")}>
            <TabsList className="w-full mb-6 bg-goat-card border border-goat-border">
              <TabsTrigger value="login"  className="flex-1 text-xs font-semibold uppercase tracking-widest data-[state=active]:bg-goat-button data-[state=active]:text-white">
                Login
              </TabsTrigger>
              <TabsTrigger value="signup" className="flex-1 text-xs font-semibold uppercase tracking-widest data-[state=active]:bg-goat-button data-[state=active]:text-white">
                Create Account
              </TabsTrigger>
            </TabsList>

            {/* ── Login tab ── */}
            <TabsContent value="login">
              <form onSubmit={handleLogin} className="flex flex-col gap-4">
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
                  className="mt-2 w-full bg-goat-button hover:bg-goat-purple text-white font-bold uppercase tracking-widest text-xs py-5"
                >
                  {pending ? "Entering the Pasture…" : "Enter the Pasture →"}
                </Button>
              </form>
            </TabsContent>

            {/* ── Signup tab ── */}
            <TabsContent value="signup">
              <form onSubmit={handleSignup} className="flex flex-col gap-4">
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
                  className="mt-2 w-full bg-goat-button hover:bg-goat-purple text-white font-bold uppercase tracking-widest text-xs py-5"
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
