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