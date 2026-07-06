import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it } from "vitest";

import {
  REMEMBERED_PROFILES_STORAGE_KEY,
  USER_STORAGE_KEY,
} from "@/lib/auth/storage";
import { Sidebar } from "@/components/layout/sidebar";

describe("Sidebar", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("shows Judge Hub navigation item", () => {
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: "Judge Hub" })).toHaveAttribute(
      "href",
      "/app/judge",
    );
  });

  it("logout clears only active user session", () => {
    localStorage.setItem(
      USER_STORAGE_KEY,
      JSON.stringify({
        id: "f7ed2559-7ec3-4433-b9e4-af8ca6adf72b",
        name: "Priya",
        occupation: "Engineer",
        monthly_income: 120000,
        currency: "INR",
      }),
    );
    localStorage.setItem(
      REMEMBERED_PROFILES_STORAGE_KEY,
      JSON.stringify([
        {
          id: "f7ed2559-7ec3-4433-b9e4-af8ca6adf72b",
          name: "Priya",
          occupation: "Engineer",
          monthly_income: 120000,
          currency: "INR",
        },
      ]),
    );

    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Logout" }));

    expect(localStorage.getItem(USER_STORAGE_KEY)).toBeNull();
    expect(
      localStorage.getItem(REMEMBERED_PROFILES_STORAGE_KEY),
    ).not.toBeNull();
  });
});
