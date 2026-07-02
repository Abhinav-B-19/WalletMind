export type RegistrationFormData = {
  fullName: string;
  occupation: string;
  monthlyIncome: string;
  currency: string;
  primaryFinancialGoal: string;
};

export type RegistrationErrors = Partial<
  Record<keyof RegistrationFormData, string>
>;
