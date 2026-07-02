import type { RegistrationFormData } from "./types";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function submitRegistration(
  data: RegistrationFormData,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/users`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      name: data.fullName,
      occupation: data.occupation,
      monthly_income: Number(data.monthlyIncome),
    }),
  });

  if (!response.ok) {
    const fallbackMessage = "Failed to create profile. Please try again.";
    let message = fallbackMessage;
    try {
      const errorPayload = (await response.json()) as { message?: string };
      message = errorPayload.message || fallbackMessage;
    } catch {
      message = fallbackMessage;
    }
    throw new Error(message);
  }
}
