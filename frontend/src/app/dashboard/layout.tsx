"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/hooks/useAuth";
import { Sidebar }  from "@/components/layout/Sidebar";
import { LevelBar } from "@/components/layout/LevelBar";
import { VoiceFAB } from "@/components/voice/VoiceFAB";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) return null;
  if (!isAuthenticated) return null;

  return (
    <div className="flex min-h-screen bg-goat-black">
      <Sidebar isMobileOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <main className="flex-1 flex flex-col min-h-screen pb-10 overflow-y-auto overflow-x-hidden">
        <button
          className="md:hidden fixed top-3 left-3 z-30 w-10 h-10 flex items-center justify-center rounded-lg"
          style={{ background: "rgba(13,13,26,0.9)", border: "1px solid #2A2A4A", color: "#F5F5F5", fontSize: 18 }}
          onClick={() => setSidebarOpen(true)}
          aria-label="Open menu"
        >
          ☰
        </button>
        {children}
      </main>
      <LevelBar />
      <VoiceFAB />
    </div>
  );
}
