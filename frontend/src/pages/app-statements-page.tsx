import { useEffect, useMemo, useState } from "react";
import {
  FileSpreadsheet,
  FileText,
  Filter,
  Image,
  Search,
  Trash2,
  Upload,
} from "lucide-react";
import { Link } from "react-router-dom";
import { useLocation } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { useGlobalLoader } from "@/context/global-loader-context";
import { PageTitle, SectionTitle } from "@/components/ui/section-title";
import { StatCard } from "@/components/ui/stat-card";
import { getStoredUser } from "@/lib/auth/storage";
import {
  deleteStatement,
  listStatements,
  type UploadedStatement,
} from "@/lib/api/statements";

const FILTER_OPTIONS = [
  "all",
  "pdf",
  "csv",
  "excel",
  "image",
  "ready",
  "processing",
  "failed",
] as const;

const SORT_OPTIONS = ["newest", "oldest", "filename", "fileSize"] as const;

type FilterOption = (typeof FILTER_OPTIONS)[number];
type SortOption = (typeof SORT_OPTIONS)[number];

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

function getStatusLabel(statement: UploadedStatement): string {
  if (statement.analysis_status === "parsed") {
    return "Completed";
  }

  if (statement.analysis_status === "processing") {
    return "Processing";
  }

  if (statement.analysis_status === "failed") {
    return "Failed";
  }

  if (statement.analysis_status === "uploaded") {
    return "Ready for Analysis";
  }

  return "Uploaded";
}

function getFileExtension(filename: string): string {
  return filename.split(".").pop()?.toLowerCase() ?? "";
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

function toFilterLabel(filter: FilterOption): string {
  if (filter === "all") {
    return "All";
  }

  if (filter === "pdf") {
    return "PDF";
  }

  if (filter === "csv") {
    return "CSV";
  }

  if (filter === "excel") {
    return "Excel";
  }

  if (filter === "image") {
    return "Image";
  }

  if (filter === "ready") {
    return "Ready";
  }

  if (filter === "processing") {
    return "Processing";
  }

  return "Failed";
}

export function AppStatementsPage() {
  const location = useLocation();
  const { hideLoader } = useGlobalLoader();
  const user = getStoredUser();
  const [statements, setStatements] = useState<UploadedStatement[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDeleting, setIsDeleting] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filter, setFilter] = useState<FilterOption>("all");
  const [sortBy, setSortBy] = useState<SortOption>("newest");

  useEffect(() => {
    let mounted = true;

    async function loadStatements() {
      if (!user?.id) {
        if (mounted) {
          setErrorMessage(
            "Unable to determine your profile. Please sign in again.",
          );
          setIsLoading(false);
        }
        return;
      }

      try {
        const response = await listStatements(user.id);
        if (!mounted) {
          return;
        }
        setStatements(response);
        setErrorMessage(null);
        hideLoader();
      } catch {
        if (!mounted) {
          return;
        }
        setErrorMessage(
          "Unable to load statements right now. Please try again.",
        );
        hideLoader();
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    }

    void loadStatements();

    return () => {
      mounted = false;
    };
  }, [location.state, user?.id]);

  const filteredAndSortedStatements = useMemo(() => {
    const normalizedSearchTerm = searchTerm.trim().toLowerCase();

    const filtered = statements.filter((statement) => {
      const extension = getFileExtension(statement.original_filename);
      const parserType = statement.parser_type.toLowerCase();
      const bankName = statement.bank_name?.toLowerCase() ?? "";
      const filename = statement.original_filename.toLowerCase();

      const matchesSearch =
        normalizedSearchTerm.length === 0 ||
        filename.includes(normalizedSearchTerm) ||
        parserType.includes(normalizedSearchTerm) ||
        bankName.includes(normalizedSearchTerm);

      if (!matchesSearch) {
        return false;
      }

      if (filter === "all") {
        return true;
      }

      if (filter === "pdf") {
        return extension === "pdf";
      }

      if (filter === "csv") {
        return extension === "csv";
      }

      if (filter === "excel") {
        return extension === "xls" || extension === "xlsx";
      }

      if (filter === "image") {
        return (
          extension === "png" || extension === "jpg" || extension === "jpeg"
        );
      }

      if (filter === "ready") {
        return statement.analysis_status === "uploaded";
      }

      if (filter === "processing") {
        return statement.analysis_status === "processing";
      }

      return statement.analysis_status === "failed";
    });

    return [...filtered].sort((left, right) => {
      if (sortBy === "newest") {
        return (
          new Date(right.uploaded_at).getTime() -
          new Date(left.uploaded_at).getTime()
        );
      }

      if (sortBy === "oldest") {
        return (
          new Date(left.uploaded_at).getTime() -
          new Date(right.uploaded_at).getTime()
        );
      }

      if (sortBy === "filename") {
        return left.original_filename.localeCompare(right.original_filename);
      }

      return right.file_size - left.file_size;
    });
  }, [filter, searchTerm, sortBy, statements]);

  const summary = useMemo(() => {
    const totalStatements = statements.length;
    const readyForAnalysis = statements.filter(
      (statement) => statement.analysis_status === "uploaded",
    ).length;
    const processing = statements.filter(
      (statement) => statement.analysis_status === "processing",
    ).length;
    const storageUsedBytes = statements.reduce(
      (sum, statement) => sum + statement.file_size,
      0,
    );

    return {
      totalStatements,
      readyForAnalysis,
      processing,
      storageUsedBytes,
    };
  }, [statements]);

  const handleDelete = async (statement: UploadedStatement) => {
    const shouldDelete = window.confirm(
      `Delete ${statement.original_filename}? This action cannot be undone.`,
    );

    if (!shouldDelete) {
      return;
    }

    setIsDeleting(statement.statement_uuid);
    setSuccessMessage(null);

    try {
      await deleteStatement(statement.statement_uuid);
      setStatements((previous) =>
        previous.filter(
          (item) => item.statement_uuid !== statement.statement_uuid,
        ),
      );
      setSuccessMessage("Statement deleted successfully.");
      setErrorMessage(null);
    } catch {
      setErrorMessage(
        "Unable to delete statement right now. Please try again.",
      );
    } finally {
      setIsDeleting(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <PageTitle
          title="Statement Library"
          subtitle="Manage your uploaded financial statements."
        />
        <Button asChild>
          <Link to="/app/statements/upload">
            <Upload className="mr-2 h-[var(--icon-sm)] w-[var(--icon-sm)]" />
            Upload Statement
          </Link>
        </Button>
      </div>

      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Total Statements"
          value={`${summary.totalStatements}`}
        />
        <StatCard
          label="Ready For Analysis"
          value={`${summary.readyForAnalysis}`}
        />
        <StatCard label="Processing" value={`${summary.processing}`} />
        <StatCard
          label="Storage Used"
          value={formatFileSize(summary.storageUsedBytes)}
        />
      </section>

      <Card>
        <CardContent className="space-y-4 p-4 md:p-5">
          <div className="grid gap-3 lg:grid-cols-[1fr_auto_auto]">
            <label className="relative flex items-center">
              <Search className="pointer-events-none absolute left-3 h-[var(--icon-sm)] w-[var(--icon-sm)] text-[var(--text-muted)]" />
              <input
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                placeholder="Search by filename, parser, or bank"
                className="flex h-10 w-full rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] px-9 py-2 text-sm text-[var(--text)] shadow-[var(--shadow-inset)] outline-none transition focus-visible:ring-2 focus-visible:ring-[var(--ring)]"
              />
            </label>

            <label className="inline-flex items-center gap-2 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--text-muted)]">
              <Filter className="h-[var(--icon-sm)] w-[var(--icon-sm)]" />
              <select
                value={filter}
                onChange={(event) =>
                  setFilter(event.target.value as FilterOption)
                }
                className="bg-transparent text-sm text-[var(--text)] outline-none"
              >
                {FILTER_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {toFilterLabel(option)}
                  </option>
                ))}
              </select>
            </label>

            <label className="inline-flex items-center rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--text-muted)]">
              <span className="mr-2">Sort</span>
              <select
                value={sortBy}
                onChange={(event) =>
                  setSortBy(event.target.value as SortOption)
                }
                className="bg-transparent text-sm text-[var(--text)] outline-none"
              >
                <option value="newest">Newest</option>
                <option value="oldest">Oldest</option>
                <option value="filename">Filename</option>
                <option value="fileSize">File Size</option>
              </select>
            </label>
          </div>
        </CardContent>
      </Card>

      {successMessage ? (
        <Card>
          <CardContent className="p-4 text-sm text-[var(--text)]">
            {successMessage}
          </CardContent>
        </Card>
      ) : null}

      {errorMessage ? (
        <ErrorState title="Statement Library" description={errorMessage} />
      ) : null}

      {isLoading ? <LoadingState title="Loading statements..." /> : null}

      {!isLoading && filteredAndSortedStatements.length === 0 ? (
        <EmptyState
          title="No Statements Yet"
          description="Upload your first bank statement to begin building your financial timeline."
          icon={FileSpreadsheet}
        />
      ) : null}

      {!isLoading && filteredAndSortedStatements.length > 0 ? (
        <section className="space-y-4">
          <SectionTitle
            title="Uploaded Statements"
            subtitle="View details and manage statement records."
          />

          <Card className="hidden md:block">
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-[var(--border)] text-sm">
                  <thead className="bg-[var(--surface-soft)] text-left text-[var(--text-muted)]">
                    <tr>
                      <th className="px-4 py-3 font-medium">Filename</th>
                      <th className="px-4 py-3 font-medium">Bank</th>
                      <th className="px-4 py-3 font-medium">Parser</th>
                      <th className="px-4 py-3 font-medium">File Size</th>
                      <th className="px-4 py-3 font-medium">Uploaded Date</th>
                      <th className="px-4 py-3 font-medium">Analysis Status</th>
                      <th className="px-4 py-3 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border)]">
                    {filteredAndSortedStatements.map((statement) => {
                      const extension = getFileExtension(
                        statement.original_filename,
                      );
                      const Icon = getFileIcon(extension);
                      return (
                        <tr
                          key={statement.statement_uuid}
                          className="align-top"
                        >
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              <Icon className="h-[var(--icon-sm)] w-[var(--icon-sm)] text-[var(--text-muted)]" />
                              <span className="font-medium">
                                {statement.original_filename}
                              </span>
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            {statement.bank_name ?? "Unknown"}
                          </td>
                          <td className="px-4 py-3">{statement.parser_type}</td>
                          <td className="px-4 py-3">
                            {formatFileSize(statement.file_size)}
                          </td>
                          <td className="px-4 py-3">
                            {new Date(statement.uploaded_at).toLocaleString()}
                          </td>
                          <td className="px-4 py-3">
                            <Badge variant="muted">
                              {getStatusLabel(statement)}
                            </Badge>
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex gap-2">
                              <Button
                                size="sm"
                                variant="secondary"
                                type="button"
                              >
                                View Details
                              </Button>
                              <Button
                                size="sm"
                                variant="secondary"
                                type="button"
                                disabled={
                                  isDeleting === statement.statement_uuid
                                }
                                onClick={() => void handleDelete(statement)}
                              >
                                <Trash2 className="mr-2 h-[var(--icon-sm)] w-[var(--icon-sm)]" />
                                Delete
                              </Button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          <div className="grid gap-3 md:hidden">
            {filteredAndSortedStatements.map((statement) => {
              const extension = getFileExtension(statement.original_filename);
              const Icon = getFileIcon(extension);
              return (
                <Card key={statement.statement_uuid}>
                  <CardContent className="space-y-3 p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-2">
                        <Icon className="h-[var(--icon-sm)] w-[var(--icon-sm)] text-[var(--text-muted)]" />
                        <p className="text-sm font-semibold">
                          {statement.original_filename}
                        </p>
                      </div>
                      <Badge variant="muted">{getStatusLabel(statement)}</Badge>
                    </div>

                    <div className="grid gap-1 text-sm text-[var(--text-muted)]">
                      <p>
                        <span className="text-[var(--text)]">Bank:</span>{" "}
                        {statement.bank_name ?? "Unknown"}
                      </p>
                      <p>
                        <span className="text-[var(--text)]">Parser:</span>{" "}
                        {statement.parser_type}
                      </p>
                      <p>
                        <span className="text-[var(--text)]">File Size:</span>{" "}
                        {formatFileSize(statement.file_size)}
                      </p>
                      <p>
                        <span className="text-[var(--text)]">Uploaded:</span>{" "}
                        {new Date(statement.uploaded_at).toLocaleString()}
                      </p>
                    </div>

                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="secondary"
                        type="button"
                        className="flex-1"
                      >
                        View Details
                      </Button>
                      <Button
                        size="sm"
                        variant="secondary"
                        type="button"
                        className="flex-1"
                        disabled={isDeleting === statement.statement_uuid}
                        onClick={() => void handleDelete(statement)}
                      >
                        <Trash2 className="mr-2 h-[var(--icon-sm)] w-[var(--icon-sm)]" />
                        Delete
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </section>
      ) : null}
    </div>
  );
}
