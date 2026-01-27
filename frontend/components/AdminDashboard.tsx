"use client";

import React, { useEffect, useState } from "react";
import {
  Shield,
  LogOut,
  RefreshCcw,
  Trash2,
  TrendingUp,
  Activity,
  Database,
  Lock,
  DollarSign,
  BarChart3,
  FileText,
  X,
} from "lucide-react";

/* ================= TYPES ================= */

interface UsageData {
  current_usage_inr: number;
  budget_limit_inr: number;
  remaining_budget_inr: number;
  percentage_used: number;
  recent_requests: any[];
  total_requests: number;
}

/* ================= COMPONENT ================= */

// Use your Render backend URL in production
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://pdf-translator-ai.onrender.com";

export default function AdminDashboard() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [usageData, setUsageData] = useState<UsageData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showPasswordModal, setShowPasswordModal] = useState(false);

  /* ================= AUTH HELPERS ================= */

  const encode = (u: string, p: string) => btoa(`${u}:${p}`);

  const setAuth = (v: string) =>
    (document.cookie = `admin_auth=${v}; path=/`);

  const clearAuth = () =>
    (document.cookie = "admin_auth=; path=/; max-age=0");

  const getAuth = () => {
    const c = document.cookie
      .split("; ")
      .find((x) => x.startsWith("admin_auth="));
    return c?.split("=")[1] || null;
  };

  const authHeaders = (v: string) => ({
    "X-Admin-Auth": v,
  });

  /* ================= LOGIN ================= */

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const encoded = encode(username, password);

      const res = await fetch(`${API_BASE}/admin/dashboard`, {
        method: "GET",
        headers: authHeaders(encoded),
      });

      if (!res.ok) {
        throw new Error("Invalid admin credentials");
      }

      setAuth(encoded);
      const data = await res.json();
      setUsageData(data);
      setIsAuthenticated(true);
    } catch (err: any) {
      setError(err.message || "Login failed");
      clearAuth();
    } finally {
      setLoading(false);
    }
  };

  /* ================= LOAD DASHBOARD ================= */

  const loadDashboard = async () => {
    const encoded = getAuth();
    if (!encoded) return;

    const res = await fetch(`${API_BASE}/admin/dashboard`, {
      headers: authHeaders(encoded),
    });

    if (!res.ok) {
      clearAuth();
      setIsAuthenticated(false);
      return;
    }

    const data = await res.json();
    setUsageData(data);
    setIsAuthenticated(true);
  };

  /* ================= RESET ================= */

  const resetUsage = async () => {
    if (!confirm("Are you sure you want to reset all usage data?")) return;
    const encoded = getAuth();
    if (!encoded) return;

    setLoading(true);
    try {
      await fetch(`${API_BASE}/admin/reset-usage`, {
        method: "POST",
        headers: authHeaders(encoded),
      });
      await loadDashboard();
    } finally {
      setLoading(false);
    }
  };

  /* ================= LOGOUT ================= */

  const logout = () => {
    clearAuth();
    setIsAuthenticated(false);
    setUsageData(null);
    setUsername("");
    setPassword("");
  };

  /* ================= EFFECT ================= */

  useEffect(() => {
    loadDashboard();
  }, []);

  /* ================= LOGIN SCREEN ================= */

  if (!isAuthenticated) {
    return (
      <main className="relative min-h-screen bg-gradient-to-br from-[#020617] to-black overflow-hidden flex items-center justify-center">
        {/* Background glow effect */}
        <div className="pointer-events-none absolute inset-0 flex justify-center">
          <div className="w-[720px] h-[720px] bg-cyan-500/20 blur-[150px] rounded-full -translate-y-1/3" />
        </div>

        <div className="relative w-full max-w-md px-6">
          <form
            onSubmit={handleLogin}
            className="rounded-2xl bg-white/5 border border-white/10 p-8 space-y-6 backdrop-blur-sm"
          >
            {/* Header */}
            <div className="text-center space-y-4">
              <div className="w-16 h-16 mx-auto rounded-full bg-gradient-to-br from-cyan-500 to-indigo-600 flex items-center justify-center shadow-lg">
                <Shield className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">Admin Portal</h1>
                <p className="text-sm text-gray-400 mt-1">
                  Secure dashboard access
                </p>
              </div>
            </div>

            {/* Inputs */}
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-300 mb-2">
                  Username
                </label>
                <input
                  placeholder="Enter your username"
                  className="w-full px-4 py-3 rounded-lg bg-black/50 border border-white/10 text-white placeholder:text-gray-500 focus:border-cyan-500/50 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 transition"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
              </div>

              <div>
                <label className="block text-sm text-gray-300 mb-2">
                  Password
                </label>
                <input
                  placeholder="Enter your password"
                  type="password"
                  className="w-full px-4 py-3 rounded-lg bg-black/50 border border-white/10 text-white placeholder:text-gray-500 focus:border-cyan-500/50 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 transition"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                {error}
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full px-6 py-3 rounded-lg text-white font-medium
                bg-gradient-to-r from-indigo-600 to-cyan-600
                hover:from-indigo-500 hover:to-cyan-500
                disabled:opacity-50 disabled:cursor-not-allowed
                transition shadow-lg"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <RefreshCcw className="w-4 h-4 animate-spin" />
                  Authenticating...
                </span>
              ) : (
                "Login to Dashboard"
              )}
            </button>
          </form>

          {/* Footer */}
          <p className="text-center text-xs text-gray-500 mt-6">
            Protected admin access • Secure authentication required
          </p>
        </div>
      </main>
    );
  }

  /* ================= DASHBOARD ================= */

  return (
    <main className="relative min-h-screen bg-gradient-to-br from-[#020617] to-black overflow-hidden">
      {/* Background glow */}
      <div className="pointer-events-none absolute inset-0 flex justify-center">
        <div className="w-[720px] h-[720px] bg-cyan-500/20 blur-[150px] rounded-full -translate-y-1/3" />
      </div>

      <div className="relative max-w-7xl mx-auto px-6 py-8">
        {/* Header */}
        <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-cyan-500/20 to-indigo-500/20 flex items-center justify-center text-cyan-400">
              <Shield className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Admin Dashboard</h1>
              <p className="text-sm text-gray-400">System monitoring & management</p>
            </div>
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => setShowPasswordModal(true)}
              className="px-4 py-2 rounded-lg border border-white/10 text-gray-300 hover:bg-white/5 hover:border-cyan-500/30 transition flex items-center gap-2"
            >
              <Lock size={16} />
              Change Password
            </button>
            <button
              onClick={logout}
              className="px-4 py-2 rounded-lg border border-red-500/30 text-red-400 hover:bg-red-500/10 transition flex items-center gap-2"
            >
              <LogOut size={16} />
              Logout
            </button>
          </div>
        </header>

        {usageData && (
          <>
            {/* Stats Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <StatCard
                icon={<DollarSign className="w-6 h-6" />}
                label="Current Usage"
                value={`₹${usageData.current_usage_inr.toFixed(2)}`}
                gradient="from-cyan-500/20 to-indigo-500/20"
                iconColor="text-cyan-400"
              />
              <StatCard
                icon={<BarChart3 className="w-6 h-6" />}
                label="Budget Limit"
                value={`₹${usageData.budget_limit_inr.toFixed(2)}`}
                gradient="from-indigo-500/20 to-purple-500/20"
                iconColor="text-indigo-400"
              />
              <StatCard
                icon={<TrendingUp className="w-6 h-6" />}
                label="Remaining Budget"
                value={`₹${usageData.remaining_budget_inr.toFixed(2)}`}
                gradient="from-green-500/20 to-emerald-500/20"
                iconColor="text-green-400"
              />
              <StatCard
                icon={<Activity className="w-6 h-6" />}
                label="Total Requests"
                value={usageData.total_requests.toString()}
                gradient="from-purple-500/20 to-pink-500/20"
                iconColor="text-purple-400"
              />
            </div>

            {/* Usage Progress Bar */}
            <div className="mb-8 rounded-xl bg-white/5 border border-white/10 p-6">
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-white font-semibold">Budget Usage</h3>
                <span className="text-sm text-gray-400">
                  {usageData.percentage_used.toFixed(1)}% used
                </span>
              </div>
              <div className="w-full h-3 bg-black/50 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-cyan-500 to-indigo-600 transition-all duration-500"
                  style={{ width: `${Math.min(usageData.percentage_used, 100)}%` }}
                />
              </div>
              <div className="flex justify-between mt-2 text-xs text-gray-500">
                <span>₹0</span>
                <span>₹{usageData.budget_limit_inr.toFixed(2)}</span>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap gap-3 mb-8">
              <button
                onClick={loadDashboard}
                disabled={loading}
                className="px-6 py-3 rounded-lg border border-white/10 text-gray-300 hover:bg-white/5 hover:border-cyan-500/30 transition flex items-center gap-2 disabled:opacity-50"
              >
                <RefreshCcw size={16} className={loading ? "animate-spin" : ""} />
                Refresh Data
              </button>
              <button
                onClick={resetUsage}
                disabled={loading}
                className="px-6 py-3 rounded-lg border border-red-500/30 text-red-400 hover:bg-red-500/10 transition flex items-center gap-2 disabled:opacity-50"
              >
                <Trash2 size={16} />
                Reset Usage
              </button>
            </div>

            {/* Recent Requests */}
            {usageData.recent_requests && usageData.recent_requests.length > 0 && (
              <div className="rounded-xl bg-white/5 border border-white/10 p-6">
                <div className="flex items-center gap-2 mb-4">
                  <FileText className="w-5 h-5 text-cyan-400" />
                  <h3 className="text-white font-semibold">Recent Activity</h3>
                </div>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {usageData.recent_requests.slice(0, 10).map((request, idx) => (
                    <div
                      key={idx}
                      className="px-4 py-3 rounded-lg bg-black/30 border border-white/5 text-sm text-gray-300"
                    >
                      Request #{idx + 1}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        {/* Password Change Modal */}
        {showPasswordModal && (
          <PasswordChangeModal
            onClose={() => setShowPasswordModal(false)}
            onSuccess={logout}
            authHeaders={authHeaders}
            getAuth={getAuth}
          />
        )}
      </div>
    </main>
  );
}

/* ================= STAT CARD COMPONENT ================= */

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  gradient: string;
  iconColor: string;
}

function StatCard({ icon, label, value, gradient, iconColor }: StatCardProps) {
  return (
    <div className="group rounded-xl bg-white/5 border border-white/10 p-6 hover:bg-white/10 hover:border-cyan-500/30 transition">
      <div className="flex items-start justify-between mb-4">
        <div className={`w-12 h-12 rounded-lg bg-gradient-to-br ${gradient} flex items-center justify-center ${iconColor} group-hover:scale-110 transition`}>
          {icon}
        </div>
      </div>
      <p className="text-gray-400 text-sm mb-1">{label}</p>
      <p className="text-2xl font-bold text-white">{value}</p>
    </div>
  );
}

/* ================= PASSWORD CHANGE MODAL ================= */

interface PasswordChangeModalProps {
  onClose: () => void;
  onSuccess: () => void;
  authHeaders: (v: string) => any;
  getAuth: () => string | null;
}

function PasswordChangeModal({ onClose, onSuccess, authHeaders, getAuth }: PasswordChangeModalProps) {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (newPassword !== confirmPassword) {
      setError("New passwords do not match");
      return;
    }

    if (newPassword.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }

    setLoading(true);

    try {
      const encoded = getAuth();
      if (!encoded) {
        throw new Error("Not authenticated");
      }

      const res = await fetch(`${API_BASE}/admin/change-password`, {
        method: "POST",
        headers: {
          ...authHeaders(encoded),
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to change password");
      }

      setSuccess(true);
      setTimeout(() => {
        onSuccess();
      }, 1500);
    } catch (err: any) {
      setError(err.message || "Failed to change password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="relative w-full max-w-md rounded-2xl bg-gradient-to-br from-[#020617] to-black border border-white/10 p-6">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-white transition"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="mb-6">
          <div className="w-12 h-12 mx-auto mb-3 rounded-lg bg-gradient-to-br from-cyan-500/20 to-indigo-500/20 flex items-center justify-center text-cyan-400">
            <Lock className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold text-white text-center">Change Password</h2>
          <p className="text-sm text-gray-400 text-center mt-1">Update your admin password</p>
        </div>

        {success ? (
          <div className="text-center py-8">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-green-500/20 flex items-center justify-center">
              <svg className="w-8 h-8 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <p className="text-white font-medium">Password changed successfully!</p>
            <p className="text-sm text-gray-400 mt-2">Logging you out...</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-gray-300 mb-2">Current Password</label>
              <input
                type="password"
                className="w-full px-4 py-3 rounded-lg bg-black/50 border border-white/10 text-white placeholder:text-gray-500 focus:border-cyan-500/50 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 transition"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
              />
            </div>

            <div>
              <label className="block text-sm text-gray-300 mb-2">New Password</label>
              <input
                type="password"
                className="w-full px-4 py-3 rounded-lg bg-black/50 border border-white/10 text-white placeholder:text-gray-500 focus:border-cyan-500/50 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 transition"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
              />
            </div>

            <div>
              <label className="block text-sm text-gray-300 mb-2">Confirm New Password</label>
              <input
                type="password"
                className="w-full px-4 py-3 rounded-lg bg-black/50 border border-white/10 text-white placeholder:text-gray-500 focus:border-cyan-500/50 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 transition"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />
            </div>

            {error && (
              <div className="px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                {error}
              </div>
            )}

            <div className="flex gap-3 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 px-4 py-3 rounded-lg border border-white/10 text-gray-300 hover:bg-white/5 transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 px-4 py-3 rounded-lg bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white font-medium disabled:opacity-50 transition"
              >
                {loading ? "Updating..." : "Update Password"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}