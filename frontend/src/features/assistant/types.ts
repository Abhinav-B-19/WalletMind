export type AssistantSource = {
  transaction_id: string;
  merchant: string;
  date: string;
  amount: number;
};

export type AssistantChatResponse = {
  answer: string;
  sources: AssistantSource[];
  confidence: number;
};

export type AssistantChatRequest = {
  statement_id: string;
  question: string;
};

export type ConversationRole = "user" | "assistant";

export type ConversationMessage = {
  id: string;
  role: ConversationRole;
  text: string;
  timestamp: string;
  confidence?: number;
  sources?: AssistantSource[];
};
