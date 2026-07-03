import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";

type ConfirmationDialogVariant = "warning" | "danger" | "info";

type ConfirmationDialogProps = {
  open: boolean;
  title: string;
  description: string;
  cancelLabel?: string;
  confirmLabel?: string;
  variant?: ConfirmationDialogVariant;
  onCancel: () => void;
  onConfirm: () => void;
  isConfirming?: boolean;
};

function getConfirmVariant(
  variant: ConfirmationDialogVariant,
): "primary" | "secondary" {
  if (variant === "info") {
    return "primary";
  }

  return "secondary";
}

function getConfirmToneClass(variant: ConfirmationDialogVariant): string {
  if (variant === "danger") {
    return "border-[var(--danger)]/50 text-[var(--danger)] hover:bg-[var(--danger)]/10";
  }

  if (variant === "warning") {
    return "border-[var(--ring)]/35 text-[var(--text)] hover:bg-[var(--surface)]";
  }

  return "";
}

export function ConfirmationDialog({
  open,
  title,
  description,
  cancelLabel = "Cancel",
  confirmLabel = "Confirm",
  variant = "warning",
  onCancel,
  onConfirm,
  isConfirming = false,
}: ConfirmationDialogProps) {
  return (
    <Dialog
      open={open}
      title={title}
      description={description}
      onClose={onCancel}
      actions={
        <div className="contents" data-variant={variant}>
          <Button type="button" variant="secondary" onClick={onCancel}>
            {cancelLabel}
          </Button>
          <Button
            type="button"
            variant={getConfirmVariant(variant)}
            className={getConfirmToneClass(variant)}
            onClick={onConfirm}
            disabled={isConfirming}
            aria-label={confirmLabel}
          >
            {confirmLabel}
          </Button>
        </div>
      }
    />
  );
}