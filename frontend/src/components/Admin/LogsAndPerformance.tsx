// frontend/src/components/Admin/LogsAndPerformance.tsx
import React, { useState, useEffect } from 'react';
import { type ChatLog, type PerformanceReport } from './types';
import { useAuth } from '../../auth/AuthContext';
import {
    BarChart3,
    Search,
    Calendar,
    Trash2,
    Filter,
    Zap,
    Target,
    AlertTriangle,
    CheckCircle2,
    Clock,
    User,
    MessageSquare,
    Headphones,
    Hash // 🆕 Added Hash icon for ID
} from "lucide-react";

const LogsAndPerformance: React.FC = () => {
    const { logout } = useAuth();
    const [logs, setLogs] = useState<ChatLog[]>([]);
    const [report, setReport] = useState<PerformanceReport | null>(null);
    const [loading, setLoading] = useState(true);

    // Filter States
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [searchEmail, setSearchEmail] = useState('');

    const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
    const ADMIN_LOGS_URL = `${API_BASE}/api/admin/logs`;

    // Secure Fetch Wrapper
    const authenticatedFetch = async (url: string, options: RequestInit = {}) => {
        const token = localStorage.getItem("token");

        if (!token) {
            console.error("No token found");
            return Promise.reject("No token");
        }

        const res = await fetch(url, {
            ...options,
            headers: {
                ...options.headers,
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            }
        });

        if (res.status === 401) {
            console.error("Session expired");
            logout();
            return Promise.reject("Unauthorized");
        }

        return res;
    };

    const fetchReport = async () => {
        try {
            const res = await authenticatedFetch(`${ADMIN_LOGS_URL}/performance-report`);
            if (res.ok) {
                const data = await res.json();
                setReport(data);
            }
        } catch (err) {
            console.error("Failed to fetch report", err);
        }
    };

    const fetchLogs = async () => {
        setLoading(true);
        const params = new URLSearchParams();
        if (startDate) params.append("start_date", startDate);
        if (endDate) params.append("end_date", endDate);
        if (searchEmail) params.append("actor_email", searchEmail);

        try {
            const res = await authenticatedFetch(`${ADMIN_LOGS_URL}/?${params.toString()}`);
            if (res.ok) {
                const data = await res.json();
                if (Array.isArray(data)) {
                    setLogs(data);
                } else {
                    setLogs([]);
                }
            }
        } catch (err) {
            console.error("Failed to fetch logs", err);
        } finally {
            setLoading(false);
        }
    };

    const handleFlexibleCleanup = async () => {
        const confirmMsg = `Are you sure you want to delete logs for ${searchEmail || 'all users'} between ${startDate || 'beginning'} and ${endDate || 'now'}?`;

        if (window.confirm(confirmMsg)) {
            const params = new URLSearchParams();
            if (startDate) params.append("start_date", startDate);
            if (endDate) params.append("end_date", endDate);
            if (searchEmail) params.append("actor_email", searchEmail);

            try {
                await authenticatedFetch(`${ADMIN_LOGS_URL}/cleanup?${params.toString()}`, {
                    method: 'DELETE'
                });
                fetchLogs();
                fetchReport();
            } catch (e) {
                alert("Failed to cleanup logs");
            }
        }
    };

    useEffect(() => {
        fetchReport();
        fetchLogs();
    }, []);

    const isAgentLog = (log: ChatLog) => {
        return log.intent === 'human_agent_reply' || log.intent === 'human_conversation';
    };

    return (
        <div className="space-y-8">
            {/* PAGE HEADER */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
                        <BarChart3 className="text-indigo-600" size={28} />
                        System Intelligence
                    </h2>
                    <p className="text-slate-500 text-sm">Monitor chatbot performance metrics and conversation logs.</p>
                </div>
            </div>

            {/* METRICS GRID */}
            {report && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    <MetricCard label="Total Conversations" value={report?.total_conversations ?? 0} icon={MessageSquare} trend="Live Data" color="indigo" />
                    <MetricCard label="Avg. Accuracy" value={`${((report?.average_accuracy ?? 0) * 100).toFixed(1)}%`} icon={Target} trend="+2.4%" color="emerald" />
                    <MetricCard label="Avg. Latency" value={`${report?.average_response_time_ms?.toFixed(0) ?? 0}ms`} icon={Zap} trend="Fast" color="amber" />
                    <MetricCard label="Escalation Rate" value={report?.escalation_rate ?? "0%"} icon={AlertTriangle} trend="Action Required" color="red" />
                </div>
            )}

            {/* FILTERS */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-4">
                <div className="flex items-center gap-2 text-slate-800 font-bold text-sm mb-2">
                    <Filter size={16} />
                    Log Filters
                </div>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="relative">
                        <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
                        <input type="date" className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 outline-none" onChange={(e) => setStartDate(e.target.value)} />
                    </div>
                    <div className="relative">
                        <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
                        <input type="date" className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 outline-none" onChange={(e) => setEndDate(e.target.value)} />
                    </div>
                    <div className="relative md:col-span-1">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
                        <input type="text" placeholder="Search actor email..." className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 outline-none" value={searchEmail} onChange={(e) => setSearchEmail(e.target.value)} />
                    </div>
                    <div className="flex gap-2">
                        <button onClick={fetchLogs} className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-bold py-2 rounded-xl transition-all shadow-md shadow-indigo-100">Apply</button>
                        <button onClick={handleFlexibleCleanup} className="px-3 bg-white border border-red-100 text-red-500 hover:bg-red-50 rounded-xl transition-colors" title="Purge filtered logs"><Trash2 size={18} /></button>
                    </div>
                </div>
            </div>

            {/* LOG TABLE */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-slate-50/50 border-b border-slate-200">
                                <th className="p-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Session Info</th>
                                <th className="p-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Conversation Log</th>
                                <th className="p-4 text-xs font-bold text-slate-500 uppercase tracking-wider text-center">Inference</th>
                                <th className="p-4 text-xs font-bold text-slate-500 uppercase tracking-wider text-center">Performance</th>
                                <th className="p-4 text-xs font-bold text-slate-500 uppercase tracking-wider text-right">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {loading ? (
                                <tr><td colSpan={5} className="p-12 text-center text-slate-400 italic">Loading logs...</td></tr>
                            ) : logs.map((log) => {
                                const isAgentReply = log.intent === 'human_agent_reply';
                                return (
                                    <tr key={log.id} className="hover:bg-slate-50/50 transition-colors group">

                                        {/* 🟢 MODIFIED: Added Conversation ID */}
                                        <td className="p-4 align-top">
                                            <div className="flex flex-col gap-1">
                                                <div className="flex items-center gap-1.5 text-xs font-bold text-slate-900">
                                                    <Clock size={12} className="text-slate-400" />
                                                    {new Date(log.timestamp).toLocaleTimeString('en-SG', { hour: '2-digit', minute: '2-digit' })}
                                                </div>
                                                <div className="text-[10px] text-slate-400 font-medium uppercase tracking-tight">
                                                    {new Date(log.timestamp).toLocaleDateString()}
                                                </div>
                                                <div className="mt-2 flex items-center gap-2">
                                                    <div className={`p-1.5 rounded-lg ${log.actor_email && log.actor_email !== "anonymous" ? "bg-indigo-50 text-indigo-600" : "bg-slate-100 text-slate-400"}`}>
                                                        <User size={14} />
                                                    </div>
                                                    <div className="truncate max-w-[120px]">
                                                        <div className="text-xs font-bold text-slate-700 truncate">
                                                            {log.actor_email !== "anonymous" ? log.actor_email : "Guest User"}
                                                        </div>
                                                        <div className="text-[9px] font-mono text-slate-400">User ID: {log.actor_id}</div>
                                                    </div>
                                                </div>

                                                {/* 🆕 Conversation ID Badge */}
                                                {log.conversation_id && (
                                                    <div className="mt-1.5 inline-flex items-center gap-1 px-1.5 py-0.5 bg-slate-100 rounded border border-slate-200 w-fit">
                                                        <Hash size={10} className="text-slate-400" />
                                                        <span className="text-[10px] font-mono font-bold text-slate-600">
                                                            Conversation ID #{log.conversation_id}
                                                        </span>
                                                    </div>
                                                )}
                                            </div>
                                        </td>

                                        <td className="p-4 align-top max-w-md">
                                            <div className="space-y-3">
                                                {log.user_message && (
                                                    <div>
                                                        <span className="text-[10px] font-black text-indigo-400 uppercase tracking-widest block mb-1">User</span>
                                                        <p className="text-sm text-slate-700 bg-slate-50 p-2 rounded-lg border border-slate-100 italic">"{log.user_message}"</p>
                                                    </div>
                                                )}
                                                {log.bot_response && (
                                                    <div>
                                                        {isAgentReply ? (
                                                            <span className="flex items-center gap-1 text-[10px] font-black text-blue-600 uppercase tracking-widest mb-1"><Headphones size={10} /> Agent</span>
                                                        ) : (
                                                            <span className="text-[10px] font-black text-emerald-400 uppercase tracking-widest block mb-1">Bot</span>
                                                        )}
                                                        <p className={`text-sm px-2 line-clamp-2 ${isAgentReply ? 'text-blue-800 font-medium' : 'text-slate-600'}`}>{log.bot_response}</p>
                                                    </div>
                                                )}
                                            </div>
                                        </td>
                                        <td className="p-4 align-top text-center">
                                            <div className={`inline-flex flex-col items-center p-2 rounded-xl border ${isAgentLog(log) ? 'bg-blue-50 border-blue-100' : 'bg-slate-50 border-slate-100'}`}>
                                                <span className={`text-xs font-bold ${isAgentLog(log) ? 'text-blue-700' : 'text-slate-800'}`}>{log.intent || "Unknown"}</span>
                                                {!isAgentLog(log) && (
                                                    <>
                                                        <div className="w-12 h-1 bg-slate-200 rounded-full mt-1 overflow-hidden">
                                                            <div className="h-full bg-indigo-500" style={{ width: `${(log.confidence || 0) * 100}%` }} />
                                                        </div>
                                                        <span className="text-[10px] text-slate-400 mt-1">{((log.confidence || 0) * 100).toFixed(0)}% Match</span>
                                                    </>
                                                )}
                                                {isAgentLog(log) && <span className="text-[10px] text-blue-400 mt-1">Human</span>}
                                            </div>
                                        </td>
                                        <td className="p-4 align-top text-center">
                                            <div className="flex flex-col items-center">
                                                <span className={`text-xs font-mono font-bold ${log.response_time_ms > 1000 ? 'text-amber-600' : 'text-slate-600'}`}>{log.response_time_ms.toFixed(0)}ms</span>
                                                <div className="text-[10px] text-slate-400">Latency</div>
                                            </div>
                                        </td>
                                        <td className="p-4 align-top text-right">
                                            {log.is_escalated ? (
                                                <span className="inline-flex items-center gap-1 bg-red-50 text-red-600 px-2.5 py-1 rounded-full text-[10px] font-black ring-1 ring-inset ring-red-200/50"><AlertTriangle size={10} /> ESCALATED</span>
                                            ) : (
                                                <span className="inline-flex items-center gap-1 bg-emerald-50 text-emerald-600 px-2.5 py-1 rounded-full text-[10px] font-black ring-1 ring-inset ring-emerald-200/50"><CheckCircle2 size={10} /> HEALTHY</span>
                                            )}
                                        </td>
                                    </tr>
                                )
                            })}
                        </tbody>
                    </table>
                </div>
                {!loading && logs.length === 0 && (
                    <div className="p-20 text-center">
                        <div className="text-slate-300 mb-2 font-medium">No logs found matching your criteria</div>
                        <p className="text-slate-400 text-sm">Try adjusting your date filters or search terms.</p>
                    </div>
                )}
            </div>
        </div>
    );
};

// MetricCard helper remains unchanged
const MetricCard = ({ label, value, icon: Icon, trend, color }: any) => {
    const colors: any = {
        indigo: "bg-indigo-50 text-indigo-600 border-indigo-100",
        emerald: "bg-emerald-50 text-emerald-600 border-emerald-100",
        amber: "bg-amber-50 text-amber-600 border-amber-100",
        red: "bg-red-50 text-red-600 border-red-100",
    };
    return (
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
            <div className="flex justify-between items-start mb-4">
                <div className={`p-2 rounded-xl border ${colors[color]}`}><Icon size={20} /></div>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${colors[color]}`}>{trend}</span>
            </div>
            <p className="text-sm font-medium text-slate-500 mb-1">{label}</p>
            <p className="text-2xl font-black text-slate-900 tracking-tight">{value}</p>
        </div>
    );
};

export default LogsAndPerformance;