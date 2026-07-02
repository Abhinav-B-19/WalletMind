import type { RegistrationErrors, RegistrationFormData } from "./types";

export function validateRegistrationForm(
  data: RegistrationFormData,
): RegistrationErrors {
  const errors: RegistrationErrors = {};

  if (!data.fullName.trim()) {
    errors.fullName = "Full Name is required.";
  }

  if (!data.occupation.trim()) {
    errors.occupation = "Occupation is required.";
  }

  if (!data.monthlyIncome.trim()) {
    errors.monthlyIncome = "Monthly Income is required.";
  } else {
    const income = Number(data.monthlyIncome);
    if (Number.isNaN(income) || income <= 0) {
      errors.monthlyIncome = "Monthly Income must be greater than 0.";
    }
  }

  if (!data.currency) {
    errors.currency = "Please select a currency.";
  }

  if (!data.primaryFinancialGoal) {
    errors.primaryFinancialGoal = "Please select a primary financial goal.";
  }

  if (!data.termsAccepted) {
    errors.termsAccepted = "You must accept Terms & Conditions to continue.";
  }

  return errors;
}
