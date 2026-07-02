import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { PageWrapper } from "@/components/layout/page-wrapper";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { PageTitle, SectionTitle } from "@/components/ui/section-title";
import { Select } from "@/components/ui/select";
import { setStoredUser } from "@/lib/auth/storage";
import { submitRegistration } from "@/lib/api/users";
import type { RegistrationErrors, RegistrationFormData } from "@/types";
import { validateRegistrationForm } from "@/validation";

const CURRENCIES = ["USD", "EUR", "INR", "GBP", "CAD", "AUD"];
const FINANCIAL_GOALS = [
  "Build Emergency Fund",
  "Pay Off Debt",
  "Save for Home",
  "Retirement Planning",
  "Travel Fund",
];
const LANGUAGES = ["English", "Hindi", "Spanish", "French"];
const NOTIFICATION_OPTIONS = ["Email", "SMS", "Push Notifications", "None"];

const EMPTY_FORM: RegistrationFormData = {
  fullName: "",
  occupation: "",
  monthlyIncome: "",
  currency: "",
  primaryFinancialGoal: "",
  preferredLanguage: "",
  notificationPreference: "",
  termsAccepted: false,
};

export function RegistrationPage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState<RegistrationFormData>(EMPTY_FORM);
  const [errors, setErrors] = useState<RegistrationErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const canSubmit = useMemo(() => !isSubmitting, [isSubmitting]);

  const updateField = <K extends keyof RegistrationFormData>(
    key: K,
    value: RegistrationFormData[K],
  ) => {
    setFormData((previous) => ({ ...previous, [key]: value }));
    setErrors((previous) => ({ ...previous, [key]: undefined }));
    setSubmitError(null);
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const validationErrors = validateRegistrationForm(formData);
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) {
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const user = await submitRegistration(formData);
      setStoredUser(user);
      navigate("/app/home", { replace: true });
    } catch (error) {
      setSubmitError(
        error instanceof Error
          ? error.message
          : "Unable to create profile right now. Please try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <PageWrapper>
      <div className="space-y-6">
        <PageTitle
          title="Create Your WalletMind Profile"
          subtitle="Set up your profile to unlock personalized financial insights."
        />

        <Card>
          <CardHeader>
            <CardTitle>Registration</CardTitle>
            <CardDescription>
              Complete your details to continue to your WalletMind home.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-6" onSubmit={handleSubmit} noValidate>
              <section className="space-y-4">
                <SectionTitle
                  title="Personal Information"
                  subtitle="Tell us a little about you."
                />
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <label className="text-sm font-medium" htmlFor="fullName">
                      Full Name
                    </label>
                    <Input
                      id="fullName"
                      value={formData.fullName}
                      onChange={(event) =>
                        updateField("fullName", event.target.value)
                      }
                      placeholder="e.g., Priya Sharma"
                      aria-invalid={Boolean(errors.fullName)}
                    />
                    <p className="text-xs text-[var(--text-muted)]">
                      This will be used in your workspace greeting.
                    </p>
                    {errors.fullName ? (
                      <p className="text-xs text-[var(--danger)]">
                        {errors.fullName}
                      </p>
                    ) : null}
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium" htmlFor="occupation">
                      Occupation
                    </label>
                    <Input
                      id="occupation"
                      value={formData.occupation}
                      onChange={(event) =>
                        updateField("occupation", event.target.value)
                      }
                      placeholder="e.g., Product Manager"
                      aria-invalid={Boolean(errors.occupation)}
                    />
                    <p className="text-xs text-[var(--text-muted)]">
                      Helps WalletMind tailor recommendations.
                    </p>
                    {errors.occupation ? (
                      <p className="text-xs text-[var(--danger)]">
                        {errors.occupation}
                      </p>
                    ) : null}
                  </div>
                </div>
              </section>

              <section className="space-y-4">
                <SectionTitle
                  title="Financial Information"
                  subtitle="Core details for your first analysis profile."
                />
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <label
                      className="text-sm font-medium"
                      htmlFor="monthlyIncome"
                    >
                      Monthly Income
                    </label>
                    <Input
                      id="monthlyIncome"
                      type="number"
                      min="0"
                      step="0.01"
                      value={formData.monthlyIncome}
                      onChange={(event) =>
                        updateField("monthlyIncome", event.target.value)
                      }
                      placeholder="e.g., 4500"
                      aria-invalid={Boolean(errors.monthlyIncome)}
                    />
                    <p className="text-xs text-[var(--text-muted)]">
                      Enter your typical monthly post-tax income.
                    </p>
                    {errors.monthlyIncome ? (
                      <p className="text-xs text-[var(--danger)]">
                        {errors.monthlyIncome}
                      </p>
                    ) : null}
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium" htmlFor="currency">
                      Currency
                    </label>
                    <Select
                      id="currency"
                      value={formData.currency}
                      onChange={(event) =>
                        updateField("currency", event.target.value)
                      }
                      aria-invalid={Boolean(errors.currency)}
                    >
                      <option value="">Select currency</option>
                      {CURRENCIES.map((currency) => (
                        <option key={currency} value={currency}>
                          {currency}
                        </option>
                      ))}
                    </Select>
                    {errors.currency ? (
                      <p className="text-xs text-[var(--danger)]">
                        {errors.currency}
                      </p>
                    ) : null}
                  </div>

                  <div className="space-y-2 md:col-span-2">
                    <label
                      className="text-sm font-medium"
                      htmlFor="primaryGoal"
                    >
                      Primary Financial Goal
                    </label>
                    <Select
                      id="primaryGoal"
                      value={formData.primaryFinancialGoal}
                      onChange={(event) =>
                        updateField("primaryFinancialGoal", event.target.value)
                      }
                      aria-invalid={Boolean(errors.primaryFinancialGoal)}
                    >
                      <option value="">Select primary goal</option>
                      {FINANCIAL_GOALS.map((goal) => (
                        <option key={goal} value={goal}>
                          {goal}
                        </option>
                      ))}
                    </Select>
                    {errors.primaryFinancialGoal ? (
                      <p className="text-xs text-[var(--danger)]">
                        {errors.primaryFinancialGoal}
                      </p>
                    ) : null}
                  </div>
                </div>
              </section>

              <section className="space-y-4">
                <SectionTitle
                  title="Preferences"
                  subtitle="Optional settings for communication and language."
                />
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <label
                      className="text-sm font-medium"
                      htmlFor="preferredLanguage"
                    >
                      Preferred Language (optional)
                    </label>
                    <Select
                      id="preferredLanguage"
                      value={formData.preferredLanguage}
                      onChange={(event) =>
                        updateField("preferredLanguage", event.target.value)
                      }
                    >
                      <option value="">Select language</option>
                      {LANGUAGES.map((language) => (
                        <option key={language} value={language}>
                          {language}
                        </option>
                      ))}
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <label
                      className="text-sm font-medium"
                      htmlFor="notificationPreference"
                    >
                      Notification Preference (optional)
                    </label>
                    <Select
                      id="notificationPreference"
                      value={formData.notificationPreference}
                      onChange={(event) =>
                        updateField(
                          "notificationPreference",
                          event.target.value,
                        )
                      }
                    >
                      <option value="">Select preference</option>
                      {NOTIFICATION_OPTIONS.map((option) => (
                        <option key={option} value={option}>
                          {option}
                        </option>
                      ))}
                    </Select>
                  </div>
                </div>
              </section>

              <section className="space-y-3">
                <SectionTitle
                  title="Terms"
                  subtitle="Review and accept the onboarding agreement."
                />
                <label className="flex items-start gap-2 text-sm text-[var(--text-muted)]">
                  <input
                    type="checkbox"
                    className="mt-0.5"
                    checked={formData.termsAccepted}
                    onChange={(event) =>
                      updateField("termsAccepted", event.target.checked)
                    }
                  />
                  <span>
                    I agree to WalletMind Terms & Conditions and understand this
                    onboarding profile is stored locally for this release.
                  </span>
                </label>
                {errors.termsAccepted ? (
                  <p className="mt-1 text-xs text-[var(--danger)]">
                    {errors.termsAccepted}
                  </p>
                ) : null}
              </section>

              {submitError ? (
                <p className="text-sm text-[var(--danger)]">{submitError}</p>
              ) : null}

              <div className="flex flex-wrap items-center gap-3">
                <Button type="submit" disabled={!canSubmit}>
                  {isSubmitting ? "Creating Profile..." : "Create Profile"}
                </Button>
                <Button asChild variant="secondary" type="button">
                  <Link to="/login">Already have a profile?</Link>
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </PageWrapper>
  );
}
