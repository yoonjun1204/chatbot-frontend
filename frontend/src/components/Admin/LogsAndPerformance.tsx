// --- frontend/src/components/Admin/LogsAndPerformance.tsx ---
import React, { useState, useEffect } from 'react';
import { type ChatLog, type PerformanceReport } from './types';
import { useAuth } from '../../auth/AuthContext';

const LogsAndPerformance: React.FC = () => {
    const { user } = useAuth();
    const [logs, setLogs] = useState<ChatLog[]>([]);
    const [report, setReport] = useState<PerformanceReport | null>(null);
    const [loading, setLoading] = useState(true);

    // Filter States
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [searchEmail, setSearchEmail] = useState(''); // RENAMED: from actorId to searchEmail

    const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
    // Helper to avoid repeating the prefix
    const ADMIN_LOGS_URL = `${API_BASE}/api/admin/logs`;

    const authenticatedFetch = async (url: string, options: RequestInit = {}) => {
        return fetch(url, {
            ...options,
            headers: {
                ...options.headers,
                "Content-Type": "application/json",
                "user_id": user?.id.toString() || "",
            }
        });
    };

    const fetchReport = async () => {
        try {
            // FIX: Use the constant path
            const res = await authenticatedFetch(`${ADMIN_LOGS_URL}/performance-report`);
            const data = await res.json();
            setReport(data);
        } catch (err) {
            console.error("Failed to fetch report", err);
        }
    };

    const fetchLogs = async () => {
        setLoading(true);
        // FIX: Build query string correctly
        const params = new URLSearchParams();
        if (startDate) params.append("start_date", startDate);
        if (endDate) params.append("end_date", endDate);
        if (searchEmail) params.append("actor_email", searchEmail); // FIX: actor_email, not actor_id

        try {
            const res = await authenticatedFetch(`${ADMIN_LOGS_URL}/?${params.toString()}`);
            const data = await res.json();
            setLogs(data);
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

            // FIX: Correct URL path added
            await authenticatedFetch(`${ADMIN_LOGS_URL}/cleanup?${params.toString()}`, {
                method: 'DELETE'
            });

            fetchLogs();
            fetchReport();
        }
    };

    useEffect(() => {
        fetchReport();
        fetchLogs();
    }, []);

    return (
        <div className="admin-logs-container p-6 bg-white rounded-xl shadow-sm border border-gray-100">
            <h2 className="text-2xl font-bold mb-6 text-gray-800">Chatbot Performance & Logs</h2>

            {/* Performance Cards (Existing logic is fine) */}
            {report && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                    {/* Performance Cards */}
                    {report && (
                        <div className="metrics-grid">
                            <div className="metric-card">
                                <h3>Total Chats</h3>
                                {/* Use 0 as fallback */}
                                <p>{report?.total_conversations ?? 0}</p>
                            </div>

                            <div className="metric-card">
                                <h3>Avg Accuracy</h3>
                                {/* Check if property exists before calling toFixed */}
                                <p>
                                    {report?.average_accuracy !== undefined
                                        ? (report.average_accuracy * 100).toFixed(1)
                                        : "0.0"}%
                                </p>
                            </div>

                            <div className="metric-card">
                                <h3>Avg Response Time</h3>
                                <p>
                                    {report?.average_response_time_ms !== undefined
                                        ? report.average_response_time_ms.toFixed(0)
                                        : "0"} ms
                                </p>
                            </div>

                            <div className="metric-card danger">
                                <h3>Escalation Rate</h3>
                                <p>{report?.escalation_rate ?? "0%"}</p>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* Filters & Controls */}
            <div className="flex flex-wrap gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
                <div className="flex flex-col">
                    <label className="text-xs font-bold text-gray-500 uppercase">Start</label>
                    <input type="date" className="border p-2 rounded" onChange={(e) => setStartDate(e.target.value)} />
                </div>
                <div className="flex flex-col">
                    <label className="text-xs font-bold text-gray-500 uppercase">End</label>
                    <input type="date" className="border p-2 rounded" onChange={(e) => setEndDate(e.target.value)} />
                </div>
                <div className="flex flex-col flex-1">
                    <label className="text-xs font-bold text-gray-500 uppercase">Email Address</label>
                    <input
                        type="text"
                        placeholder="Search by user email..."
                        className="border p-2 rounded"
                        value={searchEmail}
                        onChange={(e) => setSearchEmail(e.target.value)}
                    />
                </div>
                <div className="flex items-end gap-2">
                    <button className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700" onClick={fetchLogs}>Apply</button>
                    <button className="bg-red-50 text-red-600 border border-red-200 px-4 py-2 rounded hover:bg-red-100" onClick={handleFlexibleCleanup}>
                        Purge Filtered
                    </button>
                </div>
            </div>

            {/* Log Table */}
            {/* --- Inside LogsAndPerformance.tsx --- */}
            <div className="overflow-x-auto border rounded-lg">
                {loading ? (
                    <p className="p-4 text-center text-gray-500">Loading logs...</p>
                ) : (
                    <table className="w-full text-left text-sm">
                        <thead className="bg-gray-50 border-b text-gray-600 uppercase text-[11px]">
                            <tr>
                                <th className="p-3">Timestamp</th>
                                <th className="p-3">Actor (Email / ID)</th>
                                <th className="p-3">User Message</th>
                                <th className="p-3">Bot Response</th>
                                <th className="p-3">Intent (Conf)</th>
                                <th className="p-3">Latency</th>
                                <th className="p-3">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y">
                            {logs.map((log) => (
                                <tr key={log.id} className="border-b hover:bg-gray-50 text-sm">
                                    <td className="p-3 text-gray-500 whitespace-nowrap">
                                        {new Date(log.timestamp).toLocaleString('en-SG', {
                                            timeZone: 'Asia/Singapore',
                                            hour12: true,
                                            year: 'numeric',
                                            month: '2-digit',
                                            day: '2-digit',
                                            hour: '2-digit',
                                            minute: '2-digit'
                                        })}
                                    </td>
                                    <td className="p-3">
                                        {log.actor_email && log.actor_email !== "anonymous" ? (
                                            <>
                                                <div className="font-bold text-indigo-600">{log.actor_email}</div>
                                                <div className="text-[10px] text-gray-500 font-mono">
                                                    User ID: <span className="text-gray-800 font-bold">{log.actor_id}</span>
                                                </div>
                                            </>
                                        ) : (
                                            <>
                                                <div className="font-bold text-gray-400">Guest User</div>
                                                <div className="text-[10px] text-gray-400">Unauthenticated Session</div>
                                            </>
                                        )}
                                    </td>
                                    <td className="p-3 max-w-xs truncate">{log.user_message}</td>
                                    <td className="p-3 max-w-xs truncate">{log.bot_response}</td>
                                    <td className="p-3">
                                        <div className="font-medium">{log.intent}</div>
                                        <div className="text-xs text-gray-400">({(log.confidence * 100).toFixed(0)}%)</div>
                                    </td>
                                    <td className="p-3 font-mono text-xs">{log.response_time_ms.toFixed(0)}ms</td>
                                    <td className="p-3">
                                        {log.is_escalated ? (
                                            <span className="bg-red-100 text-red-700 px-2 py-1 rounded text-[10px] font-bold">ESCALATED</span>
                                        ) : (
                                            <span className="bg-green-100 text-green-700 px-2 py-1 rounded text-[10px] font-bold">OK</span>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    );
};

export default LogsAndPerformance;