import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

const mockFetch = vi.fn();

beforeEach(() => {
  vi.stubGlobal("fetch", mockFetch);
});

afterEach(() => {
  vi.unstubAllGlobals();
  mockFetch.mockReset();
});

describe("App", () => {
  it("shows client-side validation errors", async () => {
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "Create Profile" }));

    expect(
      await screen.findByText("Full Name is required."),
    ).toBeInTheDocument();
    expect(screen.getByText("Occupation is required.")).toBeInTheDocument();
    expect(screen.getByText("Monthly Income is required.")).toBeInTheDocument();
  });

  it("shows success state after successful registration", async () => {
    mockFetch.mockResolvedValue({ ok: true });

    render(<App />);

    fireEvent.change(screen.getByLabelText("Full Name"), {
      target: { value: "Ava Lee" },
    });
    fireEvent.change(screen.getByLabelText("Occupation"), {
      target: { value: "Consultant" },
    });
    fireEvent.change(screen.getByLabelText("Monthly Income"), {
      target: { value: "5400" },
    });
    fireEvent.change(screen.getByLabelText("Currency"), {
      target: { value: "USD" },
    });
    fireEvent.change(screen.getByLabelText("Primary Financial Goal"), {
      target: { value: "Build Emergency Fund" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Create Profile" }));

    await waitFor(() => {
      expect(
        screen.getByText("✓ Profile Created Successfully"),
      ).toBeInTheDocument();
    });
    expect(
      screen.getByText("Ready to Upload Your First Bank Statement"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Continue" }),
    ).toBeInTheDocument();
  });

  it("shows API error message when submission fails", async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      json: async () => ({
        message: "User with the same name and occupation already exists",
      }),
    });

    render(<App />);

    fireEvent.change(screen.getByLabelText("Full Name"), {
      target: { value: "Ava Lee" },
    });
    fireEvent.change(screen.getByLabelText("Occupation"), {
      target: { value: "Consultant" },
    });
    fireEvent.change(screen.getByLabelText("Monthly Income"), {
      target: { value: "5400" },
    });
    fireEvent.change(screen.getByLabelText("Currency"), {
      target: { value: "USD" },
    });
    fireEvent.change(screen.getByLabelText("Primary Financial Goal"), {
      target: { value: "Build Emergency Fund" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Create Profile" }));

    expect(
      await screen.findByText(
        "User with the same name and occupation already exists",
      ),
    ).toBeInTheDocument();
  });
});
