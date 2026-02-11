// frontend/src/pages/Admin/AdminDashboard.tsx
import React, { useState, useEffect } from 'react';
import { useAuth } from '../../auth/AuthContext';
import {
    LogOut,
    LayoutDashboard,
    Users,
    Terminal,
    ShieldCheck,
    Settings,
    ChevronRight,
    Activity,
    Loader2,
    UserCircle // Added for Customer icon
} from "lucide-react";

// Import your sub-components
import HumanAgentPermissions from '../../components/Admin/UserManagement';
import LogsAndPerformance from '../../components/Admin/LogsAndPerformance';

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

type AdminPage = 'overview' | 'users' | 'logs' | 'settings';

const AdminDashboard: React.FC = () => {
    const { user, logout } = useAuth();
    const [activePage, setActivePage] = useState<AdminPage>('overview');

    // 🟢 Updated State for Specific Roles
    const [loadingStats, setLoadingStats] = useState(false);
    const [stats, setStats] = useState({
        activeAgents: 0,
        activeAdmins: 0,
        activeCustomers: 0,
        systemHealth: "Unknown"
    });

    const menuItems = [
        { id: 'overview', label: 'Dashboard', icon: LayoutDashboard },
        { id: 'users', label: 'User Management', icon: Users },
        { id: 'logs', label: 'System Logs', icon: Terminal },
        { id: 'settings', label: 'Portal Settings', icon: Settings },
    ];

    const authenticatedFetch = async (endpoint: string) => {
        const token = localStorage.getItem("token");
        if (!token) {
            logout();
            return null;
        }

        try {
            const res = await fetch(`${API_BASE}${endpoint}`, {
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                }
            });

            if (res.status === 401) {
                logout();
                return null;
            }
            return res;
        } catch (error) {
            console.error("Network error:", error);
            return null;
        }
    };

    // 🟢 FETCH & FILTER DATA BY ROLE
    useEffect(() => {
        if (activePage === 'overview') {
            const fetchOverviewData = async () => {
                setLoadingStats(true);
                const userRes = await authenticatedFetch("/api/admin/users/");

                if (userRes && userRes.ok) {
                    const users = await userRes.json();

                    // Filter counts based on role
                    const agents = users.filter((u: any) => u.role === 'agent').length;
                    const admins = users.filter((u: any) => u.role === 'admin').length;
                    const customers = users.filter((u: any) => u.role === 'customer').length;

                    setStats({
                        activeAgents: agents,
                        activeAdmins: admins,
                        activeCustomers: customers,
                        systemHealth: "Healthy"
                    });
                }
                setLoadingStats(false);
            };
            fetchOverviewData();
        }
    }, [activePage]);

    const renderContent = () => {
        switch (activePage) {
            case 'users':
                return <HumanAgentPermissions />;
            case 'logs':
                return <LogsAndPerformance />;
            case 'overview':
                return (
                    <div className="space-y-6">
                        {/* 🟢 Updated Grid to show 4 cards */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                            {loadingStats ? (
                                <div className="col-span-4 flex justify-center py-10 text-slate-400">
                                    <Loader2 className="animate-spin" /> Loading stats...
                                </div>
                            ) : (
                                <>
                                    <StatCard
                                        title="Active Agents"
                                        value={stats.activeAgents.toString()}
                                        icon={Users}
                                        color="bg-indigo-500"
                                    />
                                    <StatCard
                                        title="Administrators"
                                        value={stats.activeAdmins.toString()}
                                        icon={ShieldCheck}
                                        color="bg-slate-800"
                                    />
                                    <StatCard
                                        title="Customers"
                                        value={stats.activeCustomers.toString()}
                                        icon={UserCircle}
                                        color="bg-emerald-500"
                                    />
                                    <StatCard
                                        title="System Status"
                                        value={stats.systemHealth}
                                        icon={Activity}
                                        color="bg-blue-500"
                                    />
                                </>
                            )}
                        </div>
                        <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm">
                            <h2 className="text-xl font-bold text-slate-800 mb-2">Welcome back, {user?.name || "Admin"}</h2>
                            <p className="text-slate-500">Select a functionality from the sidebar to manage your support portal.</p>
                        </div>
                    </div>
                );
            default:
                return <div className="p-8 text-slate-400">Section under development...</div>;
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 flex">
            <aside className="w-72 bg-slate-900 text-white flex flex-col sticky top-0 h-screen">
                <div className="p-6 border-b border-slate-800">
                    <div className="flex items-center gap-3">
                        <div className="bg-indigo-600 p-2 rounded-lg">
                            <ShieldCheck size={24} />
                        </div>
                        <div>
                            <h1 className="font-bold text-lg leading-tight">AdminPanel</h1>
                            <p className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">Shirtify v2.0</p>
                        </div>
                    </div>
                </div>

                <nav className="flex-1 p-4 space-y-1">
                    {menuItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = activePage === item.id;
                        return (
                            <button
                                key={item.id}
                                onClick={() => setActivePage(item.id as AdminPage)}
                                className={`w-full flex items-center justify-between px-4 py-3 rounded-xl transition-all ${isActive
                                    ? "bg-indigo-600 text-white shadow-lg shadow-indigo-900/20"
                                    : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
                                    }`}
                            >
                                <div className="flex items-center gap-3">
                                    <Icon size={20} />
                                    <span className="font-medium">{item.label}</span>
                                </div>
                                {isActive && <ChevronRight size={16} />}
                            </button>
                        );
                    })}
                </nav>

                <div className="p-4 border-t border-slate-800">
                    <div className="bg-slate-800/50 rounded-2xl p-4 mb-4">
                        <div className="text-xs text-slate-500 mb-1">Logged in as</div>
                        <div className="text-sm font-bold truncate">{user?.email}</div>
                    </div>
                    <button
                        onClick={logout}
                        className="w-full flex items-center justify-center gap-2 py-3 rounded-xl border border-slate-700 text-slate-300 hover:bg-red-500 hover:text-white hover:border-red-500 transition-all font-bold"
                    >
                        <LogOut size={18} />
                        Logout
                    </button>
                </div>
            </aside>

            <main className="flex-1 flex flex-col">
                <header className="h-20 bg-white border-b border-slate-200 px-8 flex items-center justify-between sticky top-0 z-30">
                    <div>
                        <h2 className="text-2xl font-bold text-slate-800 capitalize">
                            {activePage === 'overview' ? 'Dashboard Overview' : activePage.replace(/-/g, ' ')}
                        </h2>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold">
                            {user?.email?.[0].toUpperCase() || "A"}
                        </div>
                    </div>
                </header>

                <div className="p-8 max-w-6xl">
                    {renderContent()}
                </div>
            </main>
        </div>
    );
};

const StatCard = ({ title, value, icon: Icon, color }: any) => (
    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-5">
        <div className={`${color} p-3 rounded-xl text-white`}>
            <Icon size={24} />
        </div>
        <div>
            <p className="text-sm font-medium text-slate-500">{title}</p>
            <p className="text-2xl font-bold text-slate-900">{value}</p>
        </div>
    </div>
);

export default AdminDashboard;