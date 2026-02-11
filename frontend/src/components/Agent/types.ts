// --- frontend/src/components/Agent/types.ts ---
export type AgentConversation = {
    id: number;
    title: string;
    status: string;
    user_id: string;
    updated_at: string;
};

export type AgentMessage = {
    id: number;
    sender: string;
    text: string;
    created_at: string;
};
