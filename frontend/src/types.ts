export type RegistrationFormData = {
  fullName: string;
  occupation: string;
  monthlyIncome: string;
  currency: string;
  primaryFinancialGoal: string;
  preferredLanguage: string;
  notificationPreference: string;
  termsAccepted: boolean;
};

export type RegistrationErrors = Partial<
  Record<keyof RegistrationFormData, string>
>;
