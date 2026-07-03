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
import { Card, CardContent } from "@/components/ui/card";
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog";
import { Dialog } from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { useGlobalLoader } from "@/context/global-loader-context";
import { PageTitle, SectionTitle } from "@/components/ui/section-title";
import { StatCard } from "@/components/ui/stat-card";
import { getStoredUser } from "@/lib/auth/storage";
import {
  deleteStatement,
  getStatementTransactions,
  type TransactionRecord,
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
type TxTypeFilter = "all" | "income" | "expense" | "internal_transfer";

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
  if (statement.analysis_status === "ready_for_analysis") {
    return "Ready For Analysis";
  }

  if (statement.analysis_status === "ready_for_parsing") {
    return "Ready For Parsing";
  }

  if (statement.analysis_status === "classified") {
    return "Classified";
  }

  if (statement.analysis_status === "classifying") {
    return "Classifying";
  }

  if (statement.analysis_status === "parsed") {
    return "Completed";
  }

  if (statement.analysis_status === "processing") {
    return "Processing";
  }

  if (statement.analysis_status === "failed") {
    return "Failed";
  }

  if (statement.analysis_status === "parse_failed") {
    return "Parse Failed";
  }

  if (statement.analysis_status === "uploaded") {
    return "Uploaded";
  }

  if (statement.analysis_status === "queued") {
    return "Queued";
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
  const [statementPendingDelete, setStatementPendingDelete] =
    useState<UploadedStatement | null>(null);
  const [selectedStatement, setSelectedStatement] =
    useState<UploadedStatement | null>(null);
  const [statementTransactions, setStatementTransactions] = useState<
    TransactionRecord[]
  >([]);
  const [isLoadingDetails, setIsLoadingDetails] = useState(false);
  const [detailsError, setDetailsError] = useState<string | null>(null);
  const [txSearch, setTxSearch] = useState("");
  const [txTypeFilter, setTxTypeFilter] = useState<TxTypeFilter>("all");
  const [txCategoryFilter, setTxCategoryFilter] = useState("all");
  const [selectedTransaction, setSelectedTransaction] =
    useState<TransactionRecord | null>(null);
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
        return statement.analysis_status === "ready_for_analysis";
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
      (statement) => statement.analysis_status === "ready_for_analysis",
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

  const confirmDelete = async () => {
    if (!statementPendingDelete) {
      return;
    }

    const statement = statementPendingDelete;
    setIsDeleting(statement.statement_uuid);
    setSuccessMessage(null);

    try {
      await deleteStatement(statement.statement_uuid);
      setStatements((previous) =>
        previous.filter(
          (item) => item.statement_uuid !== statement.statement_uuid,
        ),
      );
      if (selectedStatement?.statement_uuid === statement.statement_uuid) {
        setSelectedStatement(null);
        setStatementTransactions([]);
      }
      setSuccessMessage("Statement deleted successfully.");
      setErrorMessage(null);
    } catch {
      setErrorMessage(
        "Unable to delete statement right now. Please try again.",
      );
    } finally {
      setIsDeleting(null);
      setStatementPendingDelete(null);
    }
  };

  const handleViewDetails = async (statement: UploadedStatement) => {
    console.info("[transactions] ui:view_details_click", {
      statementUuid: statement.statement_uuid,
      filename: statement.original_filename,
      currentParsedCount: statement.parsed_transaction_count,
    });

    setSelectedStatement(statement);
    setDetailsError(null);
    setIsLoadingDetails(true);

    try {
      const records = await getStatementTransactions(statement.statement_uuid);
      console.info("[transactions] ui:view_details_success", {
        statementUuid: statement.statement_uuid,
        returnedCount: records.length,
      });
      setStatementTransactions(records);
    } catch (error) {
      console.error("[transactions] ui:view_details_error", {
        statementUuid: statement.statement_uuid,
        error,
      });
      setStatementTransactions([]);
      setDetailsError(
        error instanceof Error
          ? error.message
          : "Unable to load parsed transactions for this statement.",
      );
    } finally {
      setIsLoadingDetails(false);
    }
  };

  const closeDetailsModal = () => {
    setSelectedStatement(null);
    setDetailsError(null);
    setStatementTransactions([]);
    setTxSearch("");
    setTxTypeFilter("all");
    setTxCategoryFilter("all");
    setSelectedTransaction(null);
  };

  const closeTransactionDetailModal = () => {
    setSelectedTransaction(null);
  };

  const transactionCategories = useMemo(() => {
    const set = new Set<string>();
    for (const tx of statementTransactions) {
      set.add(tx.category);
    }
    return ["all", ...Array.from(set).sort((a, b) => a.localeCompare(b))];
  }, [statementTransactions]);

  const filteredTransactions = useMemo(() => {
    const query = txSearch.trim().toLowerCase();
    return statementTransactions.filter((tx) => {
      if (
        txTypeFilter !== "all" &&
        tx.normalized_transaction_type !== txTypeFilter
      ) {
        return false;
      }
      if (txCategoryFilter !== "all" && tx.category !== txCategoryFilter) {
        return false;
      }
      if (!query) {
        return true;
      }
      const merchant = tx.merchant_name?.toLowerCase() ?? "";
      return (
        merchant.includes(query) ||
        tx.category.toLowerCase().includes(query) ||
        tx.clean_description.toLowerCase().includes(query)
      );
    });
  }, [statementTransactions, txSearch, txTypeFilter, txCategoryFilter]);

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
                placeholder="Search statements..."
                aria-label="Search statements"
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
                aria-label="Filter statements"
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
                aria-label="Sort statements"
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
                          className="align-middle transition-colors hover:bg-[var(--surface-soft)]/50"
                        >
                          <td className="max-w-[280px] px-4 py-3">
                            <div className="flex min-w-0 items-center gap-2">
                              <Icon className="h-[var(--icon-sm)] w-[var(--icon-sm)] text-[var(--text-muted)]" />
                              <span
                                className="block truncate font-medium"
                                title={statement.original_filename}
                              >
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
                                onClick={() =>
                                  void handleViewDetails(statement)
                                }
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
                                onClick={() =>
                                  setStatementPendingDelete(statement)
                                }
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
                        <p
                          className="max-w-[12rem] truncate text-sm font-semibold"
                          title={statement.original_filename}
                        >
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
                        onClick={() => void handleViewDetails(statement)}
                      >
                        View Details
                      </Button>
                      <Button
                        size="sm"
                        variant="secondary"
                        type="button"
                        className="flex-1"
                        disabled={isDeleting === statement.statement_uuid}
                        onClick={() => setStatementPendingDelete(statement)}
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

      <Dialog
        open={Boolean(selectedStatement)}
        title={selectedStatement?.original_filename ?? "Statement Details"}
        description={
          selectedStatement
            ? `${selectedStatement.bank_name ?? "Unknown"} • ${selectedStatement.parser_type}`
            : undefined
        }
        onClose={closeDetailsModal}
        maxWidthClassName="max-w-[1000px]"
        contentClassName="space-y-4 p-0"
        actions={
          <Button type="button" variant="secondary" onClick={closeDetailsModal}>
            Close
          </Button>
        }
      >
        {selectedStatement ? (
          <div className="space-y-3 px-6 pb-2 text-xs text-[var(--text-muted)] sm:grid sm:grid-cols-2 lg:grid-cols-4 sm:gap-3 sm:space-y-0">
            <p>
              Total Transactions:{" "}
              <span className="text-[var(--text)]">
                {selectedStatement.parsed_transaction_count}
              </span>
            </p>
            <p>
              Rows Parsed:{" "}
              <span className="text-[var(--text)]">
                {selectedStatement.rows_parsed ??
                  selectedStatement.parsed_transaction_count}
              </span>
            </p>
            <p>
              Rows Skipped:{" "}
              <span className="text-[var(--text)]">
                {selectedStatement.rows_skipped ??
                  selectedStatement.failed_transaction_count}
              </span>
            </p>
            <p>
              Parser:{" "}
              <span className="text-[var(--text)]">
                {selectedStatement.parser_type}
              </span>
            </p>
            <p>
              Bank:{" "}
              <span className="text-[var(--text)]">
                {selectedStatement.bank_name ?? "Unknown"}
              </span>
            </p>
            <p>
              Processing Time:{" "}
              <span className="text-[var(--text)]">
                {selectedStatement.parsing_duration_ms ?? 0} ms
              </span>
            </p>
            <p>
              Direction Corrections:{" "}
              <span className="text-[var(--text)]">
                {selectedStatement.direction_corrections ?? 0}
              </span>
            </p>
            <p>
              Status:{" "}
              <span className="text-[var(--text)]">
                {getStatusLabel(selectedStatement)}
              </span>
            </p>
            <p>
              Parsed At:{" "}
              <span className="text-[var(--text)]">
                {selectedStatement.parsed_at
                  ? new Date(selectedStatement.parsed_at).toLocaleString()
                  : "Not available"}
              </span>
            </p>
          </div>
        ) : null}

        <div className="max-h-[80vh] overflow-auto rounded-b-[var(--radius-md)] border-t border-[var(--border)] px-6 pb-6">
          <div className="sticky top-0 z-10 grid gap-2 border-b border-[var(--border)] bg-[var(--surface)] py-3 sm:grid-cols-3">
            <input
              value={txSearch}
              onChange={(event) => setTxSearch(event.target.value)}
              placeholder="Search merchant/category/description"
              aria-label="Search transactions"
              className="h-9 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] px-3 text-xs text-[var(--text)] outline-none"
            />
            <select
              value={txTypeFilter}
              onChange={(event) =>
                setTxTypeFilter(event.target.value as TxTypeFilter)
              }
              aria-label="Filter transactions by type"
              className="h-9 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] px-3 text-xs text-[var(--text)] outline-none"
            >
              <option value="all">All Types</option>
              <option value="income">Income</option>
              <option value="expense">Expense</option>
              <option value="internal_transfer">Transfer</option>
            </select>
            <select
              value={txCategoryFilter}
              onChange={(event) => setTxCategoryFilter(event.target.value)}
              aria-label="Filter transactions by category"
              className="h-9 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] px-3 text-xs text-[var(--text)] outline-none"
            >
              {transactionCategories.map((category) => (
                <option key={category} value={category}>
                  {category === "all" ? "All Categories" : category}
                </option>
              ))}
            </select>
          </div>

          {isLoadingDetails ? (
            <p className="py-4 text-sm text-[var(--text-muted)]">
              Loading transactions...
            </p>
          ) : null}

          {!isLoadingDetails && detailsError ? (
            <p className="py-4 text-sm text-[var(--danger)]">{detailsError}</p>
          ) : null}

          {!isLoadingDetails &&
          !detailsError &&
          filteredTransactions.length === 0 ? (
            <p className="py-4 text-sm text-[var(--text-muted)]">
              No parsed transactions available for this statement.
            </p>
          ) : null}

          {!isLoadingDetails &&
          !detailsError &&
          filteredTransactions.length > 0 ? (
            <div className="overflow-x-auto rounded-[var(--radius-md)] border border-[var(--border)]">
              <table className="min-w-full divide-y divide-[var(--border)] text-xs">
                <thead className="bg-[var(--surface-soft)] text-left text-[var(--text-muted)]">
                  <tr>
                    <th className="px-3 py-2 font-medium">Date</th>
                    <th className="px-3 py-2 font-medium">Description</th>
                    <th className="px-3 py-2 font-medium">Category</th>
                    <th className="px-3 py-2 font-medium">Merchant</th>
                    <th className="px-3 py-2 font-medium">Type</th>
                    <th className="px-3 py-2 font-medium">Amount</th>
                    <th className="px-3 py-2 font-medium">Balance</th>
                    <th className="px-3 py-2 font-medium">Info</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border)]">
                  {filteredTransactions.map((transaction) => (
                    <tr
                      key={transaction.transaction_uuid}
                      className="cursor-pointer transition-colors hover:bg-[var(--surface-soft)]/50"
                      onClick={() => setSelectedTransaction(transaction)}
                    >
                      <td className="px-3 py-2">
                        {new Date(
                          transaction.transaction_date,
                        ).toLocaleDateString()}
                      </td>
                      <td
                        className="max-w-[20rem] truncate px-3 py-2"
                        title={transaction.clean_description}
                      >
                        {transaction.clean_description}
                      </td>
                      <td className="px-3 py-2">
                        <Badge variant="muted">{transaction.category}</Badge>
                      </td>
                      <td
                        className="max-w-[14rem] truncate px-3 py-2"
                        title={transaction.merchant_name ?? "Unknown"}
                      >
                        {transaction.merchant_name ?? "Unknown"}
                      </td>
                      <td className="px-3 py-2">
                        <Badge variant="muted">
                          {transaction.normalized_transaction_type}
                        </Badge>
                      </td>
                      <td className="px-3 py-2">
                        {transaction.amount.toFixed(2)}
                      </td>
                      <td className="px-3 py-2">
                        {transaction.balance !== null &&
                        transaction.balance !== undefined
                          ? transaction.balance.toFixed(2)
                          : "-"}
                      </td>
                      <td className="px-3 py-2">
                        <Button
                          size="sm"
                          variant="secondary"
                          type="button"
                          aria-label="Open transaction details"
                          onClick={(event) => {
                            event.stopPropagation();
                            setSelectedTransaction(transaction);
                          }}
                        >
                          i
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </div>
      </Dialog>

      <Dialog
        open={Boolean(selectedTransaction)}
        title="Transaction Details"
        description={selectedTransaction?.merchant_name ?? "Unknown Merchant"}
        onClose={closeTransactionDetailModal}
        maxWidthClassName="max-w-[760px]"
        contentClassName="space-y-4 p-0"
        actions={
          <Button
            type="button"
            variant="secondary"
            onClick={closeTransactionDetailModal}
          >
            Close
          </Button>
        }
      >
        {selectedTransaction ? (
          <div className="space-y-3 px-6 pb-6 pt-2 text-sm text-[var(--text-muted)]">
            <div className="grid gap-2 sm:grid-cols-2">
              <p>
                Date:{" "}
                <span className="text-[var(--text)]">
                  {new Date(
                    selectedTransaction.transaction_date,
                  ).toLocaleDateString()}
                </span>
              </p>
              <p>
                Description:{" "}
                <span className="text-[var(--text)]">
                  {selectedTransaction.clean_description}
                </span>
              </p>
              <p>
                Merchant:{" "}
                <span className="text-[var(--text)]">
                  {selectedTransaction.merchant_name ?? "Unknown"}
                </span>
              </p>
              <p>
                Category:{" "}
                <span className="text-[var(--text)]">
                  {selectedTransaction.category}
                </span>
              </p>
              <p>
                Amount:{" "}
                <span className="text-[var(--text)]">
                  {selectedTransaction.amount.toFixed(2)}
                </span>
              </p>
              <p>
                Balance:{" "}
                <span className="text-[var(--text)]">
                  {selectedTransaction.balance !== null &&
                  selectedTransaction.balance !== undefined
                    ? selectedTransaction.balance.toFixed(2)
                    : "-"}
                </span>
              </p>
              <p>
                Payment Method:{" "}
                <span className="text-[var(--text)]">
                  {selectedTransaction.clean_description
                    .split(" ")[0]
                    ?.toUpperCase() || "Unknown"}
                </span>
              </p>
              <p>
                Reference Number:{" "}
                <span className="text-[var(--text)]">
                  {selectedTransaction.reference_number ?? "Not available"}
                </span>
              </p>
              <p>
                Bank / Gateway:{" "}
                <span className="text-[var(--text)]">
                  {selectedTransaction.bank_gateway ?? "Unknown"}
                </span>
              </p>
              <p>
                Transaction Type:{" "}
                <span className="text-[var(--text)]">
                  {selectedTransaction.normalized_transaction_type}
                </span>
              </p>
            </div>

            <div className="space-y-1">
              <p className="text-xs uppercase tracking-[0.08em] text-[var(--text-muted)]">
                Original Bank Narration
              </p>
              <pre className="max-h-[160px] overflow-auto rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-soft)] p-3 text-xs text-[var(--text)]">
                {selectedTransaction.raw_description}
              </pre>
            </div>
          </div>
        ) : null}
      </Dialog>

      <ConfirmationDialog
        open={Boolean(statementPendingDelete)}
        title="Delete Statement"
        description={
          statementPendingDelete
            ? `Delete ${statementPendingDelete.original_filename}? This action cannot be undone.`
            : "Delete this statement?"
        }
        cancelLabel="Cancel"
        confirmLabel="Delete"
        variant="danger"
        onCancel={() => setStatementPendingDelete(null)}
        onConfirm={() => void confirmDelete()}
        isConfirming={Boolean(
          statementPendingDelete &&
          isDeleting === statementPendingDelete.statement_uuid,
        )}
      />
    </div>
  );
}
