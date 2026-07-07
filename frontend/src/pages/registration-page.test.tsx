import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { RegistrationPage } from "@/pages/registration-page";
import { USER_STORAGE_KEY } from "@/lib/auth/storage";

const navigateMock = vi.fn();
const submitRegistrationMock = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual =
    await vi.importActual<typeof import("react-router-dom")>(
      "react-router-dom",
    );

  return {
    ...actual,
    Link: ({ children, to }: { children: React.ReactNode; to: string }) => (
      <a href={to}>{children}</a>
    ),
    useNavigate: () => navigateMock,
    useLocation: () => ({ state: null }),
  };
});

vi.mock("@/lib/api/users", () => ({
  submitRegistration: (...args: unknown[]) => submitRegistrationMock(...args),
}));

describe("RegistrationPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it("stores complete returned user object in localStorage", async () => {
    submitRegistrationMock.mockResolvedValue({
      id: "f7ed2559-7ec3-4433-b9e4-af8ca6adf72b",
      name: "Priya Sharma",
      occupation: "Engineer",
      monthly_income: 120000,
      currency: "INR",
      primary_financial_goal: "Build Emergency Fund",
    });

    render(<RegistrationPage />);

    fireEvent.change(screen.getByLabelText("Full Name"), {
      target: { value: "Priya Sharma" },
    });
    fireEvent.change(screen.getByLabelText("Occupation"), {
      target: { value: "Engineer" },
    });
    fireEvent.change(screen.getByLabelText("Monthly Income"), {
      target: { value: "120000" },
    });
    fireEvent.change(screen.getByLabelText("Currency"), {
      target: { value: "INR" },
    });
    fireEvent.change(screen.getByLabelText("Primary Financial Goal"), {
      target: { value: "Build Emergency Fund" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Create Profile" }));

    await waitFor(() => {
      expect(submitRegistrationMock).toHaveBeenCalledWith({
        fullName: "Priya Sharma",
        occupation: "Engineer",
        monthlyIncome: "120000",
        currency: "INR",
        primaryFinancialGoal: "Build Emergency Fund",
      });
    });

    const raw = localStorage.getItem(USER_STORAGE_KEY);
    expect(raw).not.toBeNull();
    expect(JSON.parse(raw as string)).toEqual({
      id: "f7ed2559-7ec3-4433-b9e4-af8ca6adf72b",
      name: "Priya Sharma",
      occupation: "Engineer",
      monthly_income: 120000,
      currency: "INR",
      primary_financial_goal: "Build Emergency Fund",
    });
    expect(navigateMock).toHaveBeenCalledWith("/app/home", { replace: true });
  });
});
