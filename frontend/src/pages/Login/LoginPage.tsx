// frontend/src/pages/Login/LoginPage.tsx
import React, { useState } from "react";
import { useAuth, type UserRole, type AuthUser } from "../../auth/AuthContext";
import {
  Shirt,
  ShoppingBag,
  ShieldCheck,
  Headset,
  Mail,
  Lock,
  AlertCircle,
  ArrowRight,
  Loader2,
  CheckCircle2,
  User,
  MousePointerClick
} from "lucide-react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

interface LoginResponse {
  id: number;
  email: string;
  name?: string | null;
  role: UserRole;
  access_token: string;
}

const roles: { key: UserRole; label: string; icon: any; color: string }[] = [
  { key: "customer", label: "Customer", icon: ShoppingBag, color: "blue" },
  { key: "agent", label: "Agent", icon: Headset, color: "indigo" },
  { key: "admin", label: "Admin", icon: ShieldCheck, color: "slate" },
];

const demoUsers = [
  { roleLabel: 'Customer', roleKey: 'customer' as UserRole, email: 'alicetan@example.com', color: 'text-blue-600' },
  { roleLabel: 'Support Agent', roleKey: 'agent' as UserRole, email: 'agent@example.com', color: 'text-indigo-600' },
  { roleLabel: 'Administrator', roleKey: 'admin' as UserRole, email: 'admin@example.com', color: 'text-slate-700' },
];

const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const [isRegistering, setIsRegistering] = useState(false);

  // Form States
  const [selectedRole, setSelectedRole] = useState<UserRole | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");

  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Auto-fill Handler
  const handleAutoFill = (demo: typeof demoUsers[0]) => {
    setEmail(demo.email);
    setPassword("password123");
    setSelectedRole(demo.roleKey);
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);

    if (!selectedRole) {
      setError("Please select your portal role first.");
      return;
    }

    try {
      setLoading(true);

      const endpoint = isRegistering ? "/api/register" : "/api/login";
      const payload = isRegistering
        ? { email, password, role: selectedRole, name }
        : { email, password };

      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const rawData = await res.json();

      if (!res.ok) {
        throw new Error(rawData?.detail || (isRegistering ? "Registration failed" : "Login failed"));
      }

      if (isRegistering) {
        setSuccessMsg("Account created successfully! Please sign in.");
        setIsRegistering(false);
        setPassword("");
      } else {
        const data = rawData as LoginResponse;

        if (data.role !== selectedRole) {
          throw new Error(`Access denied. Your account is registered as ${data.role}.`);
        }

        if (data.access_token) {
          console.log("✅ Token received:", data.access_token);
          localStorage.setItem("token", data.access_token);
        } else {
          console.error("❌ MISSING TOKEN in response:", data);
          throw new Error("Login successful, but server didn't send a security token.");
        }

        const authUser: AuthUser = {
          id: data.id,
          email: data.email,
          name: data.name,
          role: data.role,
        };

        login(authUser);
      }

    } catch (err: any) {
      console.error("Login Error:", err);
      setError(err.message || "An error occurred");
      localStorage.removeItem("token");
    } finally {
      setLoading(false);
    }
  };

  const toggleMode = () => {
    setIsRegistering(!isRegistering);
    setError(null);
    setSuccessMsg(null);
    setPassword("");
  };

  return (
    <div className="min-h-screen flex bg-white">

      {/* --- LEFT SIDE: HERO / BRANDING --- */}
      <div className="hidden lg:flex lg:w-1/2 bg-slate-900 relative items-center justify-center p-12 overflow-hidden">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-600/20 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-indigo-600/20 rounded-full blur-[120px]" />

        <div className="relative z-10 max-w-lg text-center lg:text-left">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 border border-white/10 text-blue-400 text-sm font-bold mb-8">
            <Shirt size={18} />
            Shirtify Portal v2.0
          </div>
          <h1 className="text-5xl font-extrabold text-white leading-tight mb-6">
            Everything you need to <span className="text-blue-500">support</span> our customers.
          </h1>
          <p className="text-slate-400 text-lg leading-relaxed mb-10">
            Access the Shirtify internal dashboard to manage orders, resolve customer queries, and monitor system performance.
          </p>

          <div className="grid grid-cols-2 gap-6">
            <div className="flex items-center gap-3 text-slate-300">
              <CheckCircle2 size={20} className="text-blue-500" />
              <span className="text-sm font-medium">Real-time Chat</span>
            </div>
            <div className="flex items-center gap-3 text-slate-300">
              <CheckCircle2 size={20} className="text-blue-500" />
              <span className="text-sm font-medium">Admin Controls</span>
            </div>
          </div>
        </div>
      </div>

      {/* --- RIGHT SIDE: FORM --- */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 md:p-16">
        <div className="max-w-md w-full">

          {/* Mobile Logo */}
          <div className="lg:hidden flex items-center gap-2 mb-8">
            <div className="bg-blue-600 p-2 rounded-lg text-white">
              <Shirt size={24} />
            </div>
            <span className="text-2xl font-bold text-slate-900">Shirtify</span>
          </div>

          <div className="mb-10">
            <h2 className="text-3xl font-bold text-slate-900 mb-2">
              {isRegistering ? "Create Account" : "Welcome Back"}
            </h2>
            <p className="text-slate-500">
              {isRegistering
                ? "Join the team. Select your role to get started."
                : "Select your role and enter your credentials."}
            </p>
          </div>

          {/* Role selection */}
          <div className="grid grid-cols-3 gap-3 mb-8">
            {roles.map((r) => {
              const Icon = r.icon;
              const isSelected = selectedRole === r.key;
              return (
                <button
                  key={r.key}
                  type="button"
                  onClick={() => setSelectedRole(r.key)}
                  className={`flex flex-col items-center justify-center p-4 rounded-2xl border-2 transition-all group ${isSelected
                    ? "border-blue-600 bg-blue-50/50"
                    : "border-slate-100 hover:border-slate-200 bg-white"
                    }`}
                >
                  <div className={`p-2 rounded-xl mb-2 transition-colors ${isSelected ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-500 group-hover:bg-slate-200"
                    }`}>
                    <Icon size={20} />
                  </div>
                  <span className={`text-xs font-bold ${isSelected ? "text-blue-900" : "text-slate-600"}`}>
                    {r.label}
                  </span>
                </button>
              );
            })}
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">

            {isRegistering && (
              <div className="space-y-1.5 animate-in fade-in slide-in-from-top-2">
                <label className="text-sm font-bold text-slate-700 ml-1">Full Name</label>
                <div className="relative">
                  <User className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                  <input
                    type="text"
                    placeholder="John Doe"
                    className="w-full pl-12 pr-4 py-3.5 bg-slate-50 border border-slate-200 rounded-2xl focus:ring-2 focus:ring-blue-600 outline-none transition-all"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                  />
                </div>
              </div>
            )}

            <div className="space-y-1.5">
              <label className="text-sm font-bold text-slate-700 ml-1">Work Email</label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                <input
                  type="email"
                  placeholder="name@example.com"
                  className="w-full pl-12 pr-4 py-3.5 bg-slate-50 border border-slate-200 rounded-2xl focus:ring-2 focus:ring-blue-600 outline-none transition-all"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between items-center ml-1">
                <label className="text-sm font-bold text-slate-700">Password</label>
                {!isRegistering && <a href="#" className="text-xs font-bold text-blue-600 hover:underline">Forgot?</a>}
              </div>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                <input
                  type="password"
                  placeholder="••••••••"
                  className="w-full pl-12 pr-4 py-3.5 bg-slate-50 border border-slate-200 rounded-2xl focus:ring-2 focus:ring-blue-600 outline-none transition-all"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
            </div>

            {error && (
              <div className="flex items-center gap-2 bg-red-50 text-red-600 p-4 rounded-2xl text-sm border border-red-100 animate-in fade-in slide-in-from-top-1">
                <AlertCircle size={18} className="shrink-0" />
                <p className="font-medium">{error}</p>
              </div>
            )}

            {successMsg && (
              <div className="flex items-center gap-2 bg-green-50 text-green-600 p-4 rounded-2xl text-sm border border-green-100 animate-in fade-in slide-in-from-top-1">
                <CheckCircle2 size={18} className="shrink-0" />
                <p className="font-medium">{successMsg}</p>
              </div>
            )}

            {/* Main Submit Button */}
            <button
              className="w-full bg-slate-900 hover:bg-slate-800 text-white font-bold py-4 rounded-2xl shadow-xl shadow-slate-200 flex items-center justify-center gap-2 transition-all active:scale-[0.99] disabled:opacity-70 disabled:cursor-not-allowed group"
              type="submit"
              disabled={loading}
            >
              {loading ? (
                <Loader2 className="animate-spin" size={20} />
              ) : (
                <>
                  {isRegistering ? "Create Account" : "Sign into Portal"}
                  <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>

            {/* 🆕 SECONDARY ACTION: Cancel / Go Back (Only visible during registration) */}
            {isRegistering && (
              <button
                type="button"
                onClick={toggleMode}
                className="w-full py-3 rounded-2xl font-bold text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors animate-in fade-in slide-in-from-top-1"
              >
                Cancel & Go Back
              </button>
            )}

          </form>

          {/* Bottom Link (Only show when NOT registering to avoid clutter) */}
          {!isRegistering && (
            <div className="mt-8 text-center">
              <p className="text-slate-500 text-sm">
                Don't have an account?{" "}
                <button
                  onClick={toggleMode}
                  className="text-blue-600 font-bold hover:underline outline-none"
                >
                  Register now
                </button>
              </p>
            </div>
          )}

          {/* DEMO ACCESS SECTION (Only on Login) */}
          {!isRegistering && (
            <div className="mt-10 p-6 bg-slate-50 rounded-2xl border border-slate-200/60">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
                  <h4 className="text-[10px] uppercase tracking-[0.15em] font-black text-slate-400">
                    Staging Demo Access
                  </h4>
                </div>
                <div className="flex items-center gap-1 text-[10px] text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full font-bold">
                  <MousePointerClick size={12} />
                  Click to fill
                </div>
              </div>

              <div className="space-y-2">
                {demoUsers.map((demo) => (
                  <button
                    key={demo.email}
                    onClick={() => handleAutoFill(demo)}
                    className="w-full flex justify-between items-center bg-white p-2.5 rounded-xl border border-slate-100 shadow-sm transition-all hover:border-blue-300 hover:shadow-md hover:scale-[1.01] active:scale-[0.98] group"
                    type="button"
                    title={`Click to fill credentials for ${demo.roleLabel}`}
                  >
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-tighter group-hover:text-slate-600 transition-colors">
                      {demo.roleLabel}
                    </span>
                    <code className={`text-[11px] ${demo.color} font-bold`}>
                      {demo.email}
                    </code>
                  </button>
                ))}
              </div>

              <div className="mt-4 pt-3 border-t border-dashed border-slate-200 flex justify-between items-center">
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-tight">Shared Password</span>
                <code className="bg-slate-900 text-white px-2 py-0.5 rounded-md text-[11px] font-bold shadow-sm tracking-widest">
                  ••••••••
                </code>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LoginPage;