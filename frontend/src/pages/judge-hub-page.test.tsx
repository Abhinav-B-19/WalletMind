import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { JudgeHubPage } from "@/pages/judge-hub-page";

describe("JudgeHubPage", () => {
  const openSpy = vi.fn();

  beforeEach(() => {
    openSpy.mockReset();
    vi.stubGlobal("open", openSpy);
  });

  it("renders grouped card sections", () => {
    render(
      <MemoryRouter>
        <JudgeHubPage />
      </MemoryRouter>,
    );

    expect(
      screen.getByRole("heading", { name: "Quick Actions" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Documentation" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Submission Assets" }),
    ).toBeInTheDocument();

    const cardTitles = [
      "Agent Playground",
      "REST Swagger",
      "MCP Swagger",
      "Architecture",
      "Quick Start",
      "Demo Guide",
      "Rubric Mapping",
      "GitHub Repository",
      "Kaggle Notebook",
      "Demo Video",
      "Project Overview",
    ];

    for (const title of cardTitles) {
      expect(screen.getByRole("heading", { name: title })).toBeInTheDocument();
    }

    expect(
      screen.queryByRole("heading", { name: "Evaluation Checklist" }),
    ).not.toBeInTheDocument();
    expect(screen.getAllByTestId("judge-hub-card")).toHaveLength(11);
  });

  it("renders hero actions and recommended flow", () => {
    render(
      <MemoryRouter>
        <JudgeHubPage />
      </MemoryRouter>,
    );

    expect(
      screen.getByRole("heading", { name: "WalletMind Judge Hub" }),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Start demo" }));
    expect(openSpy).toHaveBeenCalledWith(
      "/app/agent-playground",
      "_blank",
      "noopener,noreferrer",
    );

    fireEvent.click(screen.getByRole("button", { name: "View architecture" }));
    expect(openSpy).toHaveBeenCalledWith(
      expect.stringContaining("ARCHITECTURE.md"),
      "_blank",
      "noopener,noreferrer",
    );

    expect(
      screen.getByRole("heading", { name: "Recommended Flow" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Per-Agent Results")).toBeInTheDocument();
  });

  it("supports entire card click and button click with new-tab navigation", () => {
    render(
      <MemoryRouter>
        <JudgeHubPage />
      </MemoryRouter>,
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Agent Playground card" }),
    );
    expect(openSpy).toHaveBeenCalledWith(
      "/app/agent-playground",
      "_blank",
      "noopener,noreferrer",
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Agent Playground action" }),
    );
    expect(openSpy).toHaveBeenCalledWith(
      "/app/agent-playground",
      "_blank",
      "noopener,noreferrer",
    );
    expect(openSpy.mock.calls.length).toBeGreaterThanOrEqual(2);
  });

  it("opens coming soon modal instead of navigating", () => {
    render(
      <MemoryRouter>
        <JudgeHubPage />
      </MemoryRouter>,
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Kaggle Notebook card" }),
    );
    expect(openSpy).not.toHaveBeenCalled();
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(
      screen.getByText(
        "This submission asset will be available in the final submission package.",
      ),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Close" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("applies hover, footer, and responsive classes on cards", () => {
    render(
      <MemoryRouter>
        <JudgeHubPage />
      </MemoryRouter>,
    );

    const firstCard = screen.getAllByTestId("judge-hub-card")[0];
    expect(firstCard.className).toContain("overflow-hidden");
    expect(firstCard.className).toContain("hover:-translate-y-0.5");
    expect(firstCard.className).toContain("hover:border-[var(--primary)]/50");
    expect(firstCard.className).toContain("hover:shadow-[var(--shadow-md)]");
    expect(firstCard.className).toContain("group");

    const firstCardWrapper = screen.getAllByTestId("judge-hub-card-wrapper")[0];
    expect(firstCardWrapper.className).toContain("h-full");

    const footer = screen.getAllByTestId("judge-card-footer")[0];
    expect(footer.className).toContain("border-t");

    const grid = firstCard.parentElement?.parentElement;
    expect(grid).not.toBeNull();
    expect(grid?.className).toContain("md:grid-cols-2");
    expect(grid?.className).toContain("lg:grid-cols-3");
  });

  it("uses compact card content sizing without fixed min-height", () => {
    render(
      <MemoryRouter>
        <JudgeHubPage />
      </MemoryRouter>,
    );

    const firstCardContent =
      screen.getAllByTestId("judge-card-footer")[0].parentElement;
    expect(firstCardContent).not.toBeNull();
    expect(firstCardContent?.className).toContain("flex-1");
    expect(firstCardContent?.className).not.toContain("min-h-[13rem]");
  });

  it("keeps recommended flow and platform snapshot in equal-width responsive grid", () => {
    render(
      <MemoryRouter>
        <JudgeHubPage />
      </MemoryRouter>,
    );

    const flowSection = screen.getByTestId("judge-flow-section");
    expect(flowSection.className).toContain("md:grid-cols-2");
    expect(flowSection.className).not.toContain("xl:grid-cols-[1.2fr_0.8fr]");

    const flowCard = screen.getByTestId("judge-flow-card");
    const snapshotCard = screen.getByTestId("judge-snapshot-card");
    expect(flowCard.className).toContain("h-full");
    expect(snapshotCard.className).toContain("h-full");
  });

  it("keeps section spacing and footer compact without layout regressions", () => {
    render(
      <MemoryRouter>
        <JudgeHubPage />
      </MemoryRouter>,
    );

    const root = screen.getByLabelText("Judge hub page");
    expect(root.className).toContain("space-y-6");
    expect(root.className).not.toContain("space-y-8");

    const footer = screen.getByTestId("judge-footer");
    expect(footer.className).toContain("w-full");
    expect(footer.className).toContain("py-3");
  });

  it("supports keyboard navigation and opens cards in a new tab", () => {
    render(
      <MemoryRouter>
        <JudgeHubPage />
      </MemoryRouter>,
    );

    const restSwaggerCard = screen.getByRole("button", {
      name: "REST Swagger card",
    });

    fireEvent.keyDown(restSwaggerCard, { key: "Enter" });
    fireEvent.keyDown(restSwaggerCard, { key: " " });

    expect(openSpy).toHaveBeenCalledWith(
      "http://localhost:8000/docs",
      "_blank",
      "noopener,noreferrer",
    );
    expect(openSpy.mock.calls.length).toBeGreaterThanOrEqual(2);
  });
});
