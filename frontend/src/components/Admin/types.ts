// --- frontend/src/components/Admin/types.ts ---
export const ACCESS_KEYS = ["can_view_chats", "can_reply", "can_close_chat"] as const;
export type AccessKey = typeof ACCESS_KEYS[number];

export interface User {
  id: number;
  name: string;
  email: string;
  role: "admin" | "agent" | "customer";
  status: string;
  access: Record<AccessKey, boolean>;
}

export interface ChatLog {
  id: number;
  timestamp: string;
  actor_id: string;
  actor_email: string;
  user_message: string;
  bot_response: string;
  intent: string;
  confidence: number;
  response_time_ms: number;
  is_escalated: boolean;
  conversation_id?: number;
}

export interface PerformanceReport {
  total_conversations: number;
  average_accuracy: number;
  average_response_time_ms: number;
  escalation_rate: string;
  escalation_count: number;
}