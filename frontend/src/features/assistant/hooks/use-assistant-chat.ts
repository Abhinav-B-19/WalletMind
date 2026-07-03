import { useMutation } from "@tanstack/react-query";

import { sendAssistantMessage } from "@/features/assistant/services/assistant-api";

export function useAssistantChat() {
  return useMutation({
    mutationKey: ["assistant", "chat"],
    mutationFn: sendAssistantMessage,
  });
}
