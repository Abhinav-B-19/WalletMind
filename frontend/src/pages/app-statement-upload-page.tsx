import { useMemo, useRef, useState } from "react";
import {
  FileSpreadsheet,
  FileText,
  Image,
  LoaderCircle,
  Upload,
  X,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog";
import { ErrorState } from "@/components/ui/error-state";
import { Badge } from "@/components/ui/badge";
import { Dialog } from "@/components/ui/dialog";
import { PageTitle } from "@/components/ui/section-title";
import { getStoredUser } from "@/lib/auth/storage";
import {
  listStatements,
  type UploadedStatement,
  uploadStatement,
} from "@/lib/api/statements";
import { cn } from "@/lib/utils";

const ACCEPTED_EXTENSIONS = [
  "csv",
  "xls",
  "xlsx",
  "pdf",
  "png",
  "jpg",
  "jpeg",
] as const;

const ACCEPTED_FILE_TYPES = ACCEPTED_EXTENSIONS.map(
  (extension) => `.${extension}`,
).join(",");
const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024;

type ValidationState = {
  error: string | null;
  warning: string | null;
};

function formatFileSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  const kilobytes = bytes / 1024;
  if (kilobytes < 1024) {
    return `${kilobytes.toFixed(1)} KB`;
  }

  return `${(kilobytes / 1024).toFixed(1)} MB`;
}

function getFileExtension(filename: string): string {
  const extension = filename.split(".").pop()?.toLowerCase();
  return extension ?? "";
}

function getFileIcon(extension: string) {
  if (["csv", "xls", "xlsx"].includes(extension)) {
    return FileSpreadsheet;
  }

  if (["png", "jpg", "jpeg"].includes(extension)) {
    return Image;
  }

  return FileText;
}

export function AppStatementUploadPage() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [validationState, setValidationState] = useState<ValidationState>({
    error: null,
    warning: null,
  });
  const [dragActive, setDragActive] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadResult, setUploadResult] = useState<UploadedStatement | null>(
    null,
  );
  const [isSuccessDialogOpen, setIsSuccessDialogOpen] = useState(false);
  const [isDuplicateDialogOpen, setIsDuplicateDialogOpen] = useState(false);
  const [duplicateFilename, setDuplicateFilename] = useState<string>("");

  const user = getStoredUser();

  const previewData = useMemo(() => {
    if (!selectedFile) {
      return null;
    }

    const extension = getFileExtension(selectedFile.name);
    const Icon = getFileIcon(extension);
    return {
      extension,
      Icon,
      name: selectedFile.name,
      size: formatFileSize(selectedFile.size),
    };
  }, [selectedFile]);

  const clearSelection = () => {
    setSelectedFile(null);
    setUploadProgress(0);
    setUploadResult(null);
    setValidationState({ error: null, warning: null });
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const validateFile = (file: File): ValidationState => {
    if (!file || file.size <= 0) {
      return {
        error: "Please select a valid non-empty file.",
        warning: null,
      };
    }

    const extension = getFileExtension(file.name);
    if (
      !ACCEPTED_EXTENSIONS.includes(
        extension as (typeof ACCEPTED_EXTENSIONS)[number],
      )
    ) {
      return {
        error:
          "Unsupported file type. Please upload CSV, XLS, XLSX, PDF, PNG, or JPG.",
        warning: null,
      };
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      return {
        error:
          "File exceeds the 10 MB size limit. Please choose a smaller file.",
        warning: null,
      };
    }

    return { error: null, warning: null };
  };

  const handleFileSelection = (file: File | null) => {
    setUploadResult(null);

    if (!file) {
      setSelectedFile(null);
      setValidationState({
        error: "Please choose a file before uploading.",
        warning: null,
      });
      return;
    }

    const nextValidationState = validateFile(file);
    setValidationState(nextValidationState);

    if (nextValidationState.error) {
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
    setUploadProgress(0);
  };

  const performUpload = async () => {
    if (!user?.id) {
      setValidationState({
        error:
          "Unable to determine your profile. Please sign in again before uploading.",
        warning: null,
      });
      return;
    }

    if (!selectedFile) {
      setValidationState({
        error: "Please select a file before uploading.",
        warning: null,
      });
      return;
    }

    setIsUploading(true);
    setValidationState({ error: null, warning: null });

    try {
      const result = await uploadStatement({
        userUuid: user.id,
        file: selectedFile,
        onUploadProgress: setUploadProgress,
      });

      setUploadResult(result);
      setIsSuccessDialogOpen(true);
    } catch (error) {
      setValidationState({
        error:
          error instanceof Error
            ? error.message
            : "Unable to upload statement right now. Please try again.",
        warning: null,
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleUpload = async () => {
    if (!user?.id) {
      setValidationState({
        error:
          "Unable to determine your profile. Please sign in again before uploading.",
        warning: null,
      });
      return;
    }

    if (!selectedFile) {
      setValidationState({
        error: "Please select a file before uploading.",
        warning: null,
      });
      return;
    }

    try {
      const existingStatements = await listStatements(user.id);
      const hasDuplicateFilename = existingStatements.some(
        (statement) =>
          statement.original_filename.toLowerCase() ===
          selectedFile.name.toLowerCase(),
      );

      if (hasDuplicateFilename) {
        setDuplicateFilename(selectedFile.name);
        setIsDuplicateDialogOpen(true);
        return;
      }

      await performUpload();
    } catch (error) {
      setValidationState({
        error:
          error instanceof Error
            ? error.message
            : "Unable to upload statement right now. Please try again.",
        warning: null,
      });
    }
  };

  const handleUploadAnother = () => {
    setIsSuccessDialogOpen(false);
    clearSelection();
  };

  const handleViewLibrary = () => {
    setIsSuccessDialogOpen(false);
    navigate("/app/statements", {
      state: { refreshToken: Date.now() },
    });
  };

  const handleDuplicateCancel = () => {
    setIsDuplicateDialogOpen(false);
    setDuplicateFilename("");
  };

  const handleDuplicateUploadAnyway = async () => {
    setIsDuplicateDialogOpen(false);
    await performUpload();
  };

  const handleFileInputChange = (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const file = event.target.files?.[0] ?? null;
    handleFileSelection(file);
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setDragActive(false);

    const file = event.dataTransfer.files?.[0] ?? null;
    handleFileSelection(file);
  };

  const openFilePicker = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="space-y-6">
      <PageTitle
        title="Statement Upload Workspace"
        subtitle="Upload, review, and prepare statement files for WalletMind analysis."
      />

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Upload Statement</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div
            role="button"
            tabIndex={0}
            onClick={openFilePicker}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                openFilePicker();
              }
            }}
            onDragEnter={(event) => {
              event.preventDefault();
              event.stopPropagation();
              setDragActive(true);
            }}
            onDragOver={(event) => {
              event.preventDefault();
              event.stopPropagation();
              setDragActive(true);
            }}
            onDragLeave={(event) => {
              event.preventDefault();
              event.stopPropagation();
              setDragActive(false);
            }}
            onDrop={handleDrop}
            className={cn(
              "cursor-pointer rounded-[var(--radius-lg)] border-2 border-dashed border-[var(--border)] bg-[var(--surface-soft)] px-6 py-8 text-center transition",
              dragActive
                ? "border-[var(--ring)] bg-[var(--surface)]"
                : "hover:bg-[var(--surface)]",
            )}
          >
            <div className="mx-auto flex max-w-xl flex-col items-center gap-3">
              <div className="grid h-12 w-12 place-items-center rounded-full border border-[var(--border)] bg-[var(--surface)] text-[var(--text-muted)]">
                <Upload className="h-[var(--icon-lg)] w-[var(--icon-lg)]" />
              </div>
              <div>
                <p className="text-sm font-semibold">
                  Drag & drop your statement file here
                </p>
                <p className="mt-1 text-sm text-[var(--text-muted)]">
                  CSV, XLS, XLSX, PDF, PNG, JPG, JPEG • Up to 10 MB
                </p>
              </div>
              <Button
                variant="secondary"
                size="sm"
                type="button"
                onClick={openFilePicker}
              >
                Browse Files
              </Button>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept={ACCEPTED_FILE_TYPES}
              className="hidden"
              onChange={handleFileInputChange}
            />
          </div>

          {validationState.error ? (
            <ErrorState
              title="Upload validation"
              description={validationState.error}
            />
          ) : null}

          {previewData ? (
            <Card>
              <CardContent className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-center gap-3">
                  <div className="grid h-10 w-10 place-items-center rounded-md border border-[var(--border)] bg-[var(--surface-soft)] text-[var(--text-muted)]">
                    <previewData.Icon className="h-[var(--icon-md)] w-[var(--icon-md)]" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold">{previewData.name}</p>
                    <p className="text-xs text-[var(--text-muted)]">
                      {previewData.size} • .
                      {previewData.extension.toUpperCase()}
                    </p>
                  </div>
                </div>

                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={clearSelection}
                >
                  <X className="mr-2 h-[var(--icon-sm)] w-[var(--icon-sm)]" />
                  Remove
                </Button>
              </CardContent>
            </Card>
          ) : null}

          {isUploading ? (
            <Card>
              <CardContent className="space-y-2 p-4">
                <p className="inline-flex items-center gap-2 text-sm text-[var(--text-muted)]">
                  <LoaderCircle className="h-[var(--icon-sm)] w-[var(--icon-sm)] animate-spin" />
                  Uploading statement...
                </p>
                <div className="h-2 rounded-full bg-[var(--surface-soft)]">
                  <div
                    className="h-2 rounded-full bg-[var(--primary)] transition-all"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
                <p className="text-xs text-[var(--text-muted)]">
                  {uploadProgress}% complete
                </p>
              </CardContent>
            </Card>
          ) : null}

          <div className="flex flex-wrap gap-3">
            <Button
              type="button"
              onClick={handleUpload}
              disabled={!selectedFile || isUploading}
            >
              Upload Statement
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={clearSelection}
              disabled={isUploading}
            >
              Reset
            </Button>
          </div>
        </CardContent>
      </Card>

      <Dialog
        open={isSuccessDialogOpen && Boolean(uploadResult)}
        title="Statement Uploaded Successfully"
        description="Your statement has been securely uploaded and is ready for AI analysis."
        actions={
          <>
            <Button
              type="button"
              variant="secondary"
              onClick={handleUploadAnother}
            >
              Upload Another
            </Button>
            <Button type="button" onClick={handleViewLibrary}>
              View Statement Library
            </Button>
          </>
        }
      >
        {uploadResult ? (
          <div className="grid auto-rows-fr gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <Card className="h-full min-w-0">
              <CardContent className="flex h-full min-w-0 flex-col justify-between space-y-1 p-4">
                <p className="text-xs text-[var(--text-muted)]">Filename</p>
                <p
                  className="truncate text-sm font-semibold"
                  title={uploadResult.original_filename}
                  aria-label={`Full filename: ${uploadResult.original_filename}`}
                >
                  {uploadResult.original_filename}
                </p>
              </CardContent>
            </Card>
            <Card className="h-full min-w-0">
              <CardContent className="flex h-full min-w-0 flex-col justify-between space-y-1 p-4">
                <p className="text-xs text-[var(--text-muted)]">File Size</p>
                <p className="text-sm font-semibold">
                  {formatFileSize(uploadResult.file_size)}
                </p>
              </CardContent>
            </Card>
            <Card className="h-full min-w-0">
              <CardContent className="flex h-full min-w-0 flex-col justify-between space-y-1 p-4">
                <p className="text-xs text-[var(--text-muted)]">Parser Type</p>
                <p className="truncate text-sm font-semibold" title={uploadResult.parser_type}>
                  {uploadResult.parser_type}
                </p>
              </CardContent>
            </Card>
            <Card className="h-full min-w-0">
              <CardContent className="flex h-full min-w-0 flex-col justify-between space-y-1 p-4">
                <p className="text-xs text-[var(--text-muted)]">Upload Time</p>
                <p className="text-sm font-semibold">
                  {new Date(uploadResult.uploaded_at).toLocaleString()}
                </p>
              </CardContent>
            </Card>
            <Card className="h-full min-w-0">
              <CardContent className="flex h-full min-w-0 flex-col justify-between space-y-1 p-4">
                <p className="text-xs text-[var(--text-muted)]">
                  Analysis Status
                </p>
                <p className="truncate text-sm font-semibold capitalize" title={uploadResult.analysis_status}>
                  {uploadResult.analysis_status}
                </p>
              </CardContent>
            </Card>
            <Card className="h-full min-w-0">
              <CardContent className="flex h-full min-w-0 flex-col justify-between space-y-1 p-4">
                <p className="text-xs text-[var(--text-muted)]">Readiness</p>
                <Badge className="mt-1">Ready for Analysis</Badge>
              </CardContent>
            </Card>
          </div>
        ) : null}
      </Dialog>

      <ConfirmationDialog
        open={isDuplicateDialogOpen}
        title="Duplicate Statement Detected"
        description="A statement with this filename already exists. Uploading another copy may create duplicate records."
        cancelLabel="Cancel"
        confirmLabel="Upload Anyway"
        variant="warning"
        onCancel={handleDuplicateCancel}
        onConfirm={() => void handleDuplicateUploadAnyway()}
      />
    </div>
  );
}
