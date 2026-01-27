"use client";

import { useState, useEffect } from "react";
import { Shield, LogOut, RefreshCcw, Trash2, TrendingUp, Activity, Database, Lock } from "lucide-react";
import { PasswordChangeModal } from "@/components/PasswordManagement";

interface UsageData {
  current_usage_inr: number;
  budget_limit_inr: number;
  remaining_budget_inr: number;
  percentage_used: number;
  recent_requests: any[];
  total_requests: number;
}

export default function AdminDashboard() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [usageData, setUsageData] = useState<UsageData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showPasswordModal, setShowPasswordModal] = useState(false);

  const API_BASE =
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  /* -------------------- helpers -------------------- */

  const encode = (u: string, p: string) => btoa(`${u}:${p}`);
  const setCookie = (v: string) =>
    (document.cookie = `admin_auth=${v}; path=/`);
  const clearCookie = () =>
    (document.cookie = "admin_auth=; path=/; max-age=0");

  const getCookie = () => {
    const match = document.cookie
      .split("; ")
      .find((c) => c.startsWith("admin_auth="));
    return match?.split("=")[1] || null;
  };

  const authHeader = (v: string) => ({
    Authorization: `Basic ${v}`,
  });

  /* -------------------- login -------------------- */

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    const encoded = encode(username, password);

    try {
      const res = await fetch(`${API_BASE}/admin/dashboard`, {
        headers: authHeader(encoded),
      });

      if (!res.ok) {
        setError("Invalid admin credentials");
        return;
      }

      const data = await res.json();
      setCookie(encoded);
      setUsageData(data);
      setIsAuthenticated(true);
    } catch {
      setError("Backend not reachable");
    } finally {
      setLoading(false);
    }
  };

  /* -------------------- load -------------------- */

  const loadDashboard = async () => {
    const encoded = getCookie();
    if (!encoded) return;

    const res = await fetch(`${API_BASE}/admin/dashboard`, {
      headers: authHeader(encoded),
    });

    if (!res.ok) {
      clearCookie();
      return;
    }

    const data = await res.json();
    setUsageData(data);
    setIsAuthenticated(true);
  };

  /* -------------------- reset -------------------- */

  const resetUsage = async () => {
    if (!confirm("Reset usage? This cannot be undone.")) return;

    const encoded = getCookie();
    if (!encoded) return;

    await fetch(`${API_BASE}/admin/reset-usage`, {
      method: "POST",
      headers: authHeader(encoded),
    });

    loadDashboard();
  };

  /* -------------------- logout -------------------- */

  const logout = () => {
    clearCookie();
    setIsAuthenticated(false);
    setUsageData(null);
    setUsername("");
    setPassword("");
  };

  /* -------------------- password change success -------------------- */

  const handlePasswordChangeSuccess = () => {
    alert("Password changed successfully! Please login again.");
    logout();
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  /* -------------------- LOGIN SCREEN -------------------- */

  if (!isAuthenticated) {
    return (
      <main className="relative min-h-screen bg-gradient-to-br from-[#020617] to-black overflow-hidden flex items-center justify-center">
        
        {/* Background glow */}
        <div className="pointer-events-none absolute inset-0 flex justify-center">
          <div className="w-[720px] h-[720px] bg-cyan-500/20 blur-[150px] rounded-full -translate-y-1/3" />
        </div>

        <div className="relative w-full max-w-md mx-4">
          {/* Login Card */}
          <div className="rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm p-8 shadow-2xl">
            
            {/* Header */}
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-cyan-500/20 to-indigo-500/20 mb-4">
                <Shield className="w-8 h-8 text-cyan-400" />
              </div>
              <h1 className="text-2xl font-mono font-semibold text-white mb-2 tracking-tight">
                &lt; Admin Access /&gt;
              </h1>
              <p className="text-gray-400 text-sm">
                Secure authentication required
              </p>
            </div>

            {/* Login Form */}
            <form onSubmit={handleLogin} className="space-y-5">
              <div>
                <label className="block text-sm text-gray-400 mb-2">
                  Username
                </label>
                <input
                  placeholder="Enter username"
                  className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-3 text-white placeholder:text-gray-600 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">
                  Password
                </label>
                <input
                  placeholder="Enter password"
                  type="password"
                  className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-3 text-white placeholder:text-gray-600 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>

              {error && (
                <div className="rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3">
                  <p className="text-red-400 text-sm text-center">{error}</p>
                </div>
              )}

              <button
                disabled={loading}
                className="w-full py-3 rounded-lg bg-gradient-to-r from-indigo-600 to-cyan-600 text-white font-medium hover:from-indigo-500 hover:to-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed transition shadow-lg"
              >
                {loading ? "Authenticating..." : "Login to Dashboard"}
              </button>
            </form>

            {/* Footer */}
            <p className="text-center text-xs text-gray-500 mt-6">
              Protected access • Unauthorized use prohibited
            </p>
          </div>
        </div>
      </main>
    );
  }

  /* -------------------- DASHBOARD -------------------- */

  return (
    <main className="relative min-h-screen bg-gradient-to-br from-[#020617] to-black overflow-hidden">
      
      {/* Background glow */}
      <div className="pointer-events-none absolute inset-0 flex justify-center">
        <div className="w-[720px] h-[720px] bg-cyan-500/20 blur-[150px] rounded-full -translate-y-1/3" />
      </div>

      <div className="relative">
        {/* Header */}
        <header className="border-b border-white/10 backdrop-blur-sm bg-black/20">
          <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyan-500/20 to-indigo-500/20 flex items-center justify-center">
                <Shield className="w-5 h-5 text-cyan-400" />
              </div>
              <div>
                <h1 className="font-mono text-xl font-semibold text-white">
                  Admin Dashboard
                </h1>
                <p className="text-xs text-gray-500">System Overview</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowPasswordModal(true)}
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm text-cyan-400 bg-cyan-500/10 border border-cyan-500/20 hover:bg-cyan-500/20 transition"
              >
                <Lock className="w-4 h-4" />
                Change Password
              </button>
              <button
                onClick={logout}
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm text-red-400 bg-red-500/10 border border-red-500/20 hover:bg-red-500/20 transition"
              >
                <LogOut className="w-4 h-4" />
                Logout
              </button>
            </div>
          </div>
        </header>

        {usageData && (
          <div className="max-w-7xl mx-auto px-6 py-10 space-y-8">

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <StatCard
                icon={<TrendingUp className="w-5 h-5" />}
                label="Current Usage"
                value={`₹${usageData.current_usage_inr.toFixed(2)}`}
                color="cyan"
              />
              <StatCard
                icon={<Database className="w-5 h-5" />}
                label="Budget Limit"
                value={`₹${usageData.budget_limit_inr.toFixed(2)}`}
                color="indigo"
              />
              <StatCard
                icon={<Activity className="w-5 h-5" />}
                label="Remaining"
                value={`₹${usageData.remaining_budget_inr.toFixed(2)}`}
                color="green"
              />
              <StatCard
                icon={<RefreshCcw className="w-5 h-5" />}
                label="Total Requests"
                value={usageData.total_requests.toString()}
                color="purple"
              />
            </div>

            {/* Usage Percentage Bar */}
            <div className="rounded-xl bg-white/5 border border-white/10 p-6">
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-white font-medium">Budget Usage</h3>
                <span className="text-cyan-400 font-semibold">
                  {usageData.percentage_used.toFixed(1)}%
                </span>
              </div>
              <div className="w-full h-3 bg-black/50 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-cyan-500 to-indigo-600 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(usageData.percentage_used, 100)}%` }}
                />
              </div>
              <div className="flex justify-between mt-2 text-xs text-gray-500">
                <span>₹0</span>
                <span>₹{usageData.budget_limit_inr.toFixed(2)}</span>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap gap-4">
              <button
                onClick={loadDashboard}
                className="flex items-center gap-2 px-5 py-3 rounded-lg text-sm font-medium bg-cyan-600/20 text-cyan-400 border border-cyan-500/30 hover:bg-cyan-600/30 transition"
              >
                <RefreshCcw className="w-4 h-4" />
                Refresh Data
              </button>
              <button
                onClick={resetUsage}
                className="flex items-center gap-2 px-5 py-3 rounded-lg text-sm font-medium bg-red-600/20 text-red-400 border border-red-500/30 hover:bg-red-600/30 transition"
              >
                <Trash2 className="w-4 h-4" />
                Reset Usage
              </button>
            </div>

            {/* Recent Requests Table */}
            <div className="rounded-xl bg-white/5 border border-white/10 overflow-hidden">
              <div className="px-6 py-4 border-b border-white/10">
                <h2 className="text-white font-semibold text-lg">Recent Requests</h2>
                <p className="text-gray-400 text-sm mt-1">Latest API usage activity</p>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-white/5">
                    <tr>
                      <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                        Timestamp
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                        Operation
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                        Pages
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                        Cost (₹)
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/10">
                    {usageData.recent_requests.length > 0 ? (
                      usageData.recent_requests.map((r, i) => (
                        <tr key={i} className="hover:bg-white/5 transition">
                          <td className="px-6 py-4 text-sm text-gray-300">
                            {new Date(r.timestamp).toLocaleString()}
                          </td>
                          <td className="px-6 py-4">
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                              {r.details.operation}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-300">
                            {r.details.pages}
                          </td>
                          <td className="px-6 py-4 text-sm font-medium text-white">
                            ₹{r.cost_inr.toFixed(4)}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={4} className="px-6 py-12 text-center text-gray-500">
                          No recent requests found
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

          </div>
        )}
      </div>

      {/* Password Change Modal */}
      {showPasswordModal && (
        <PasswordChangeModal
          onClose={() => setShowPasswordModal(false)}
          onSuccess={handlePasswordChangeSuccess}
        />
      )}
    </main>
  );
}

/* -------------------- Components -------------------- */

type StatCardProps = {
  icon: React.ReactNode;
  label: string;
  value: string;
  color: "cyan" | "indigo" | "green" | "purple";
};

function StatCard({ icon, label, value, color }: StatCardProps) {
  const colorClasses = {
    cyan: "from-cyan-500/20 to-cyan-500/5 text-cyan-400 border-cyan-500/30",
    indigo: "from-indigo-500/20 to-indigo-500/5 text-indigo-400 border-indigo-500/30",
    green: "from-green-500/20 to-green-500/5 text-green-400 border-green-500/30",
    purple: "from-purple-500/20 to-purple-500/5 text-purple-400 border-purple-500/30",
  };

  return (
    <div className="rounded-xl bg-white/5 border border-white/10 p-6 hover:bg-white/10 transition group">
      <div className="flex items-start justify-between mb-4">
        <div className={`w-12 h-12 rounded-lg bg-gradient-to-br ${colorClasses[color].split(' ')[0]} ${colorClasses[color].split(' ')[1]} flex items-center justify-center ${colorClasses[color].split(' ')[2]} group-hover:scale-110 transition`}>
          {icon}
        </div>
      </div>
      <p className="text-xs text-gray-400 mb-1 uppercase tracking-wider">{label}</p>
      <p className="text-2xl font-bold text-white">{value}</p>
    </div>
  );
}