import { z } from "zod";

import { apiClient } from "@/lib/api/client";
import type { RegistrationFormData } from "@/types";

const userDataSchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  occupation: z.string(),
  monthly_income: z.number(),
  currency: z.string(),
  primary_financial_goal: z.string().nullable().optional(),
});

const userEnvelopeSchema = z.object({
  success: z.boolean(),
  message: z.string(),
  data: userDataSchema,
});

export async function submitRegistration(
  data: RegistrationFormData,
): Promise<z.infer<typeof userDataSchema>> {
  try {
    const response = await apiClient.post("/users", {
      name: data.fullName,
      occupation: data.occupation,
      monthly_income: Number(data.monthlyIncome),
      currency: data.currency,
      primary_financial_goal: data.primaryFinancialGoal,
    });

    const parsed = userEnvelopeSchema.parse(response.data);
    return parsed.data;
  } catch (error) {
    if (error instanceof z.ZodError) {
      throw new Error("Received an unexpected response from the server.");
    }

    throw error;
  }
}
