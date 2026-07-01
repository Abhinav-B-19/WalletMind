import { describe, expect, it } from "vitest";

import { validateRegistrationForm } from "./validation";

describe("validateRegistrationForm", () => {
  it("returns errors for empty required fields", () => {
    const result = validateRegistrationForm({
      fullName: "",
      occupation: "",
      monthlyIncome: "",
      currency: "",
      primaryFinancialGoal: ""
    });

    expect(result.fullName).toBe("Full Name is required.");
    expect(result.occupation).toBe("Occupation is required.");
    expect(result.monthlyIncome).toBe("Monthly Income is required.");
    expect(result.currency).toBe("Please select a currency.");
    expect(result.primaryFinancialGoal).toBe("Please select a primary financial goal.");
  });

  it("returns error when monthly income is zero or invalid", () => {
    const zeroResult = validateRegistrationForm({
      fullName: "Priya",
      occupation: "Engineer",
      monthlyIncome: "0",
      currency: "USD",
      primaryFinancialGoal: "Build Emergency Fund"
    });

    const invalidResult = validateRegistrationForm({
      fullName: "Priya",
      occupation: "Engineer",
      monthlyIncome: "abc",
      currency: "USD",
      primaryFinancialGoal: "Build Emergency Fund"
    });

    expect(zeroResult.monthlyIncome).toBe("Monthly Income must be greater than 0.");
    expect(invalidResult.monthlyIncome).toBe("Monthly Income must be greater than 0.");
  });

  it("returns no errors for valid input", () => {
    const result = validateRegistrationForm({
      fullName: "Priya Sharma",
      occupation: "Product Manager",
      monthlyIncome: "7500",
      currency: "USD",
      primaryFinancialGoal: "Retirement Planning"
    });

    expect(result).toEqual({});
  });
});
