export type Sender = "user" | "bot";

export interface ChatMessage {
    id: number;
    sender: Sender;
    text: string;
}

export interface ChatPayload {
    need_order_number?: boolean;
    order?: {
        order_number: string;
        status: string;
        estimated_delivery?: string | null;
    };
    [key: string]: any;
}

export interface ChatApiResponse {
    conversation_id: number;
    reply: string;
    intent: string;
    entities: Record<string, any>;
    quick_replies: string[];
    payload: ChatPayload;
}

export interface ChatWidgetProps {
    userIdentifier?: string | null; // e.g. customer email
}