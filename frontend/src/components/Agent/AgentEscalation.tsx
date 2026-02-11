// frontend/src/components/Agent/AgentEscalation.tsx
import React, { useEffect, useRef, useState } from 'react';
import type { AgentConversation, AgentMessage } from './types';
import { Send, User, Bot, MessageSquare, Clock, UserCheck } from 'lucide-react';

interface AgentEscalationProps {
    activeChat: AgentConversation | null;
    messages: AgentMessage[];
    onJoin: () => void;
    onSendMessage: (message: string) => void;
    onEndChat: () => void;
}

const AgentEscalation: React.FC<AgentEscalationProps> = ({
    activeChat,
    messages,
    onJoin,
    onSendMessage,
    onEndChat
}) => {
    const [reply, setReply] = useState("");
    const scrollRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom when messages change
    useEffect(() => {
        scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!reply.trim()) return;
        onSendMessage(reply);
        setReply(""); // Clear input
    };

    const formatTime = (dateString: string) => {
        if (!dateString) return "";
        // If the string doesn't end with Z, add it to force UTC conversion
        const utcString = dateString.endsWith("Z") ? dateString : `${dateString}Z`;
        return new Date(utcString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    if (!activeChat) {
        return (
            <div className="flex-1 flex flex-col items-center justify-center bg-gray-50 text-gray-400 h-full">
                <div className="bg-white p-8 rounded-2xl shadow-sm text-center max-w-md">
                    <div className="w-20 h-20 bg-indigo-50 text-indigo-500 rounded-full flex items-center justify-center mx-auto mb-6">
                        <MessageSquare size={40} />
                    </div>
                    <h3 className="text-xl font-bold text-gray-800 mb-2">No Chat Selected</h3>
                    <p className="text-gray-500">Select a conversation from the queue on the left to start viewing or chatting.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="flex-1 flex flex-col h-full bg-white relative">
            {/* HEADER */}
            <header className="px-6 py-4 bg-white border-b border-gray-100 flex justify-between items-center sticky top-0 z-10">
                <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center text-gray-500 font-bold text-xl">
                        {activeChat.user_id ? activeChat.user_id.charAt(0).toUpperCase() : <User size={24} />}
                    </div>
                    <div>
                        <h1 className="font-bold text-gray-800 text-lg flex items-center gap-2">
                            {activeChat.user_id || 'Guest User'}
                        </h1>
                        <div className="flex items-center gap-3 text-xs text-gray-500">
                            <span className="flex items-center gap-1 bg-gray-100 px-2 py-0.5 rounded-full">
                                ID: #{activeChat.id}
                            </span>
                            <span className={`flex items-center gap-1 px-2 py-0.5 rounded-full border ${activeChat.status === 'active_agent' ? 'bg-green-50 text-green-700 border-green-100' : 'bg-yellow-50 text-yellow-700 border-yellow-100'}`}>
                                {activeChat.status === 'active_agent' ? 'Active Session' : 'Waiting for Agent'}
                            </span>
                        </div>
                    </div>
                </div>

                {/* JOIN BUTTON */}
                {activeChat.status === 'waiting_for_agent' && (
                    <button
                        onClick={onJoin}
                        className="group flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 rounded-lg shadow-md hover:shadow-lg transition-all font-medium"
                    >
                        <UserCheck size={18} className="group-hover:scale-110 transition-transform" />
                        Accept Chat
                    </button>
                )}

                {/* 🆕 END CHAT BUTTON (Only if Active) */}
                {activeChat.status === 'active_agent' && (
                    <button
                        onClick={onEndChat}
                        className="bg-red-50 text-red-600 hover:bg-red-100 border border-red-200 px-4 py-2 rounded-lg font-bold transition-colors text-sm flex items-center gap-2"
                    >
                        End Session
                    </button>
                )}
            </header>

            {/* MESSAGES AREA */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-gray-50 scrollbar-thin scrollbar-thumb-gray-200">
                {messages.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full text-gray-400 opacity-60">
                        <Clock size={48} className="mb-2" />
                        <p className="text-sm">Loading message history...</p>
                    </div>
                )}

                {messages.map((m, idx) => {
                    const isAgent = m.sender === 'agent';
                    const isBot = m.sender === 'bot';

                    return (
                        <div key={m.id || idx} className={`flex w-full ${isAgent ? 'justify-end' : 'justify-start'}`}>
                            <div className={`flex max-w-[75%] gap-3 ${isAgent ? 'flex-row-reverse' : 'flex-row'}`}>

                                {/* Avatar */}
                                <div className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-white text-xs mt-1 ${isAgent ? 'bg-indigo-600' : (isBot ? 'bg-gray-400' : 'bg-blue-500')}`}>
                                    {isAgent ? <UserCheck size={14} /> : (isBot ? <Bot size={14} /> : <User size={14} />)}
                                </div>

                                {/* Bubble */}
                                <div className={`group relative p-3.5 rounded-2xl shadow-sm text-sm leading-relaxed ${isAgent
                                    ? 'bg-indigo-600 text-white rounded-tr-none'
                                    : (isBot ? 'bg-gray-200 text-gray-700 rounded-tl-none border border-gray-300' : 'bg-white text-gray-800 border border-gray-200 rounded-tl-none')
                                    }`}>
                                    {m.text}
                                    <div className={`text-[10px] mt-1.5 opacity-70 font-medium flex items-center gap-1 ${isAgent ? 'text-indigo-100 justify-end' : 'text-gray-400'}`}>
                                        {m.sender.toUpperCase()} • {formatTime(m.created_at)}
                                    </div>
                                </div>
                            </div>
                        </div>
                    );
                })}
                <div ref={scrollRef} />
            </div>

            {/* INPUT AREA */}
            <footer className="p-5 bg-white border-t border-gray-100">
                <form onSubmit={handleSubmit} className="flex gap-3 items-end">
                    <div className="flex-1 relative">
                        <input
                            disabled={activeChat.status !== 'active_agent'}
                            className="w-full bg-gray-50 border border-gray-200 text-gray-800 p-4 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all disabled:bg-gray-100 disabled:cursor-not-allowed placeholder-gray-400"
                            placeholder={activeChat.status === 'active_agent' ? "Type your reply..." : "Join the chat to reply"}
                            value={reply}
                            onChange={e => setReply(e.target.value)}
                        />
                    </div>
                    <button
                        type="submit"
                        disabled={activeChat.status !== 'active_agent' || !reply.trim()}
                        className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white p-4 rounded-xl shadow-md transition-all flex items-center justify-center"
                    >
                        <Send size={20} />
                    </button>
                </form>
            </footer>
        </div>
    );
};

export default AgentEscalation;