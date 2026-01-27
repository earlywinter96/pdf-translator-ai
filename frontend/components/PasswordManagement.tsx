"use client";

import { useState } from "react";
import { Lock, Eye, EyeOff, CheckCircle, XCircle } from "lucide-react";

interface PasswordChangeProps {
  onClose: () => void;
  onSuccess: () => void;
}

export function PasswordChangeModal({ onClose, onSuccess }: PasswordChangeProps) {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Password strength checker
  const checkPasswordStrength = (password: string) => {
    const checks = {
      length: password.length >= 8,
      uppercase: /[A-Z]/.test(password),
      lowercase: /[a-z]/.test(password),
      number: /[0-9]/.test(password),
      special: /[!@#$%^&*(),.?":{}|<>]/.test(password),
    };

    const strength = Object.values(checks).filter(Boolean).length;
    return { checks, strength };
  };

  const { checks, strength } = checkPasswordStrength(newPassword);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    // Validation
    if (newPassword !== confirmPassword) {
      setError("New passwords don't match");
      return;
    }

    if (strength < 4) {
      setError("Password is too weak. Please meet all requirements.");
      return;
    }

    setLoading(true);

    try {
      const getCookie = () => {
        const match = document.cookie
          .split("; ")
          .find((c) => c.startsWith("admin_auth="));
        return match?.split("=")[1] || null;
      };

      const encoded = getCookie();
      if (!encoded) {
        setError("Session expired. Please login again.");
        return;
      }

      const response = await fetch(`${API_BASE}/admin/change-password`, {
        method: "POST",
        headers: {
          Authorization: `Basic ${encoded}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        setError(data.detail || "Failed to change password");
        return;
      }

      onSuccess();
      onClose();
    } catch (err) {
      setError("Backend not reachable");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="relative w-full max-w-md rounded-2xl bg-[#020617] border border-white/10 p-6 shadow-2xl">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyan-500/20 to-indigo-500/20 flex items-center justify-center">
            <Lock className="w-5 h-5 text-cyan-400" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-white">Change Password</h2>
            <p className="text-xs text-gray-400">Update your admin credentials</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Current Password */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">
              Current Password
            </label>
            <div className="relative">
              <input
                type={showCurrent ? "text" : "password"}
                placeholder="Enter current password"
                className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-3 pr-12 text-white placeholder:text-gray-600 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
              />
              <button
                type="button"
                onClick={() => setShowCurrent(!showCurrent)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition"
              >
                {showCurrent ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>

          {/* New Password */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">
              New Password
            </label>
            <div className="relative">
              <input
                type={showNew ? "text" : "password"}
                placeholder="Enter new password"
                className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-3 pr-12 text-white placeholder:text-gray-600 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
              />
              <button
                type="button"
                onClick={() => setShowNew(!showNew)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition"
              >
                {showNew ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>

          {/* Password Strength Indicator */}
          {newPassword && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-400">Password Strength</span>
                <span className={`font-medium ${
                  strength >= 5 ? "text-green-400" : 
                  strength >= 4 ? "text-yellow-400" : 
                  "text-red-400"
                }`}>
                  {strength >= 5 ? "Strong" : strength >= 4 ? "Good" : "Weak"}
                </span>
              </div>
              <div className="w-full h-2 bg-black/50 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-300 ${
                    strength >= 5 ? "bg-green-500" : 
                    strength >= 4 ? "bg-yellow-500" : 
                    "bg-red-500"
                  }`}
                  style={{ width: `${(strength / 5) * 100}%` }}
                />
              </div>
              
              {/* Requirements */}
              <div className="space-y-1 pt-2">
                <PasswordRequirement met={checks.length} text="At least 8 characters" />
                <PasswordRequirement met={checks.uppercase} text="One uppercase letter" />
                <PasswordRequirement met={checks.lowercase} text="One lowercase letter" />
                <PasswordRequirement met={checks.number} text="One number" />
                <PasswordRequirement met={checks.special} text="One special character" />
              </div>
            </div>
          )}

          {/* Confirm Password */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">
              Confirm New Password
            </label>
            <div className="relative">
              <input
                type={showConfirm ? "text" : "password"}
                placeholder="Confirm new password"
                className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-3 pr-12 text-white placeholder:text-gray-600 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />
              <button
                type="button"
                onClick={() => setShowConfirm(!showConfirm)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition"
              >
                {showConfirm ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          {/* Buttons */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-3 rounded-lg text-white font-medium bg-white/5 border border-white/10 hover:bg-white/10 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || strength < 4}
              className="flex-1 py-3 rounded-lg text-white font-medium bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed transition shadow-lg"
            >
              {loading ? "Updating..." : "Change Password"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function PasswordRequirement({ met, text }: { met: boolean; text: string }) {
  return (
    <div className="flex items-center gap-2 text-xs">
      {met ? (
        <CheckCircle className="w-4 h-4 text-green-400" />
      ) : (
        <XCircle className="w-4 h-4 text-gray-600" />
      )}
      <span className={met ? "text-gray-300" : "text-gray-500"}>{text}</span>
    </div>
  );
}