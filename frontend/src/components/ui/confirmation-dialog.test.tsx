import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ConfirmationDialog } from "@/components/ui/confirmation-dialog";

describe("ConfirmationDialog", () => {
  it("renders title and description", () => {
    render(
      <ConfirmationDialog
        open
        title="Delete Statement"
        description="This action cannot be undone."
        onCancel={() => undefined}
        onConfirm={() => undefined}
      />,
    );

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText("Delete Statement")).toBeInTheDocument();
    expect(screen.getByText("This action cannot be undone.")).toBeInTheDocument();
  });

  it("invokes cancel callback", () => {
    const onCancel = vi.fn();

    render(
      <ConfirmationDialog
        open
        title="Cancel Upload"
        description="Cancel this upload?"
        onCancel={onCancel}
        onConfirm={() => undefined}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it("invokes confirm callback", () => {
    const onConfirm = vi.fn();

    render(
      <ConfirmationDialog
        open
        title="Delete Statement"
        description="Confirm delete"
        onCancel={() => undefined}
        onConfirm={onConfirm}
        confirmLabel="Delete"
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Delete" }));
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it("renders variant marker for warning, danger, and info", () => {
    const { rerender, container } = render(
      <ConfirmationDialog
        open
        title="Warn"
        description="Warning dialog"
        variant="warning"
        onCancel={() => undefined}
        onConfirm={() => undefined}
      />,
    );

    expect(container.querySelector('[data-variant="warning"]')).toBeInTheDocument();

    rerender(
      <ConfirmationDialog
        open
        title="Danger"
        description="Danger dialog"
        variant="danger"
        onCancel={() => undefined}
        onConfirm={() => undefined}
      />,
    );

    expect(container.querySelector('[data-variant="danger"]')).toBeInTheDocument();

    rerender(
      <ConfirmationDialog
        open
        title="Info"
        description="Info dialog"
        variant="info"
        onCancel={() => undefined}
        onConfirm={() => undefined}
      />,
    );

    expect(container.querySelector('[data-variant="info"]')).toBeInTheDocument();
  });
});
