import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  REMEMBERED_PROFILES_STORAGE_KEY,
  USER_STORAGE_KEY,
} from "@/lib/auth/storage";
import { LoginPage } from "@/pages/login-page";

const navigateMock = vi.fn();
const listUsersMock = vi.fn();

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
  listUsers: (...args: unknown[]) => listUsersMock(...args),
}));

describe("LoginPage profile picker", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it("loads users and supports searching by name", async () => {
    listUsersMock.mockResolvedValue([
      {
        id: "f7ed2559-7ec3-4433-b9e4-af8ca6adf72b",
        name: "Priya Sharma",
        email: "priya@example.com",
        occupation: "Engineer",
        monthly_income: 120000,
        currency: "INR",
      },
      {
        id: "1bdb1578-c464-42fa-b212-a0fd4ea4de83",
        name: "Amit Singh",
        email: "amit@example.com",
        occupation: "Analyst",
        monthly_income: 90000,
        currency: "INR",
      },
    ]);

    render(<LoginPage />);

    expect(
      screen.getByText("Loading existing profiles..."),
    ).toBeInTheDocument();

    expect(await screen.findByText("Amit Singh")).toBeInTheDocument();
    expect(screen.getByText("Priya Sharma")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Search profiles"), {
      target: { value: "priya" },
    });

    expect(screen.getByText("Priya Sharma")).toBeInTheDocument();
    expect(screen.queryByText("Amit Singh")).not.toBeInTheDocument();
  });

  it("supports searching by email and selecting profile stores active user", async () => {
    listUsersMock.mockResolvedValue([
      {
        id: "f7ed2559-7ec3-4433-b9e4-af8ca6adf72b",
        name: "Priya Sharma",
        email: "priya@example.com",
        occupation: "Engineer",
        monthly_income: 120000,
        currency: "INR",
      },
    ]);

    render(<LoginPage />);

    await screen.findByText("Priya Sharma");

    fireEvent.change(screen.getByLabelText("Search profiles"), {
      target: { value: "priya@example.com" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Select Profile" }));

    await waitFor(() => {
      const rawUser = localStorage.getItem(USER_STORAGE_KEY);
      expect(rawUser).not.toBeNull();
      expect(JSON.parse(rawUser as string)).toMatchObject({
        id: "f7ed2559-7ec3-4433-b9e4-af8ca6adf72b",
        name: "Priya Sharma",
      });
    });

    const remembered = localStorage.getItem(REMEMBERED_PROFILES_STORAGE_KEY);
    expect(remembered).not.toBeNull();
    expect(navigateMock).toHaveBeenCalledWith("/app/home", { replace: true });
  });

  it("shows empty state and create new profile link", async () => {
    listUsersMock.mockResolvedValue([]);

    render(<LoginPage />);

    expect(await screen.findByText("No profiles found.")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Create New Profile" }),
    ).toHaveAttribute("href", "/register");
  });

  it("shows retry state on network failure", async () => {
    listUsersMock.mockRejectedValueOnce(new Error("network down"));
    listUsersMock.mockResolvedValueOnce([
      {
        id: "f7ed2559-7ec3-4433-b9e4-af8ca6adf72b",
        name: "Priya Sharma",
        email: null,
        occupation: "Engineer",
        monthly_income: 120000,
        currency: "INR",
      },
    ]);

    render(<LoginPage />);

    expect(
      await screen.findByText("Unable to load profiles"),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Retry" }));

    expect(await screen.findByText("Priya Sharma")).toBeInTheDocument();
  });
});
