// frontend/src/pages/HumanAgent/AgentDashboard.tsx
import { useEffect, useState } from 'react';
import { useAuth } from "../../auth/AuthContext";
import AgentEscalation from "../../components/Agent/AgentEscalation";
import type { AgentConversation, AgentMessage } from '../../components/Agent/types';
import { LogOut, Inbox, Search, Clock } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const AgentDashboard = () => {
  // 🟢 UPDATE: Get 'user' object to show name/email in sidebar
  const { logout, user } = useAuth();

  const [pendingChats, setPendingChats] = useState<AgentConversation[]>([]);
  const [activeChat, setActiveChat] = useState<AgentConversation | null>(null);
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [searchTerm, setSearchTerm] = useState("");

  // 1. Unified Fetch Function
  const fetchChats = async () => {
    const token = localStorage.getItem("token");

    if (!token) {
      console.error("No auth token found");
      return;
    }

    try {
      // Fetches "My Assigned Chats" + "Unassigned General Queue"
      const res = await fetch(`${API_BASE}/api/agent/pending_chats`, {
        headers: {
          "Authorization": `Bearer ${token}`
        }
      });

      if (res.status === 401) {
        console.error("Unauthorized - Token likely expired");
        return;
      }

      if (res.ok) {
        setPendingChats(await res.json());
      }
    } catch (e) {
      console.error("Fetch failed", e);
    }
  };

  // Poll for chats
  useEffect(() => {
    fetchChats();
    const interval = setInterval(fetchChats, 5000);
    return () => clearInterval(interval);
  }, []);

  // 2. Load a specific chat
  const handleLoadChat = async (chat: AgentConversation) => {
    setActiveChat(chat);
    setMessages([]);
    try {
      const res = await fetch(`${API_BASE}/api/conversations/${chat.id}/messages`);
      if (res.ok) setMessages(await res.json());
    } catch (e) { console.error(e); }
  };

  // 3. Join Chat
  const handleJoin = async () => {
    if (!activeChat) return;
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API_BASE}/api/agent/join_chat/${activeChat.id}`, {
        method: 'POST',
        headers: { "Authorization": `Bearer ${token}` }
      });

      if (res.ok) {
        const updatedChat = { ...activeChat, status: 'active_agent' };
        setActiveChat(updatedChat);
        fetchChats(); // Refresh list immediately
      }
    } catch (e) { console.error(e); }
  };

  // 4. Send Message
  const handleSendMessage = async (text: string) => {
    if (!activeChat) return;
    const token = localStorage.getItem("token");

    try {
      const res = await fetch(`${API_BASE}/api/agent/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ conversation_id: activeChat.id, message: text })
      });

      if (res.ok) {
        const data = await res.json();
        setMessages(prev => [...prev, {
          id: data.message_id,
          sender: 'agent',
          text: text,
          created_at: new Date().toISOString()
        }]);
      }
    } catch (e) { console.error(e); }
  };

  // 5. End Chat
  const handleEndChat = async () => {
    if (!activeChat) return;
    if (!window.confirm("End this session and return user to bot?")) return;
    const token = localStorage.getItem("token");

    try {
      const res = await fetch(`${API_BASE}/api/agent/end_chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ conversation_id: activeChat.id })
      });

      if (res.ok) {
        setActiveChat({ ...activeChat, status: 'active_bot' });
        fetchChats();
        alert("Session ended.");
      }
    } catch (e) { console.error(e); }
  };

  // Filter chats logic
  const filteredChats = pendingChats.filter(chat =>
    (chat.user_id || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
    chat.id.toString().includes(searchTerm)
  );

  return (
    <div className="flex h-screen bg-gray-50 font-sans overflow-hidden">
      <aside className="w-96 bg-white border-r border-gray-200 flex flex-col shadow-xl z-20">

        {/* Sidebar Header */}
        <div className="p-5 border-b border-gray-100">
          <div className="flex justify-between items-center mb-6">
            <h2 className="font-bold text-gray-800 text-xl flex items-center gap-2">
              <span className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center text-white shadow-md"><Inbox size={18} /></span>
              Agent Console
            </h2>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
            <input type="text" placeholder="Search ID or User..." className="w-full bg-gray-50 border border-gray-200 rounded-lg pl-10 pr-4 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none" value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} />
          </div>
        </div>

        {/* Chat List */}
        <div className="flex-1 overflow-y-auto">
          <div className="px-5 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider flex justify-between items-center">
            <span>Queue ({filteredChats.length})</span>
          </div>

          {filteredChats.length === 0 && (
            <div className="flex flex-col items-center justify-center pt-20 text-gray-400 opacity-60">
              <div className="bg-gray-100 p-4 rounded-full mb-3"><Inbox size={32} /></div>
              <p className="text-sm font-medium">No pending chats found</p>
            </div>
          )}

          <div className="space-y-1 px-3 pb-4">
            {filteredChats.map(chat => {
              const isActive = activeChat?.id === chat.id;
              const isWaiting = chat.status === 'waiting_for_agent';
              return (
                <div key={chat.id} onClick={() => handleLoadChat(chat)} className={`group p-4 rounded-xl cursor-pointer transition-all border border-transparent ${isActive ? 'bg-indigo-50 border-indigo-200 shadow-sm' : 'hover:bg-white hover:border-gray-200 hover:shadow-sm'}`}>
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${isWaiting ? 'bg-yellow-400 animate-pulse' : 'bg-green-500'}`}></span>
                      <span className={`font-bold text-sm ${isActive ? 'text-indigo-900' : 'text-gray-700'}`}>{chat.user_id || "Guest User"}</span>
                    </div>
                    <span className="text-[10px] text-gray-400 font-medium flex items-center gap-1"><Clock size={10} />{new Date(chat.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </div>
                  <div className="flex justify-between items-end">
                    <div className="flex flex-col gap-1">
                      <p className={`text-xs truncate max-w-[180px] ${isActive ? 'text-indigo-700' : 'text-gray-500'}`}>{chat.title}</p>
                      <span className="text-[10px] text-gray-400">ID: #{chat.id}</span>
                    </div>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold border ${isWaiting ? 'bg-yellow-50 text-yellow-700 border-yellow-200' : 'bg-green-50 text-green-700 border-green-200'}`}>{isWaiting ? 'WAITING' : 'ACTIVE'}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* 🟢 NEW: Dynamic Sidebar Footer */}
        <div className="p-4 bg-gray-50 border-t border-gray-200">
          <div className="flex items-center gap-3">
            {/* Avatar */}
            <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold text-xs border border-indigo-200">
              {user?.name ? user.name.charAt(0).toUpperCase() : "A"}
            </div>

            {/* Info */}
            <div className="flex flex-col overflow-hidden">
              <span className="text-sm font-bold text-gray-700 truncate">
                {user?.name || "Agent"}
              </span>
              <span className="text-[10px] text-gray-400 font-medium truncate" title={user?.email}>
                {user?.email || "Unknown Email"}
              </span>
            </div>
          </div>

          <button
            onClick={logout}
            className="mt-3 w-full flex items-center justify-center gap-2 text-xs font-bold text-red-500 hover:bg-red-50 py-2 rounded-lg transition-colors border border-transparent hover:border-red-100"
          >
            <LogOut size={12} />
            Sign Out
          </button>
        </div>

      </aside>

      <main className="flex-1 flex flex-col relative shadow-2xl z-10">
        <AgentEscalation activeChat={activeChat} messages={messages} onJoin={handleJoin} onSendMessage={handleSendMessage} onEndChat={handleEndChat} />
      </main>
    </div>
  );
};

export default AgentDashboard;