import { z } from "zod";

import { apiClient } from "@/lib/api/client";

export const executionModeSchema = z.enum(["single", "multi"]);

export type AgentExecutionMode = z.infer<typeof executionModeSchema>;

export type ExecuteAgentsPayload = {
  query: string;
  user_id: string;
  session_id: string;
  user_uuid?: string;
  inputs: {
    statement_uuid: string;
    execution_mode: "single_agent" | "multi_agent";
  };
};

const executeAgentsEnvelopeSchema = z.object({
  success: z.boolean(),
  message: z.string(),
  data: z.unknown(),
});

export type ExecuteAgentsResponseEnvelope = z.infer<
  typeof executeAgentsEnvelopeSchema
>;

export async function executeAgents(
  payload: ExecuteAgentsPayload,
): Promise<ExecuteAgentsResponseEnvelope> {
  const response = await apiClient.post("/agents/execute", payload);
  return executeAgentsEnvelopeSchema.parse(response.data);
}
