// frontend/src/pages/Admin/AdminDashboard.tsx
import React, { useState } from 'react';
import { useAuth } from '../../auth/AuthContext';
import {
    LogOut,
    LayoutDashboard,
    Users,
    Terminal,
    ShieldCheck,
    Settings,
    ChevronRight,
    Activity
} from "lucide-react";
import HumanAgentPermissions from '../../components/Admin/UserManagement';
import LogsAndPerformance from '../../components/Admin/LogsAndPerformance';

// Define the available pages
type AdminPage = 'overview' | 'users' | 'logs' | 'settings';

const AdminDashboard: React.FC = () => {
    const { user, logout } = useAuth();
    const [activePage, setActivePage] = useState<AdminPage>('overview');

    // Navigation menu items
    const menuItems = [
        { id: 'overview', label: 'Dashboard', icon: LayoutDashboard },
        { id: 'users', label: 'User Management', icon: Users },
        { id: 'logs', label: 'System Logs', icon: Terminal },
        { id: 'settings', label: 'Portal Settings', icon: Settings },
    ];

    const renderContent = () => {
        switch (activePage) {
            case 'users':
                return <HumanAgentPermissions />;
            case 'logs':
                return <LogsAndPerformance />;
            case 'overview':
                return (
                    <div className="space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <StatCard title="Active Agents" value="12" icon={Users} color="bg-indigo-500" />
                            <StatCard title="Chat Requests" value="148" icon={Activity} color="bg-emerald-500" />
                            <StatCard title="Security Level" value="High" icon={ShieldCheck} color="bg-slate-800" />
                        </div>
                        <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm">
                            <h2 className="text-xl font-bold text-slate-800 mb-2">Welcome back, Admin</h2>
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

            {/* --- SIDEBAR --- */}
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

            {/* --- MAIN CONTENT AREA --- */}
            <main className="flex-1 flex flex-col">
                {/* Header with breadcrumbs or title */}
                <header className="h-20 bg-white border-b border-slate-200 px-8 flex items-center justify-between sticky top-0 z-30">
                    <div>
                        <h2 className="text-2xl font-bold text-slate-800 capitalize">
                            {activePage === 'overview' ? 'Dashboard Overview' : activePage.replace(/-/g, ' ')}
                        </h2>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold">
                            {user?.email?.[0].toUpperCase()}
                        </div>
                    </div>
                </header>

                {/* Dynamic Page Content */}
                <div className="p-8 max-w-6xl">
                    {renderContent()}
                </div>
            </main>
        </div>
    );
};

// Helper component for Dashboard Stats
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