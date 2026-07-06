import { describe, expect, it, vi, beforeEach } from "vitest";

import { listUsers, submitRegistration } from "@/lib/api/users";
import { apiClient } from "@/lib/api/client";

vi.mock("@/lib/api/client", () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

describe("submitRegistration", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("sends currency and primary_financial_goal", async () => {
    const postMock = vi.mocked(apiClient.post);
    postMock.mockResolvedValue({
      data: {
        success: true,
        message: "User created successfully.",
        data: {
          id: "f7ed2559-7ec3-4433-b9e4-af8ca6adf72b",
          name: "Priya Sharma",
          occupation: "Engineer",
          monthly_income: 120000,
          currency: "INR",
          primary_financial_goal: "Build Emergency Fund",
        },
      },
    });

    await submitRegistration({
      fullName: "Priya Sharma",
      occupation: "Engineer",
      monthlyIncome: "120000",
      currency: "INR",
      primaryFinancialGoal: "Build Emergency Fund",
    });

    expect(postMock).toHaveBeenCalledWith("/users", {
      name: "Priya Sharma",
      occupation: "Engineer",
      monthly_income: 120000,
      currency: "INR",
      primary_financial_goal: "Build Emergency Fund",
    });
  });
});

describe("listUsers", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("loads users from GET /users", async () => {
    const getMock = vi.mocked(apiClient.get);
    getMock.mockResolvedValue({
      data: {
        success: true,
        message: "Users retrieved successfully.",
        data: [
          {
            id: "f7ed2559-7ec3-4433-b9e4-af8ca6adf72b",
            name: "Priya Sharma",
            occupation: "Engineer",
            monthly_income: 120000,
            currency: "INR",
            primary_financial_goal: "Build Emergency Fund",
            email: null,
            created_at: "2026-07-07T00:00:00.000Z",
            updated_at: "2026-07-07T00:00:00.000Z",
          },
        ],
      },
    });

    const users = await listUsers();

    expect(getMock).toHaveBeenCalledWith("/users");
    expect(users).toHaveLength(1);
    expect(users[0]?.name).toBe("Priya Sharma");
  });
});
