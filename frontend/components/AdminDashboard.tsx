"use client";

import React, { useEffect, useState, useMemo } from "react";
import {
  Shield,
  LogOut,
  RefreshCcw,
  Trash2,
  TrendingUp,
  Activity,
  DollarSign,
  BarChart3,
  FileText,
  X,
  Lock,
  CreditCard,
  Users,
  CheckCircle,
  XCircle,
  Clock,
  Calendar,
  TrendingDown,
  Download,
  Search,
  Filter,
  Eye,
  AlertCircle,
  Zap,
  Package,
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "https://pdf-translator-ai-ggqe.onrender.com";

/* ================= TYPES ================= */

interface PaymentStats {
  total_orders: number;
  verified_payments: number;
  failed_payments: number;
  pending_payments: number;
  total_revenue_inr: number;
}

interface SessionStats {
  total_sessions: number;
  active_sessions_24h: number;
  total_free_pages_used: number;
  free_pages_limit: number;
}

interface UsageData {
  current_usage_inr: number;
  budget_limit_inr: number;
  remaining_budget_inr: number;
  percentage_used: number;
  recent_requests: any[];
  total_requests: number;
}

interface RecentPayment {
  order_id: string;
  job_id: string;
  amount_inr: number;
  page_count: number;
  status: string;
  created_at: string;
  demo: boolean;
  session_id?: string;
  payment_id?: string;
}

interface Session {
  session_id: string;
  created_at: string;
  last_activity: string;
  free_pages_used: number;
  total_jobs: number;
  total_payments: number;
}

interface DashboardData {
  usage: UsageData;
  payments: PaymentStats;
  sessions: SessionStats;
  recent_payments: RecentPayment[];
  recent_requests: any[];
}

/* ================= COMPONENT ================= */


export default function AdminDashboard() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [detailedPayments, setDetailedPayments] = useState<RecentPayment[]>([]);
  const [detailedSessions, setDetailedSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [showSessionModal, setShowSessionModal] = useState(false);
  const [selectedSession, setSelectedSession] = useState<Session | null>(null);
  const [activeTab, setActiveTab] = useState<"overview" | "payments" | "sessions">("overview");
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  
  // Filters
  const [paymentFilter, setPaymentFilter] = useState("");
  const [paymentStatusFilter, setPaymentStatusFilter] = useState<string>("all");
  const [sessionFilter, setSessionFilter] = useState("");
  const [dateRange, setDateRange] = useState<"24h" | "7d" | "30d" | "all">("all");

  /* ================= AUTH HELPERS ================= */

  const encode = (u: string, p: string) => btoa(`${u}:${p}`);
  const setAuth = (v: string) => (document.cookie = `admin_auth=${v}; path=/`);
  const clearAuth = () => (document.cookie = "admin_auth=; path=/; max-age=0");
  const getAuth = () => {
    const c = document.cookie.split("; ").find((x) => x.startsWith("admin_auth="));
    return c?.split("=")[1] || null;
  };
  const authHeaders = (v: string) => ({ "X-Admin-Auth": v });

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

      if (!res.ok) throw new Error("Invalid admin credentials");

      setAuth(encoded);
      const data = await res.json();
      setDashboardData(data);
      setIsAuthenticated(true);
      setLastRefresh(new Date());
      
      // Load detailed data
      await loadDetailedData(encoded);
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

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/admin/dashboard`, {
        headers: authHeaders(encoded),
      });

      if (!res.ok) {
        clearAuth();
        setIsAuthenticated(false);
        return;
      }

      const data = await res.json();
      setDashboardData(data);
      setIsAuthenticated(true);
      setLastRefresh(new Date());
      
      // Load detailed data in background
      await loadDetailedData(encoded);
    } catch (err) {
      console.error("Failed to load dashboard:", err);
    } finally {
      setLoading(false);
    }
  };

  /* ================= LOAD DETAILED DATA ================= */

  const loadDetailedData = async (encoded: string) => {
    try {
      // Load detailed payments
      const paymentsRes = await fetch(`${API_BASE}/admin/payments?limit=100`, {
        headers: authHeaders(encoded),
      });
      if (paymentsRes.ok) {
        const paymentsData = await paymentsRes.json();
        setDetailedPayments(paymentsData.payments || []);
      }

      // Load detailed sessions
      const sessionsRes = await fetch(`${API_BASE}/admin/sessions`, {
        headers: authHeaders(encoded),
      });
      if (sessionsRes.ok) {
        const sessionsData = await sessionsRes.json();
        setDetailedSessions(sessionsData.sessions || []);
      }
    } catch (err) {
      console.error("Failed to load detailed data:", err);
    }
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

  /* ================= EXPORT FUNCTIONS ================= */

  const exportToCSV = (data: any[], filename: string) => {
    if (data.length === 0) return;
    
    const headers = Object.keys(data[0]);
    const csvContent = [
      headers.join(","),
      ...data.map(row => headers.map(h => JSON.stringify(row[h] || "")).join(","))
    ].join("\n");
    
    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${filename}_${new Date().toISOString().split("T")[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportToJSON = (data: any, filename: string) => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${filename}_${new Date().toISOString().split("T")[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  /* ================= LOGOUT ================= */

  const logout = () => {
    clearAuth();
    setIsAuthenticated(false);
    setDashboardData(null);
    setUsername("");
    setPassword("");
    setAutoRefresh(false);
  };

  /* ================= FILTERED DATA ================= */

  const filteredPayments = useMemo(() => {
    let filtered = detailedPayments;

    // Status filter
    if (paymentStatusFilter !== "all") {
      filtered = filtered.filter(p => p.status === paymentStatusFilter);
    }

    // Search filter
    if (paymentFilter) {
      const search = paymentFilter.toLowerCase();
      filtered = filtered.filter(p =>
        p.order_id.toLowerCase().includes(search) ||
        p.job_id?.toLowerCase().includes(search) ||
        p.session_id?.toLowerCase().includes(search)
      );
    }

    // Date range filter
    if (dateRange !== "all") {
      const now = new Date();
      const cutoff = new Date();
      if (dateRange === "24h") cutoff.setHours(now.getHours() - 24);
      if (dateRange === "7d") cutoff.setDate(now.getDate() - 7);
      if (dateRange === "30d") cutoff.setDate(now.getDate() - 30);

      filtered = filtered.filter(p => {
        if (!p.created_at) return false;
        return new Date(p.created_at) >= cutoff;
      });
    }

    return filtered;
  }, [detailedPayments, paymentFilter, paymentStatusFilter, dateRange]);

  const filteredSessions = useMemo(() => {
    let filtered = detailedSessions;

    if (sessionFilter) {
      const search = sessionFilter.toLowerCase();
      filtered = filtered.filter(s =>
        s.session_id.toLowerCase().includes(search)
      );
    }

    return filtered;
  }, [detailedSessions, sessionFilter]);

  /* ================= ANALYTICS CALCULATIONS ================= */

  const analytics = useMemo(() => {
    if (!dashboardData) return null;

    const payments = filteredPayments;
    const avgPayment = payments.length > 0
      ? payments.reduce((sum, p) => sum + p.amount_inr, 0) / payments.length
      : 0;

    const avgPages = payments.length > 0
      ? payments.reduce((sum, p) => sum + p.page_count, 0) / payments.length
      : 0;

    const successRate = dashboardData.payments.total_orders > 0
      ? (dashboardData.payments.verified_payments / dashboardData.payments.total_orders) * 100
      : 0;

    return {
      avgPayment,
      avgPages,
      successRate,
      conversionRate: dashboardData.sessions.total_sessions > 0
        ? (dashboardData.payments.total_orders / dashboardData.sessions.total_sessions) * 100
        : 0,
    };
  }, [dashboardData, filteredPayments]);

  /* ================= AUTO REFRESH ================= */

  useEffect(() => {
    if (autoRefresh && isAuthenticated) {
      const interval = setInterval(loadDashboard, 30000); // 30 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh, isAuthenticated]);

  /* ================= EFFECT ================= */

  useEffect(() => {
    loadDashboard();
  }, []);

  /* ================= LOGIN SCREEN ================= */

  if (!isAuthenticated) {
    return (
      <main className="relative min-h-screen bg-gradient-to-br from-[#020617] to-black overflow-hidden flex items-center justify-center">
        <div className="pointer-events-none absolute inset-0 flex justify-center">
          <div className="w-[720px] h-[720px] bg-cyan-500/20 blur-[150px] rounded-full -translate-y-1/3" />
        </div>

        <div className="relative w-full max-w-md px-6">
          <form
            onSubmit={handleLogin}
            className="rounded-2xl bg-white/5 border border-white/10 p-8 space-y-6 backdrop-blur-sm"
          >
            <div className="text-center space-y-4">
              <div className="w-16 h-16 mx-auto rounded-full bg-gradient-to-br from-cyan-500 to-indigo-600 flex items-center justify-center shadow-lg">
                <Shield className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">Admin Portal</h1>
                <p className="text-sm text-gray-400 mt-1">Secure dashboard access</p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-300 mb-2">Username</label>
                <input
                  placeholder="Enter your username"
                  className="w-full px-4 py-3 rounded-lg bg-black/50 border border-white/10 text-white placeholder:text-gray-500 focus:border-cyan-500/50 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 transition"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
              </div>

              <div>
                <label className="block text-sm text-gray-300 mb-2">Password</label>
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

            {error && (
              <div className="px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full px-6 py-3 rounded-lg text-white font-medium bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed transition shadow-lg"
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
              <div className="flex items-center gap-2 text-sm text-gray-400">
                <span>System monitoring & analytics</span>
                {lastRefresh && (
                  <>
                    <span>•</span>
                    <span>Updated {new Date(lastRefresh).toLocaleTimeString()}</span>
                  </>
                )}
              </div>
            </div>
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`px-4 py-2 rounded-lg border transition flex items-center gap-2 ${
                autoRefresh
                  ? "border-cyan-500/50 bg-cyan-500/10 text-cyan-400"
                  : "border-white/10 text-gray-300 hover:bg-white/5"
              }`}
            >
              <Zap size={16} className={autoRefresh ? "animate-pulse" : ""} />
              Auto-refresh
            </button>
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

        {/* Tabs */}
        <div className="flex gap-2 mb-8 border-b border-white/10">
          <TabButton
            active={activeTab === "overview"}
            onClick={() => setActiveTab("overview")}
            icon={<BarChart3 className="w-4 h-4" />}
            label="Overview"
          />
          <TabButton
            active={activeTab === "payments"}
            onClick={() => setActiveTab("payments")}
            icon={<CreditCard className="w-4 h-4" />}
            label="Payments"
            badge={detailedPayments.length}
          />
          <TabButton
            active={activeTab === "sessions"}
            onClick={() => setActiveTab("sessions")}
            icon={<Users className="w-4 h-4" />}
            label="Sessions"
            badge={detailedSessions.length}
          />
        </div>

        {dashboardData && (
          <>
            {/* Overview Tab */}
            {activeTab === "overview" && (
              <div className="space-y-8">
                {/* Key Metrics */}
                {analytics && (
                  <div>
                    <h2 className="text-white font-semibold mb-4 flex items-center gap-2">
                      <Activity className="w-5 h-5 text-cyan-400" />
                      Key Metrics
                    </h2>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                      <StatCard
                        icon={<TrendingUp className="w-6 h-6" />}
                        label="Success Rate"
                        value={`${analytics.successRate.toFixed(1)}%`}
                        gradient="from-green-500/20 to-emerald-500/20"
                        iconColor="text-green-400"
                        trend={analytics.successRate > 80 ? "up" : analytics.successRate > 50 ? "neutral" : "down"}
                      />
                      <StatCard
                        icon={<DollarSign className="w-6 h-6" />}
                        label="Avg Payment"
                        value={`₹${analytics.avgPayment.toFixed(2)}`}
                        gradient="from-cyan-500/20 to-blue-500/20"
                        iconColor="text-cyan-400"
                      />
                      <StatCard
                        icon={<FileText className="w-6 h-6" />}
                        label="Avg Pages/Order"
                        value={analytics.avgPages.toFixed(1)}
                        gradient="from-purple-500/20 to-pink-500/20"
                        iconColor="text-purple-400"
                      />
                      <StatCard
                        icon={<Users className="w-6 h-6" />}
                        label="Conversion Rate"
                        value={`${analytics.conversionRate.toFixed(1)}%`}
                        gradient="from-indigo-500/20 to-purple-500/20"
                        iconColor="text-indigo-400"
                        trend={analytics.conversionRate > 10 ? "up" : analytics.conversionRate > 5 ? "neutral" : "down"}
                      />
                    </div>
                  </div>
                )}

                {/* Payment Stats Grid */}
                <div>
                  <h2 className="text-white font-semibold mb-4 flex items-center gap-2">
                    <CreditCard className="w-5 h-5 text-cyan-400" />
                    Payment Statistics
                  </h2>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    <StatCard
                      icon={<DollarSign className="w-6 h-6" />}
                      label="Total Revenue"
                      value={`₹${dashboardData.payments.total_revenue_inr.toFixed(2)}`}
                      gradient="from-green-500/20 to-emerald-500/20"
                      iconColor="text-green-400"
                    />
                    <StatCard
                      icon={<CheckCircle className="w-6 h-6" />}
                      label="Verified Payments"
                      value={dashboardData.payments.verified_payments.toString()}
                      gradient="from-cyan-500/20 to-blue-500/20"
                      iconColor="text-cyan-400"
                    />
                    <StatCard
                      icon={<Clock className="w-6 h-6" />}
                      label="Pending Payments"
                      value={dashboardData.payments.pending_payments.toString()}
                      gradient="from-yellow-500/20 to-orange-500/20"
                      iconColor="text-yellow-400"
                    />
                    <StatCard
                      icon={<XCircle className="w-6 h-6" />}
                      label="Failed Payments"
                      value={dashboardData.payments.failed_payments.toString()}
                      gradient="from-red-500/20 to-pink-500/20"
                      iconColor="text-red-400"
                    />
                  </div>
                </div>

                {/* Session Stats Grid */}
                <div>
                  <h2 className="text-white font-semibold mb-4 flex items-center gap-2">
                    <Users className="w-5 h-5 text-indigo-400" />
                    User Sessions
                  </h2>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    <StatCard
                      icon={<Users className="w-6 h-6" />}
                      label="Total Sessions"
                      value={dashboardData.sessions.total_sessions.toString()}
                      gradient="from-indigo-500/20 to-purple-500/20"
                      iconColor="text-indigo-400"
                    />
                    <StatCard
                      icon={<Activity className="w-6 h-6" />}
                      label="Active (24h)"
                      value={dashboardData.sessions.active_sessions_24h.toString()}
                      gradient="from-purple-500/20 to-pink-500/20"
                      iconColor="text-purple-400"
                    />
                    <StatCard
                      icon={<FileText className="w-6 h-6" />}
                      label="Free Pages Used"
                      value={dashboardData.sessions.total_free_pages_used.toString()}
                      gradient="from-cyan-500/20 to-teal-500/20"
                      iconColor="text-cyan-400"
                    />
                    <StatCard
                      icon={<TrendingUp className="w-6 h-6" />}
                      label="Free Page Limit"
                      value={dashboardData.sessions.free_pages_limit.toString()}
                      gradient="from-teal-500/20 to-green-500/20"
                      iconColor="text-teal-400"
                    />
                  </div>
                </div>

                {/* API Usage Stats */}
                <div>
                  <h2 className="text-white font-semibold mb-4 flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-cyan-400" />
                    API Usage
                  </h2>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    <StatCard
                      icon={<DollarSign className="w-6 h-6" />}
                      label="Current Usage"
                      value={`₹${dashboardData.usage.current_usage_inr.toFixed(2)}`}
                      gradient="from-cyan-500/20 to-indigo-500/20"
                      iconColor="text-cyan-400"
                    />
                    <StatCard
                      icon={<BarChart3 className="w-6 h-6" />}
                      label="Budget Limit"
                      value={`₹${dashboardData.usage.budget_limit_inr.toFixed(2)}`}
                      gradient="from-indigo-500/20 to-purple-500/20"
                      iconColor="text-indigo-400"
                    />
                    <StatCard
                      icon={<TrendingDown className="w-6 h-6" />}
                      label="Remaining Budget"
                      value={`₹${dashboardData.usage.remaining_budget_inr.toFixed(2)}`}
                      gradient="from-green-500/20 to-emerald-500/20"
                      iconColor="text-green-400"
                    />
                    <StatCard
                      icon={<Activity className="w-6 h-6" />}
                      label="Total Requests"
                      value={dashboardData.usage.total_requests.toString()}
                      gradient="from-purple-500/20 to-pink-500/20"
                      iconColor="text-purple-400"
                    />
                  </div>
                </div>

                {/* Budget Usage Bar */}
                <div className="rounded-xl bg-white/5 border border-white/10 p-6">
                  <div className="flex justify-between items-center mb-3">
                    <h3 className="text-white font-semibold">Budget Usage</h3>
                    <span className="text-sm text-gray-400">
                      {dashboardData.usage.percentage_used.toFixed(1)}% used
                    </span>
                  </div>
                  <div className="w-full h-3 bg-black/50 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all duration-500 ${
                        dashboardData.usage.percentage_used > 90
                          ? "bg-gradient-to-r from-red-500 to-orange-500"
                          : dashboardData.usage.percentage_used > 70
                          ? "bg-gradient-to-r from-yellow-500 to-orange-500"
                          : "bg-gradient-to-r from-cyan-500 to-indigo-600"
                      }`}
                      style={{
                        width: `${Math.min(dashboardData.usage.percentage_used, 100)}%`,
                      }}
                    />
                  </div>
                  {dashboardData.usage.percentage_used > 80 && (
                    <div className="mt-3 flex items-center gap-2 text-yellow-400 text-sm">
                      <AlertCircle className="w-4 h-4" />
                      <span>Budget limit approaching - consider increasing limits</span>
                    </div>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="flex flex-wrap gap-3">
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
                  <button
                    onClick={() => exportToJSON(dashboardData, "dashboard_data")}
                    className="px-6 py-3 rounded-lg border border-white/10 text-gray-300 hover:bg-white/5 hover:border-cyan-500/30 transition flex items-center gap-2"
                  >
                    <Download size={16} />
                    Export Dashboard
                  </button>
                </div>
              </div>
            )}

            {/* Payments Tab */}
            {activeTab === "payments" && (
              <div className="space-y-6">
                {/* Filters */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                    <input
                      type="text"
                      placeholder="Search orders..."
                      value={paymentFilter}
                      onChange={(e) => setPaymentFilter(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 rounded-lg bg-white/5 border border-white/10 text-white placeholder:text-gray-500 focus:border-cyan-500/50 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 transition"
                    />
                  </div>
                  
                  <select
                    value={paymentStatusFilter}
                    onChange={(e) => setPaymentStatusFilter(e.target.value)}
                    className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-white focus:border-cyan-500/50 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 transition"
                  >
                    <option value="all">All Statuses</option>
                    <option value="verified">Verified</option>
                    <option value="captured">Captured</option>
                    <option value="pending">Pending</option>
                    <option value="created">Created</option>
                    <option value="failed">Failed</option>
                  </select>

                  <select
                    value={dateRange}
                    onChange={(e) => setDateRange(e.target.value as any)}
                    className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-white focus:border-cyan-500/50 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 transition"
                  >
                    <option value="all">All Time</option>
                    <option value="24h">Last 24 Hours</option>
                    <option value="7d">Last 7 Days</option>
                    <option value="30d">Last 30 Days</option>
                  </select>

                  <button
                    onClick={() => exportToCSV(filteredPayments, "payments")}
                    className="px-4 py-2 rounded-lg border border-white/10 text-gray-300 hover:bg-white/5 hover:border-cyan-500/30 transition flex items-center justify-center gap-2"
                  >
                    <Download size={16} />
                    Export CSV
                  </button>
                </div>

                {/* Payments Table */}
                <div className="rounded-xl bg-white/5 border border-white/10 overflow-hidden">
                  <div className="p-6 border-b border-white/10 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <CreditCard className="w-5 h-5 text-cyan-400" />
                      <h3 className="text-white font-semibold">Payment Transactions</h3>
                    </div>
                    <span className="text-sm text-gray-400">
                      {filteredPayments.length} of {detailedPayments.length} transactions
                    </span>
                  </div>
                  
                  {filteredPayments.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-black/30">
                          <tr className="text-left text-sm text-gray-400">
                            <th className="px-6 py-3 font-medium">Order ID</th>
                            <th className="px-6 py-3 font-medium">Job ID</th>
                            <th className="px-6 py-3 font-medium">Amount</th>
                            <th className="px-6 py-3 font-medium">Pages</th>
                            <th className="px-6 py-3 font-medium">Status</th>
                            <th className="px-6 py-3 font-medium">Created</th>
                            <th className="px-6 py-3 font-medium">Type</th>
                          </tr>
                        </thead>
                        <tbody>
                          {filteredPayments.map((payment, idx) => (
                            <tr
                              key={idx}
                              className="border-t border-white/5 hover:bg-white/5 transition"
                            >
                              <td className="px-6 py-4">
                                <span className="text-sm font-mono text-gray-300">
                                  {payment.order_id.slice(0, 12)}...
                                </span>
                              </td>
                              <td className="px-6 py-4">
                                <span className="text-sm font-mono text-gray-400">
                                  {payment.job_id?.slice(0, 8)}...
                                </span>
                              </td>
                              <td className="px-6 py-4">
                                <span className="text-white font-semibold">
                                  ₹{payment.amount_inr.toFixed(2)}
                                </span>
                              </td>
                              <td className="px-6 py-4">
                                <span className="text-gray-300">{payment.page_count}</span>
                              </td>
                              <td className="px-6 py-4">
                                <StatusBadge status={payment.status} />
                              </td>
                              <td className="px-6 py-4">
                                <span className="text-sm text-gray-400">
                                  {payment.created_at
                                    ? new Date(payment.created_at).toLocaleDateString()
                                    : "N/A"}
                                </span>
                              </td>
                              <td className="px-6 py-4">
                                {payment.demo && (
                                  <span className="px-2 py-1 text-xs rounded bg-yellow-500/20 text-yellow-400 border border-yellow-500/30">
                                    DEMO
                                  </span>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="text-center text-gray-500 py-12">
                      No transactions match your filters
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Sessions Tab */}
            {activeTab === "sessions" && (
              <div className="space-y-6">
                {/* Filters */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                    <input
                      type="text"
                      placeholder="Search sessions..."
                      value={sessionFilter}
                      onChange={(e) => setSessionFilter(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 rounded-lg bg-white/5 border border-white/10 text-white placeholder:text-gray-500 focus:border-cyan-500/50 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 transition"
                    />
                  </div>

                  <button
                    onClick={() => exportToCSV(filteredSessions, "sessions")}
                    className="px-4 py-2 rounded-lg border border-white/10 text-gray-300 hover:bg-white/5 hover:border-cyan-500/30 transition flex items-center justify-center gap-2"
                  >
                    <Download size={16} />
                    Export CSV
                  </button>
                </div>

                {/* Sessions Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {filteredSessions.map((session, idx) => (
                    <div
                      key={idx}
                      className="rounded-xl bg-white/5 border border-white/10 p-6 hover:bg-white/10 hover:border-cyan-500/30 transition cursor-pointer"
                      onClick={() => {
                        setSelectedSession(session);
                        setShowSessionModal(true);
                      }}
                    >
                      <div className="flex items-start justify-between mb-4">
                        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-500/20 to-purple-500/20 flex items-center justify-center text-indigo-400">
                          <Users className="w-5 h-5" />
                        </div>
                        <Eye className="w-4 h-4 text-gray-400" />
                      </div>
                      
                      <h4 className="text-white font-mono text-sm mb-2 truncate">
                        {session.session_id}
                      </h4>
                      
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-400">Free Pages:</span>
                          <span className="text-cyan-400 font-semibold">
                            {session.free_pages_used}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">Jobs:</span>
                          <span className="text-white">{session.total_jobs}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">Payments:</span>
                          <span className="text-green-400">{session.total_payments}</span>
                        </div>
                      </div>

                      <div className="mt-4 pt-4 border-t border-white/10">
                        <div className="flex items-center gap-2 text-xs text-gray-500">
                          <Clock className="w-3 h-3" />
                          <span>
                            {session.last_activity
                              ? new Date(session.last_activity).toLocaleString()
                              : "Never"}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {filteredSessions.length === 0 && (
                  <div className="rounded-xl bg-white/5 border border-white/10 p-12 text-center">
                    <Users className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                    <p className="text-gray-500">No sessions match your filters</p>
                  </div>
                )}
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

        {/* Session Detail Modal */}
        {showSessionModal && selectedSession && (
          <SessionDetailModal
            session={selectedSession}
            onClose={() => {
              setShowSessionModal(false);
              setSelectedSession(null);
            }}
          />
        )}
      </div>
    </main>
  );
}

/* ================= TAB BUTTON ================= */

interface TabButtonProps {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
  badge?: number;
}

function TabButton({ active, onClick, icon, label, badge }: TabButtonProps) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-3 flex items-center gap-2 border-b-2 transition ${
        active
          ? "border-cyan-500 text-cyan-400"
          : "border-transparent text-gray-400 hover:text-gray-300"
      }`}
    >
      {icon}
      <span className="font-medium">{label}</span>
      {badge !== undefined && badge > 0 && (
        <span className="ml-1 px-2 py-0.5 text-xs rounded-full bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
          {badge}
        </span>
      )}
    </button>
  );
}

/* ================= STATUS BADGE ================= */

function StatusBadge({ status }: { status: string }) {
  const colors = {
    verified: "bg-green-500/20 text-green-400 border-green-500/30",
    captured: "bg-green-500/20 text-green-400 border-green-500/30",
    created: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
    pending: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
    failed: "bg-red-500/20 text-red-400 border-red-500/30",
  };

  return (
    <span
      className={`inline-block px-2 py-0.5 text-xs rounded border ${
        colors[status as keyof typeof colors] || "bg-gray-500/20 text-gray-400 border-gray-500/30"
      }`}
    >
      {status}
    </span>
  );
}

/* ================= STAT CARD ================= */

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  gradient: string;
  iconColor: string;
  trend?: "up" | "down" | "neutral";
}

function StatCard({ icon, label, value, gradient, iconColor, trend }: StatCardProps) {
  return (
    <div className="group rounded-xl bg-white/5 border border-white/10 p-6 hover:bg-white/10 hover:border-cyan-500/30 transition">
      <div className="flex items-start justify-between mb-4">
        <div
          className={`w-12 h-12 rounded-lg bg-gradient-to-br ${gradient} flex items-center justify-center ${iconColor} group-hover:scale-110 transition`}
        >
          {icon}
        </div>
        {trend && (
          <div className={`flex items-center gap-1 text-xs ${
            trend === "up" ? "text-green-400" : trend === "down" ? "text-red-400" : "text-gray-400"
          }`}>
            {trend === "up" && <TrendingUp className="w-4 h-4" />}
            {trend === "down" && <TrendingDown className="w-4 h-4" />}
          </div>
        )}
      </div>
      <p className="text-gray-400 text-sm mb-1">{label}</p>
      <p className="text-2xl font-bold text-white">{value}</p>
    </div>
  );
}

/* ================= SESSION DETAIL MODAL ================= */

function SessionDetailModal({ session, onClose }: { session: Session; onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="relative w-full max-w-2xl rounded-2xl bg-gradient-to-br from-[#020617] to-black border border-white/10 p-6 max-h-[90vh] overflow-y-auto">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-white transition"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="mb-6">
          <div className="w-12 h-12 mx-auto mb-3 rounded-lg bg-gradient-to-br from-indigo-500/20 to-purple-500/20 flex items-center justify-center text-indigo-400">
            <Users className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold text-white text-center">Session Details</h2>
          <p className="text-sm text-gray-400 text-center mt-1 font-mono">
            {session.session_id}
          </p>
        </div>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <InfoCard label="Total Jobs" value={session.total_jobs.toString()} icon={<Package className="w-4 h-4" />} />
            <InfoCard label="Total Payments" value={session.total_payments.toString()} icon={<CreditCard className="w-4 h-4" />} />
            <InfoCard label="Free Pages Used" value={session.free_pages_used.toString()} icon={<FileText className="w-4 h-4" />} />
            <InfoCard label="Created" value={new Date(session.created_at).toLocaleDateString()} icon={<Calendar className="w-4 h-4" />} />
          </div>

          <div className="rounded-lg bg-white/5 border border-white/10 p-4">
            <div className="flex items-center gap-2 text-sm text-gray-400 mb-2">
              <Clock className="w-4 h-4" />
              <span className="font-medium">Last Activity</span>
            </div>
            <p className="text-white">
              {session.last_activity
                ? new Date(session.last_activity).toLocaleString()
                : "Never"}
            </p>
          </div>
        </div>

        <button
          onClick={onClose}
          className="w-full mt-6 px-4 py-3 rounded-lg bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white font-medium transition"
        >
          Close
        </button>
      </div>
    </div>
  );
}

function InfoCard({ label, value, icon }: { label: string; value: string; icon: React.ReactNode }) {
  return (
    <div className="rounded-lg bg-white/5 border border-white/10 p-4">
      <div className="flex items-center gap-2 text-sm text-gray-400 mb-1">
        {icon}
        <span>{label}</span>
      </div>
      <p className="text-xl font-bold text-white">{value}</p>
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

function PasswordChangeModal({
  onClose,
  onSuccess,
  authHeaders,
  getAuth,
}: PasswordChangeModalProps) {
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
      if (!encoded) throw new Error("Not authenticated");

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
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-white transition"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="mb-6">
          <div className="w-12 h-12 mx-auto mb-3 rounded-lg bg-gradient-to-br from-cyan-500/20 to-indigo-500/20 flex items-center justify-center text-cyan-400">
            <Lock className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold text-white text-center">Change Password</h2>
          <p className="text-sm text-gray-400 text-center mt-1">
            Update your admin password
          </p>
        </div>

        {success ? (
          <div className="text-center py-8">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-green-500/20 flex items-center justify-center">
              <CheckCircle className="w-8 h-8 text-green-400" />
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
              <label className="block text-sm text-gray-300 mb-2">
                Confirm New Password
              </label>
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
