import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import App from "./App";

describe("App Shell", () => {
  it("renders WalletMind shell and home content", async () => {
    render(<App />);

    expect(
      await screen.findByRole("heading", {
        name: "Welcome to WalletMind",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Get Started",
        level: 3,
      }),
    ).toBeInTheDocument();
  });

  it("shows onboarding links", async () => {
    render(<App />);

    expect(
      await screen.findByRole("link", { name: "Get Started" }),
    ).toBeInTheDocument();
    expect(
      await screen.findByRole("link", { name: "Continue" }),
    ).toBeInTheDocument();
  });
});
