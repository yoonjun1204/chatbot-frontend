// --- frontend/src/components/Customer/ChatWidget.tsx ---
import React, { useState, useEffect, useRef } from "react";
import type { FormEvent } from "react";
import { type Sender, type ChatMessage, type ChatApiResponse, type ChatWidgetProps, type ConversationHistory, type ChatStatus } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const ChatWidget: React.FC<ChatWidgetProps> = ({ userIdentifier }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const [chatStatus, setChatStatus] = useState<ChatStatus>("active_bot");
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [history, setHistory] = useState<ConversationHistory[]>([]);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [quickReplies, setQuickReplies] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [editingMessageId, setEditingMessageId] = useState<number | null>(null);
  const [editText, setEditText] = useState("");
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // --- Fetch History List ---
  const fetchHistory = async () => {
    if (!userIdentifier || userIdentifier === "anonymous") return;
    try {
      const res = await fetch(`${API_BASE}/api/customer/conversations?user_email=${userIdentifier}`);
      if (res.ok) {
        const data = await res.json();
        setHistory(data);
      }
    } catch (err) {
      console.error("Failed to fetch history", err);
    }
  };

  // --- Load Specific Conversation ---
  const loadConversation = async (id: number) => {
    setLoading(true);
    setConversationId(id);
    setIsSidebarOpen(false);

    const selectedChat = history.find(c => c.id === id);
    if (selectedChat?.status) {
      setChatStatus(selectedChat.status);
    } else {
      setChatStatus("active_bot");
    }

    try {
      const res = await fetch(`${API_BASE}/api/conversations/${id}/messages`);
      if (res.ok) {
        const data = await res.json();
        setMessages(data.map((m: any) => ({
          id: m.id,
          sender: m.sender,
          text: m.text
        })));

        if (!selectedChat?.status || selectedChat.status === 'active_bot') {
          setQuickReplies(["Ask about shirts", "Check order status", "Return / exchange policy"]);
        } else {
          setQuickReplies([]);
        }
      }
    } catch (err) {
      console.error("Error loading chat", err);
    } finally {
      setLoading(false);
    }
  };

  const deleteChat = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    if (!window.confirm("Delete this chat?")) return;
    try {
      const res = await fetch(`${API_BASE}/api/customer/conversations/${id}`, { method: "DELETE" });
      if (res.ok) {
        setHistory((prev) => prev.filter((chat) => chat.id !== id));
        if (conversationId === id) startNewChat();
      }
    } catch (err) {
      console.error("Delete failed", err);
    }
  };

  // --- Start New Chat ---
  const startNewChat = () => {
    setConversationId(null);
    setMessages([]);
    resetToGreeting();
    setIsSidebarOpen(false);
    setChatStatus("active_bot");
  };

  // --- 🟢 FIXED: Handle Escalation (Talk to Human) ---
  const handleEscalate = async () => {
    if (!conversationId) {
      alert("Please start a conversation first.");
      return;
    }

    if (chatStatus !== "active_bot") return;

    if (!window.confirm("Do you want to speak to a human agent?")) return;

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/customer/escalate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          conversation_id: conversationId,
          message: "Requesting human agent...",
          user_id: userIdentifier
        }),
      });

      const data = await res.json();

      // 🛑 CRITICAL FIX: Check if server rejected the request
      if (data.message === "Limit Reached" || data.message === "Already connected") {
        alert(data.reply); // Show error to user
        setLoading(false);
        // DO NOT CHANGE STATUS to 'waiting_for_agent'
        return;
      }

      // Only if successful:
      if (res.ok) {
        addMessage("bot", data.reply || "Connecting you to an agent...");
        setChatStatus("waiting_for_agent");
        setHistory(prev => prev.map(c => c.id === conversationId ? { ...c, status: "waiting_for_agent" } : c));
      } else {
        alert("Failed to connect to agent.");
      }
    } catch (err) {
      console.error("Escalation failed", err);
    } finally {
      setLoading(false);
    }
  };

  const addMessage = (sender: Sender, text: string) => {
    setMessages((prev) => [...prev, { id: Date.now() + Math.random(), sender, text }]);
  };

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  };

  useEffect(() => { scrollToBottom(); }, [messages, loading]);

  useEffect(() => { if (isOpen) fetchHistory(); }, [isOpen, userIdentifier]);

  useEffect(() => {
    if (isOpen && !conversationId && messages.length === 0) {
      resetToGreeting();
    }
  }, [isOpen, conversationId]);

  const sendMessage = async (text: string) => {
    if (!text.trim()) return;

    const tempUserMsgId = Date.now();
    setMessages((prev) => [...prev, { id: tempUserMsgId, sender: "user", text }]);
    setInput("");
    setLoading(true);
    setQuickReplies([]);

    try {
      const res = await fetch(`${API_BASE}/api/customer/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          conversation_id: conversationId,
          user_id: userIdentifier || "anonymous",
        }),
      });

      if (!res.ok) throw new Error("API error");

      const data: ChatApiResponse = await res.json();

      if (!conversationId) {
        setConversationId(data.conversation_id);
        fetchHistory();
      }

      setMessages((prev) => {
        const withoutTemp = prev.filter((m) => m.id !== tempUserMsgId);
        return [
          ...withoutTemp,
          { id: data.user_message_id || Date.now(), sender: "user", text },
          ...(data.reply ? [{ id: data.bot_message_id || Date.now() + 1, sender: "bot" as Sender, text: data.reply }] : [])
        ];
      });

      setQuickReplies(data.quick_replies || []);
    } catch (err) {
      console.error(err);
      addMessage("bot", "Sorry, something went wrong while talking to the server.");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: FormEvent) => { e.preventDefault(); sendMessage(input); };

  const INITIAL_GREETING = "Hi! 👋 I'm your shirt support chatbot. I can help with product info, order status, and returns.";
  const INITIAL_QUICK_REPLIES = ["Ask about shirts", "Check order status", "Return / exchange policy"];

  const resetToGreeting = () => {
    setMessages([{ id: Date.now(), sender: "bot", text: INITIAL_GREETING }]);
    setQuickReplies(INITIAL_QUICK_REPLIES);
  };

  const handleEditSubmit = async (messageId: number) => {
    if (!editText.trim()) return;
    setLoading(true);
    setEditingMessageId(null);

    try {
      const res = await fetch(`${API_BASE}/api/customer/message/${messageId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: editText, user_id: userIdentifier, conversation_id: conversationId }),
      });

      if (res.ok) {
        const data: ChatApiResponse = await res.json();
        setMessages((prev) => {
          const index = prev.findIndex(m => m.id === messageId);
          const updatedUserMsg = { ...prev[index], text: editText };
          const newBotMsg = { id: Date.now(), sender: "bot" as Sender, text: data.reply };
          return [...prev.slice(0, index), updatedUserMsg, newBotMsg];
        });
        setQuickReplies(data.quick_replies || []);
      }
    } catch (err) {
      console.error("Edit failed", err);
    } finally {
      setLoading(false);
    }
  };

  const handleEndChat = async () => {
    if (!conversationId) return;
    if (!window.confirm("Disconnect from human support?")) return;

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/customer/end_chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ conversation_id: conversationId, user_id: userIdentifier }),
      });

      if (res.ok) {
        const data = await res.json();
        addMessage("bot", data.reply || "Session ended.");
        setChatStatus("active_bot");
        setHistory(prev => prev.map(c => c.id === conversationId ? { ...c, status: "active_bot" } : c));
      }
    } catch (err) {
      console.error("End chat failed", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {!isOpen && (
        <button
          className="fixed bottom-6 right-6 w-14 h-14 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-2xl flex items-center justify-center text-2xl transition-transform hover:scale-110 active:scale-95"
          onClick={() => { setIsOpen(true); fetchHistory(); }}
        >
          💬
        </button>
      )}

      {isOpen && (
        <div className="fixed inset-0 md:inset-auto md:bottom-6 md:right-6 md:w-[850px] md:h-[600px] bg-white md:rounded-2xl shadow-2xl flex overflow-hidden border border-gray-200 z-50">
          <aside className={`${isSidebarOpen ? 'w-64' : 'w-0'} md:w-64 bg-gray-50 border-r border-gray-200 flex flex-col transition-all duration-300 ease-in-out overflow-hidden`}>
            <div className="p-4">
              <button onClick={startNewChat} className="w-full py-3 px-4 bg-white border border-gray-300 rounded-xl text-gray-700 font-medium hover:bg-blue-50 hover:border-blue-200 flex items-center gap-2 transition-colors">
                <span className="text-xl">+</span> New Chat
              </button>
            </div>
            <div className="flex-1 overflow-y-auto px-2 pb-4">
              <p className="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Recent</p>
              {history.map((chat) => (
                <div key={chat.id} className="group relative">
                  <button onClick={() => loadConversation(chat.id)} className={`w-full text-left px-3 py-2 pr-10 rounded-lg text-sm truncate transition-colors ${conversationId === chat.id ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-200'}`}>
                    <div className="font-medium truncate">💬 {chat.title}</div>
                    <div className="text-[10px] text-gray-400 mt-0.5">
                      {chat.status === 'waiting_for_agent' && '⏳ Waiting'}
                      {chat.status === 'active_agent' && '👤 Agent'}
                    </div>
                  </button>
                  <button onClick={(e) => deleteChat(e, chat.id)} className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 transition-all" title="Delete chat">🗑️</button>
                </div>
              ))}
            </div>
          </aside>

          <div className="flex-1 flex flex-col bg-white">
            <header className="px-4 py-3 border-b border-gray-200 flex items-center justify-between bg-white">
              <div className="flex items-center gap-3">
                <button className="md:hidden p-1 hover:bg-gray-100 rounded" onClick={() => setIsSidebarOpen(!isSidebarOpen)}>☰</button>
                <div>
                  <h3 className="font-bold text-gray-800 flex items-center gap-2">
                    Shirt Support
                    {chatStatus === "active_agent" && <span className="text-[10px] bg-green-100 text-green-800 px-2 py-0.5 rounded-full border border-green-200">Human Connected</span>}
                  </h3>
                  <p className="text-xs text-green-500 flex items-center gap-1"><span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>{userIdentifier || "Guest"}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {chatStatus === "active_bot" ? (
                  <button onClick={handleEscalate} className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-full transition-colors" title="Talk to a Human">🎧</button>
                ) : (
                  <button onClick={handleEndChat} className="p-2 text-red-500 hover:bg-red-50 rounded-full transition-colors border border-red-100" title="End Human Chat">❌</button>
                )}
                <button onClick={() => setIsOpen(false)} className="text-gray-400 hover:text-gray-600 text-xl p-1">✕</button>
              </div>
            </header>

            <main className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-gray-200">
              {messages.length === 0 && !loading && (
                <div className="h-full flex flex-col items-center justify-center text-gray-400 space-y-2">
                  <div className="text-4xl">👕</div>
                  <p className="font-medium text-lg">How can I help you today?</p>
                </div>
              )}

              {messages.map((m) => (
                <div key={m.id} className={`flex group ${m.sender === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`relative max-w-[80%] px-4 py-2 rounded-2xl shadow-sm text-sm ${m.sender === "user" ? "bg-blue-600 text-white rounded-br-none" : (m.sender === "agent" ? "bg-green-50 text-green-900 border border-green-200 rounded-bl-none" : "bg-gray-100 text-gray-800 rounded-bl-none border border-gray-200")}`}>
                    {editingMessageId === m.id ? (
                      <div className="flex flex-col gap-2">
                        <textarea className="bg-white text-gray-800 p-2 rounded-lg outline-none border-none text-sm w-full min-w-[200px]" value={editText} onChange={(e) => setEditText(e.target.value)} />
                        <div className="flex justify-end gap-2">
                          <button onClick={() => setEditingMessageId(null)} className="text-[10px] uppercase font-bold opacity-70">Cancel</button>
                          <button onClick={() => handleEditSubmit(m.id)} className="text-[10px] uppercase font-bold">Save & Submit</button>
                        </div>
                      </div>
                    ) : (
                      <>
                        {m.text}
                        {m.sender === 'agent' && <div className="text-[10px] uppercase font-bold text-green-700 mt-1 border-t border-green-200 pt-1">Support Agent</div>}
                        {m.sender === "user" && (
                          <button onClick={() => { setEditingMessageId(m.id); setEditText(m.text); }} className="absolute -left-8 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity p-1 text-gray-400 hover:text-blue-500">✎</button>
                        )}
                      </>
                    )}
                  </div>
                </div>
              ))}

              {loading && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 border border-gray-200 text-gray-500 px-4 py-2 rounded-2xl rounded-bl-none text-sm animate-pulse">AI is thinking...</div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </main>

            <footer className="p-4 border-t border-gray-200 bg-gray-50/50">
              <div className="flex gap-2 mb-3 overflow-x-auto pb-1 no-scrollbar">
                {quickReplies.map((q, idx) => (
                  <button key={idx} onClick={() => sendMessage(q)} className="whitespace-nowrap px-3 py-1 bg-white border border-gray-300 rounded-full text-xs text-gray-600 hover:border-blue-500 hover:text-blue-500 transition-colors shadow-sm">{q}</button>
                ))}
              </div>
              <form className="flex gap-2" onSubmit={handleSubmit}>
                <input className="flex-1 px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none shadow-sm" placeholder="Ask about your order..." value={input} onChange={(e) => setInput(e.target.value)} />
                <button type="submit" disabled={loading || !input.trim()} className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white px-5 py-2 rounded-xl font-medium transition-colors shadow-md">Send</button>
              </form>
            </footer>
          </div>
        </div>
      )}
    </>
  );
};
export default ChatWidget;