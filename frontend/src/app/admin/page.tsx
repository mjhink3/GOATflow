"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api/client";
import { useAuth } from "@/lib/hooks/useAuth";

interface AdminUser {
  id: number;
  username: string;
  display_name: string;
  email: string | null;
  provider: string;
  created_at: string;
  role: string;
  level: number | null;
  total_hay_earned: number | null;
  tasks_completed: number | null;
  cheese_state: string | null;
  last_active_at: string | null;
  current_herd_id: number | null;
}

export default function AdminPage() {
  const { user, isAuthenticated } = useAuth();
  const router = useRouter();
  const [users,         setUsers]         = useState<AdminUser[]>([]);
  const [loading,       setLoading]       = useState(true);
  const [search,        setSearch]        = useState("");
  const [confirmDelete, setConfirmDelete] = useState<number | null>(null);
  const [message,       setMessage]       = useState("");

  useEffect(() => {
    if (!isAuthenticated) { router.push("/login"); return; }
    if (user?.username !== "ob_testuser") { router.push("/dashboard"); return; }
    loadUsers();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, user]);

  async function loadUsers() {
    setLoading(true);
    try {
      const res = await api.get<AdminUser[]>("/auth/admin/users");
      setUsers(res.data);
    } finally {
      setLoading(false);
    }
  }

  async function deleteUser(id: number) {
    try {
      await api.delete(`/auth/admin/users/${id}`);
      setUsers(u => u.filter(u => u.id !== id));
      setConfirmDelete(null);
      setMessage("User deleted.");
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setMessage(err?.response?.data?.detail || "Delete failed.");
    }
  }

  async function resetPassword(id: number) {
    try {
      const res = await api.patch<{ temp_password: string }>(`/auth/admin/users/${id}/reset-password`);
      setMessage(`Temp password for user ${id}: ${res.data.temp_password}`);
    } catch {
      setMessage("Reset failed.");
    }
  }

  const filtered = users.filter(u =>
    u.username.toLowerCase().includes(search.toLowerCase()) ||
    (u.display_name ?? "").toLowerCase().includes(search.toLowerCase()) ||
    (u.email ?? "").toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div style={{ minHeight: "100vh", background: "#08080f", color: "#F5F5F5", padding: 32 }}>
      <div style={{ maxWidth: 1100, margin: "0 auto" }}>

        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
          <div>
            <h1 style={{ fontFamily: "var(--font-syne)", fontSize: 22, fontWeight: 800, color: "#F5F5F5" }}>🐐 GOATflow Admin</h1>
            <p style={{ fontSize: 12, color: "#4b5563", marginTop: 4 }}>{users.length} total users</p>
          </div>
          <button onClick={() => router.push("/dashboard")} style={{ background: "none", border: "1px solid #2A2A4A", borderRadius: 8, padding: "8px 16px", fontSize: 12, color: "#6b7280", cursor: "pointer" }}>
            ← Dashboard
          </button>
        </div>

        {message && (
          <div style={{ background: "rgba(97,0,255,0.1)", border: "1px solid rgba(97,0,255,0.3)", borderRadius: 8, padding: "10px 16px", marginBottom: 16, fontSize: 13, color: "#a78bfa", display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ flex: 1 }}>{message}</span>
            <button onClick={() => setMessage("")} style={{ background: "none", border: "none", color: "#6b7280", cursor: "pointer", fontSize: 14 }}>✕</button>
          </div>
        )}

        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search by username, display name, or email…"
          style={{ width: "100%", background: "rgba(255,255,255,0.04)", border: "1px solid #2A2A4A", borderRadius: 8, padding: "10px 14px", fontSize: 13, color: "#F5F5F5", outline: "none", marginBottom: 16, boxSizing: "border-box" }}
        />

        {loading ? (
          <p style={{ color: "#6b7280", fontSize: 13 }}>Loading users…</p>
        ) : (
          <div style={{ background: "rgba(26,26,46,0.8)", border: "1px solid #2A2A4A", borderRadius: 12, overflow: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 900 }}>
              <thead>
                <tr style={{ borderBottom: "1px solid #2A2A4A" }}>
                  {["ID", "Username", "Display Name", "Email", "Provider", "Level", "Hay", "Tracks", "State", "Joined", "Actions"].map(h => (
                    <th key={h} style={{ padding: "10px 12px", textAlign: "left", fontSize: 9, color: "#4b5563", textTransform: "uppercase", letterSpacing: "0.1em", fontWeight: 600, whiteSpace: "nowrap" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map(u => (
                  <tr key={u.id} style={{ borderBottom: "1px solid rgba(42,42,74,0.5)" }}>
                    <td style={{ padding: "10px 12px", fontSize: 12, color: "#4b5563" }}>{u.id}</td>
                    <td style={{ padding: "10px 12px", fontSize: 12, color: "#F5F5F5", fontWeight: 600 }}>{u.username}</td>
                    <td style={{ padding: "10px 12px", fontSize: 12, color: "#9ca3af" }}>{u.display_name}</td>
                    <td style={{ padding: "10px 12px", fontSize: 11, color: "#6b7280" }}>{u.email || "—"}</td>
                    <td style={{ padding: "10px 12px", fontSize: 11, color: "#6b7280" }}>{u.provider || "local"}</td>
                    <td style={{ padding: "10px 12px", fontSize: 12, color: "#a78bfa" }}>{u.level ?? "—"}</td>
                    <td style={{ padding: "10px 12px", fontSize: 12, color: "#f59e0b" }}>{u.total_hay_earned ?? "—"}</td>
                    <td style={{ padding: "10px 12px", fontSize: 12, color: "#53c660" }}>{u.tasks_completed ?? "—"}</td>
                    <td style={{ padding: "10px 12px", fontSize: 11, color: u.cheese_state === "rotting" ? "#ef4444" : u.cheese_state === "staling" ? "#f59e0b" : "#53c660" }}>
                      {u.cheese_state ?? "—"}
                    </td>
                    <td style={{ padding: "10px 12px", fontSize: 11, color: "#4b5563", whiteSpace: "nowrap" }}>
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                    <td style={{ padding: "10px 12px" }}>
                      <div style={{ display: "flex", gap: 6 }}>
                        <button onClick={() => resetPassword(u.id)} style={{ fontSize: 10, padding: "4px 8px", background: "rgba(97,0,255,0.15)", border: "1px solid rgba(97,0,255,0.3)", borderRadius: 6, color: "#a78bfa", cursor: "pointer", whiteSpace: "nowrap" }}>
                          Reset PW
                        </button>
                        {u.username !== "ob_testuser" && (
                          confirmDelete === u.id ? (
                            <>
                              <button onClick={() => deleteUser(u.id)} style={{ fontSize: 10, padding: "4px 8px", background: "rgba(239,68,68,0.2)", border: "1px solid rgba(239,68,68,0.4)", borderRadius: 6, color: "#ef4444", cursor: "pointer" }}>Confirm</button>
                              <button onClick={() => setConfirmDelete(null)} style={{ fontSize: 10, padding: "4px 8px", background: "none", border: "1px solid #2A2A4A", borderRadius: 6, color: "#6b7280", cursor: "pointer" }}>Cancel</button>
                            </>
                          ) : (
                            <button onClick={() => setConfirmDelete(u.id)} style={{ fontSize: 10, padding: "4px 8px", background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)", borderRadius: 6, color: "#ef4444", cursor: "pointer" }}>Delete</button>
                          )
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
