import { FormEvent, useMemo, useState } from "react";

import { submitRegistration } from "./api";
import type { RegistrationErrors, RegistrationFormData } from "./types";
import { validateRegistrationForm } from "./validation";

const CURRENCIES = ["USD", "EUR", "INR", "GBP", "CAD", "AUD"];
const FINANCIAL_GOALS = [
  "Build Emergency Fund",
  "Pay Off Debt",
  "Save for Home",
  "Retirement Planning",
  "Travel Fund",
];

const EMPTY_FORM: RegistrationFormData = {
  fullName: "",
  occupation: "",
  monthlyIncome: "",
  currency: "",
  primaryFinancialGoal: "",
};

export default function App() {
  const [formData, setFormData] = useState<RegistrationFormData>(EMPTY_FORM);
  const [errors, setErrors] = useState<RegistrationErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSuccess, setIsSuccess] = useState(false);

  const canSubmit = useMemo(() => !isSubmitting, [isSubmitting]);

  const handleInputChange = (
    key: keyof RegistrationFormData,
    value: string,
  ) => {
    setFormData((previous) => ({ ...previous, [key]: value }));
    setErrors((previous) => ({ ...previous, [key]: undefined }));
    setSubmitError(null);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const nextErrors = validateRegistrationForm(formData);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) {
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      await submitRegistration(formData);
      setIsSuccess(true);
    } catch (error) {
      setSubmitError(
        error instanceof Error ? error.message : "Something went wrong.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="page-shell">
      <main className="registration-card" aria-live="polite">
        <header className="brand-header">
          <div className="logo-mark" aria-hidden="true">
            WM
          </div>
          <div>
            <h1>WalletMind</h1>
            <p>Set up your profile to start your smart money journey.</p>
          </div>
        </header>

        {!isSuccess ? (
          <form
            className="registration-form"
            onSubmit={handleSubmit}
            noValidate
          >
            <label>
              Full Name
              <input
                name="fullName"
                value={formData.fullName}
                onChange={(event) =>
                  handleInputChange("fullName", event.target.value)
                }
                placeholder="e.g., Priya Sharma"
                aria-invalid={Boolean(errors.fullName)}
              />
              {errors.fullName ? (
                <span className="field-error">{errors.fullName}</span>
              ) : null}
            </label>

            <label>
              Occupation
              <input
                name="occupation"
                value={formData.occupation}
                onChange={(event) =>
                  handleInputChange("occupation", event.target.value)
                }
                placeholder="e.g., Product Manager"
                aria-invalid={Boolean(errors.occupation)}
              />
              {errors.occupation ? (
                <span className="field-error">{errors.occupation}</span>
              ) : null}
            </label>

            <label>
              Monthly Income
              <input
                type="number"
                name="monthlyIncome"
                min="0"
                step="0.01"
                value={formData.monthlyIncome}
                onChange={(event) =>
                  handleInputChange("monthlyIncome", event.target.value)
                }
                placeholder="e.g., 4500"
                aria-invalid={Boolean(errors.monthlyIncome)}
              />
              {errors.monthlyIncome ? (
                <span className="field-error">{errors.monthlyIncome}</span>
              ) : null}
            </label>

            <label>
              Currency
              <select
                name="currency"
                value={formData.currency}
                onChange={(event) =>
                  handleInputChange("currency", event.target.value)
                }
                aria-invalid={Boolean(errors.currency)}
              >
                <option value="">Select currency</option>
                {CURRENCIES.map((currency) => (
                  <option key={currency} value={currency}>
                    {currency}
                  </option>
                ))}
              </select>
              {errors.currency ? (
                <span className="field-error">{errors.currency}</span>
              ) : null}
            </label>

            <label>
              Primary Financial Goal
              <select
                name="primaryFinancialGoal"
                value={formData.primaryFinancialGoal}
                onChange={(event) =>
                  handleInputChange("primaryFinancialGoal", event.target.value)
                }
                aria-invalid={Boolean(errors.primaryFinancialGoal)}
              >
                <option value="">Select your primary goal</option>
                {FINANCIAL_GOALS.map((goal) => (
                  <option key={goal} value={goal}>
                    {goal}
                  </option>
                ))}
              </select>
              {errors.primaryFinancialGoal ? (
                <span className="field-error">
                  {errors.primaryFinancialGoal}
                </span>
              ) : null}
            </label>

            {submitError ? <p className="submit-error">{submitError}</p> : null}

            <button
              className="submit-button"
              type="submit"
              disabled={!canSubmit}
            >
              {isSubmitting ? "Creating Profile..." : "Create Profile"}
            </button>
          </form>
        ) : (
          <section className="success-panel">
            <p className="success-title">✓ Profile Created Successfully</p>
            <p className="success-subtitle">
              Ready to Upload Your First Bank Statement
            </p>
            <button type="button" className="continue-button">
              Continue
            </button>
          </section>
        )}
      </main>
    </div>
  );
}
