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
  CheckCircle2
} from "lucide-react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

interface LoginResponse {
  id: number;
  email: string;
  name?: string | null;
  role: UserRole;
}

const roles: { key: UserRole; label: string; icon: any; color: string }[] = [
  { key: "customer", label: "Customer", icon: ShoppingBag, color: "blue" },
  { key: "agent", label: "Agent", icon: Headset, color: "indigo" },
  { key: "admin", label: "Admin", icon: ShieldCheck, color: "slate" },
];

const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const [selectedRole, setSelectedRole] = useState<UserRole | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!selectedRole) {
      setError("Please select your portal role first.");
      return;
    }

    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/api/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        let msg: any = null;
        try { msg = await res.json(); } catch { /* ignore */ }
        throw new Error(msg?.detail || "Login failed");
      }

      const data: LoginResponse = await res.json();
      if (data.role !== selectedRole) {
        throw new Error(`Access denied. Your account is registered as ${data.role}.`);
      }

      const authUser: AuthUser = {
        id: data.id,
        email: data.email,
        name: data.name,
        role: data.role,
      };
      login(authUser);
    } catch (err: any) {
      setError(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex bg-white">

      {/* --- LEFT SIDE: HERO / BRANDING --- */}
      <div className="hidden lg:flex lg:w-1/2 bg-slate-900 relative items-center justify-center p-12 overflow-hidden">
        {/* Abstract Background Decoration */}
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

      {/* --- RIGHT SIDE: LOGIN FORM --- */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 md:p-16">
        <div className="max-w-md w-full">
          {/* Mobile Logo Only */}
          <div className="lg:hidden flex items-center gap-2 mb-8">
            <div className="bg-blue-600 p-2 rounded-lg text-white">
              <Shirt size={24} />
            </div>
            <span className="text-2xl font-bold text-slate-900">Shirtify</span>
          </div>

          <div className="mb-10">
            <h2 className="text-3xl font-bold text-slate-900 mb-2">Welcome Back</h2>
            <p className="text-slate-500">Select your role and enter your credentials.</p>
          </div>

          {/* Role selection - Horizontal Grid */}
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
            <div className="space-y-1.5">
              <label className="text-sm font-bold text-slate-700 ml-1">Work Email</label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                <input
                  type="email"
                  placeholder="name@shirtify.com"
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
                <a href="#" className="text-xs font-bold text-blue-600 hover:underline">Forgot?</a>
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

            <button
              className="w-full bg-slate-900 hover:bg-slate-800 text-white font-bold py-4 rounded-2xl shadow-xl shadow-slate-200 flex items-center justify-center gap-2 transition-all active:scale-[0.99] disabled:opacity-70 disabled:cursor-not-allowed group"
              type="submit"
              disabled={loading}
            >
              {loading ? (
                <Loader2 className="animate-spin" size={20} />
              ) : (
                <>
                  Sign into Portal
                  <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>
          </form>

          {/* Demo Credentials Helper */}
          <div className="mt-10 p-6 bg-slate-50 rounded-2xl border border-slate-200/60">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
              <h4 className="text-[10px] uppercase tracking-[0.15em] font-black text-slate-400">
                Staging Demo Access
              </h4>
            </div>

            <div className="space-y-2">
              {[
                { role: 'Customer', email: 'alicetan@example.com', color: 'text-blue-600' },
                { role: 'Support Agent', email: 'agent@example.com', color: 'text-indigo-600' },
                { role: 'Administrator', email: 'admin@example.com', color: 'text-slate-700' },
              ].map((demo) => (
                <div
                  key={demo.email}
                  className="flex justify-between items-center bg-white p-2.5 rounded-xl border border-slate-100 shadow-sm transition-hover hover:border-blue-200"
                >
                  <span className="text-[10px] font-black text-slate-400 uppercase tracking-tighter">
                    {demo.role}
                  </span>
                  <code className={`text-[11px] ${demo.color} font-bold select-all cursor-pointer`}>
                    {demo.email}
                  </code>
                </div>
              ))}
            </div>

            {/* Shared Password Footer */}
            <div className="mt-4 pt-3 border-t border-dashed border-slate-200 flex justify-between items-center">
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-tight">Shared Password</span>
              <code className="bg-slate-900 text-white px-2 py-0.5 rounded-md text-[11px] font-bold shadow-sm">
                password123
              </code>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;