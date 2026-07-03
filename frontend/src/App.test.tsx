import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import App from "./App";

describe("App Shell", () => {
  it("renders WalletMind shell and home content", async () => {
    render(<App />);

    expect(
      await screen.findByRole("heading", {
        name: "WalletMind",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Understand your money in under a minute with grounded AI insights.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("AI Capabilities")).toBeInTheDocument();
  });

  it("shows onboarding links", async () => {
    render(<App />);

    expect(
      await screen.findByRole("link", { name: "Get Started" }),
    ).toBeInTheDocument();
    expect(
      await screen.findByRole("link", { name: "Open Workspace" }),
    ).toBeInTheDocument();
  });
});
