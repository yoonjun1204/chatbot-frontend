// --- frontend/src/pages/Admin/AdminDashboard.tsx ---
import React from 'react';
import { useAuth } from '../../auth/AuthContext';
import { LogOut, LayoutDashboard } from "lucide-react";
import HumanAgentPermissions from '../../components/Admin/UserManagement';
import LogsAndPerformance from '../../components/Admin/LogsAndPerformance';

const AdminDashboard: React.FC = () => {
    const { logout } = useAuth();

    return (
        <div className="min-h-screen bg-gray-50">
            {/* GLOBAL ADMIN HEADER */}
            <nav className="bg-white border-b border-gray-200 sticky top-0 z-40">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between h-16 items-center">
                        <div className="flex items-center gap-2">
                            <div className="bg-indigo-600 p-1.5 rounded-lg">
                                <LayoutDashboard className="text-white" size={20} />
                            </div>
                            <h1 className="text-xl font-bold text-gray-900">Admin Control Panel</h1>
                        </div>

                        <button
                            onClick={logout}
                            className="flex items-center gap-2 bg-white border border-gray-200 text-gray-600 hover:bg-red-50 hover:text-red-600 px-4 py-2 rounded-lg font-semibold transition-all shadow-sm"
                        >
                            <LogOut size={18} />
                            Logout
                        </button>
                    </div>
                </div>
            </nav>

            {/* DASHBOARD CONTENT */}
            <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8 space-y-12">
                <section>
                    <HumanAgentPermissions />
                </section>

                <hr className="border-gray-200" />

                <section>
                    <LogsAndPerformance />
                </section>
            </main>
        </div>
    );
};

export default AdminDashboard;