"""Statement parser engine and parser registry for F-2.3."""

from __future__ import annotations

from abc import ABC, abstractmethod
import csv
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
import json
import logging
import re
from time import perf_counter
from typing import Any

from walletmind.schemas.transaction import ParserResultDTO, TransactionCreateDTO

logger = logging.getLogger(__name__)


def normalize_date(value: Any) -> date | None:
    """Normalize incoming date values to date.

    Supports DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD, MM/DD/YYYY, and Excel serial dates.
    """

    if value is None:
        return None

    if isinstance(value, date) and not isinstance(value, datetime):
        return value

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, (int, float)):
        try:
            serial = int(value)
            if serial <= 0:
                return None
            excel_epoch = datetime(1899, 12, 30)
            return (excel_epoch + timedelta(days=serial)).date()
        except (ValueError, OverflowError):
            return None

    text = str(value).strip()
    if not text:
        return None

    formats = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%y",
        "%Y/%m/%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue

    return None


def normalize_amount(value: Any) -> Decimal | None:
    """Normalize amount formats like ₹1,000.50, 1,000, -500, CR/DR suffixes."""

    if value is None:
        return None

    if isinstance(value, Decimal):
        return value

    if isinstance(value, (int, float)):
        return Decimal(str(value)).quantize(Decimal("0.01"))

    text = str(value).strip().upper()
    if not text:
        return None

    sign = Decimal("1")
    if text.endswith("CR"):
        text = text.removesuffix("CR").strip()
        sign = Decimal("1")
    elif text.endswith("DR"):
        text = text.removesuffix("DR").strip()
        sign = Decimal("-1")

    text = re.sub(r"[^0-9.\-]", "", text)
    text = text.replace(",", "")
    if not text:
        return None

    try:
        amount = Decimal(text)
        if amount < 0:
            sign = Decimal("1")
        return (amount * sign).quantize(Decimal("0.01"))
    except InvalidOperation:
        return None


def should_skip_row(description: str) -> bool:
    """Skip non-transactional or summary/footer rows."""

    normalized = description.strip().lower()
    if not normalized:
        return True

    skip_tokens = [
        "opening balance",
        "closing balance",
        "total",
        "summary",
        "balance brought forward",
        "balance carried forward",
        "page",
    ]
    return any(token in normalized for token in skip_tokens)


def normalize_transaction(
    *,
    date_value: Any,
    description_value: Any,
    debit_value: Any,
    credit_value: Any,
    amount_value: Any,
    balance_value: Any,
    currency: str | None,
    reference_number: str | None,
    raw_row: dict[str, Any],
) -> TransactionCreateDTO | None:
    """Normalize a raw parser row into the canonical transaction DTO."""

    parsed_date = normalize_date(date_value)
    description = str(description_value or "").strip() or "Transaction"

    if parsed_date is None or should_skip_row(description):
        return None

    debit = normalize_amount(debit_value)
    credit = normalize_amount(credit_value)
    amount = normalize_amount(amount_value)

    if debit is None and credit is None and amount is None:
        return None

    if debit is not None and debit > 0:
        debit = -debit

    if credit is not None and credit < 0:
        credit = -credit

    if amount is None:
        if debit is not None and credit is None:
            amount = debit
        elif credit is not None and debit is None:
            amount = credit
        elif credit is not None and debit is not None:
            amount = credit + debit

    if amount is None:
        return None

    tx_type = "credit" if amount >= 0 else "debit"

    return TransactionCreateDTO(
        transaction_date=parsed_date,
        description=description,
        debit=debit,
        credit=credit,
        amount=amount,
        transaction_type=tx_type,
        balance=normalize_amount(balance_value),
        currency=(currency or "").strip().upper() or None,
        reference_number=reference_number,
        raw_row_json=raw_row,
    )


class BaseStatementParser(ABC):
    """Abstract parser contract."""

    parser_name: str

    @abstractmethod
    def parse(self, *, content: bytes, filename: str, content_type: str | None) -> ParserResultDTO:
        """Parse raw statement bytes and return normalized transactions."""


class GenericCSVParser(BaseStatementParser):
    parser_name = "generic_csv_parser"

    DATE_HEADERS = {"tran date", "date", "txn date", "transaction date"}
    DESCRIPTION_HEADERS = {"particulars", "narration", "description"}
    DEBIT_HEADERS = {"dr", "debit", "withdrawal"}
    CREDIT_HEADERS = {"cr", "credit", "deposit"}
    BALANCE_HEADERS = {"bal", "balance"}
    REFERENCE_HEADERS = {"chqno", "chq no", "cheque no", "reference", "ref"}

    def _normalize_header_token(self, value: str) -> str:
        token = value.strip().lower()
        token = token.replace("_", " ").replace("-", " ")
        token = re.sub(r"\s+", " ", token)
        return token

    def _extract_metadata(self, lines: list[str]) -> dict[str, str]:
        metadata: dict[str, str] = {}
        for line in lines:
            clean = line.strip()
            if not clean:
                continue

            def _value_after_separator(value: str) -> str:
                normalized = value.replace(":-", ":")
                if ":" in normalized:
                    return normalized.split(":", 1)[1].strip()
                return normalized.strip()

            if "currency" in clean.lower() and ":" in clean:
                metadata["currency"] = _value_after_separator(clean)
            if "name" in clean.lower() and ":" in clean and "customer" not in metadata:
                metadata["customer_name"] = _value_after_separator(clean)
            if "account no" in clean.lower() and "for the period" in clean.lower():
                match = re.search(r"account\s+no\s*-\s*([0-9]+)", clean, flags=re.IGNORECASE)
                if match:
                    metadata["account_number"] = match.group(1)
                period_match = re.search(r"for the period\s*\((.*)\)", clean, flags=re.IGNORECASE)
                if period_match:
                    metadata["statement_period"] = period_match.group(1).strip()

        return metadata

    def _find_header_row(self, rows: list[list[str]]) -> tuple[int | None, dict[str, int]]:
        for idx, row in enumerate(rows):
            normalized = [self._normalize_header_token(cell) for cell in row]
            if not normalized:
                continue

            has_date = any(token in self.DATE_HEADERS for token in normalized)
            has_description = any(token in self.DESCRIPTION_HEADERS for token in normalized)
            has_debit = any(token in self.DEBIT_HEADERS for token in normalized)
            has_credit = any(token in self.CREDIT_HEADERS for token in normalized)
            has_balance = any(token in self.BALANCE_HEADERS for token in normalized)

            if not (has_date and has_description and (has_debit or has_credit)):
                continue

            mapping: dict[str, int] = {}
            for col_idx, token in enumerate(normalized):
                if token in self.DATE_HEADERS and "date" not in mapping:
                    mapping["date"] = col_idx
                elif token in self.DESCRIPTION_HEADERS and "description" not in mapping:
                    mapping["description"] = col_idx
                elif token in self.DEBIT_HEADERS and "debit" not in mapping:
                    mapping["debit"] = col_idx
                elif token in self.CREDIT_HEADERS and "credit" not in mapping:
                    mapping["credit"] = col_idx
                elif token in self.BALANCE_HEADERS and "balance" not in mapping:
                    mapping["balance"] = col_idx
                elif token in self.REFERENCE_HEADERS and "reference" not in mapping:
                    mapping["reference"] = col_idx

            return idx, mapping

        return None, {}

    @staticmethod
    def _value_at(row: list[str], idx: int | None) -> str | None:
        if idx is None or idx < 0 or idx >= len(row):
            return None
        value = row[idx].strip()
        return value or None

    @staticmethod
    def _is_footer_or_summary(row: list[str], description: str | None) -> bool:
        joined = " ".join(cell.strip().lower() for cell in row if cell.strip())
        if not joined:
            return True

        tokens = [
            "total",
            "closing balance",
            "opening balance",
            "statement summary",
            "generated on",
            "page",
            "end of statement",
        ]
        if any(token in joined for token in tokens):
            return True

        if description and should_skip_row(description):
            return True

        return False

    def parse(self, *, content: bytes, filename: str, content_type: str | None) -> ParserResultDTO:
        logger.info("CSV opened", extra={"filename": filename, "content_type": content_type})
        decoded = content.decode("utf-8", errors="ignore")
        lines = decoded.splitlines()
        reader = csv.reader(lines)
        rows = [list(row) for row in reader]

        metadata = self._extract_metadata(lines)
        header_index, column_map = self._find_header_row(rows)

        if header_index is None:
            return ParserResultDTO(
                parser_name=self.parser_name,
                rows_scanned=len(rows),
                rows_skipped=len(rows),
                transactions=[],
                errors=["header_not_found"],
                metadata=metadata,
            )

        logger.info(
            "Header detected",
            extra={
                "filename": filename,
                "header_row": header_index + 1,
                "column_map": column_map,
            },
        )

        transactions: list[TransactionCreateDTO] = []
        rows_scanned = 0
        rows_skipped = 0
        errors: list[str] = []

        date_idx = column_map.get("date")
        description_idx = column_map.get("description")
        debit_idx = column_map.get("debit")
        credit_idx = column_map.get("credit")
        balance_idx = column_map.get("balance")
        reference_idx = column_map.get("reference")

        for row_number, row in enumerate(rows[header_index + 1 :], start=header_index + 2):
            rows_scanned += 1
            try:
                if all(not cell.strip() for cell in row):
                    rows_skipped += 1
                    continue

                description_value = self._value_at(row, description_idx)
                if self._is_footer_or_summary(row, description_value):
                    rows_skipped += 1
                    continue

                normalized = normalize_transaction(
                    date_value=self._value_at(row, date_idx),
                    description_value=description_value,
                    debit_value=self._value_at(row, debit_idx),
                    credit_value=self._value_at(row, credit_idx),
                    amount_value=None,
                    balance_value=self._value_at(row, balance_idx),
                    currency=metadata.get("currency"),
                    reference_number=self._value_at(row, reference_idx),
                    raw_row={"row_number": row_number, "columns": row},
                )
                if normalized is None:
                    rows_skipped += 1
                    continue
                transactions.append(normalized)
            except Exception as exc:  # noqa: BLE001
                rows_skipped += 1
                errors.append(f"row_{row_number}:{exc}")

        logger.info(
            "CSV parsing completed",
            extra={
                "filename": filename,
                "rows_scanned": rows_scanned,
                "rows_skipped": rows_skipped,
                "transactions_extracted": len(transactions),
            },
        )

        return ParserResultDTO(
            parser_name=self.parser_name,
            rows_scanned=rows_scanned,
            rows_skipped=rows_skipped,
            transactions=transactions,
            errors=errors,
            metadata=metadata,
        )


class GenericExcelParser(GenericCSVParser):
    parser_name = "generic_excel_parser"


class GenericPDFParser(BaseStatementParser):
    parser_name = "generic_pdf_parser"

    def parse(self, *, content: bytes, filename: str, content_type: str | None) -> ParserResultDTO:
        # Lightweight text extraction strategy for text-based PDFs only.
        decoded = content.decode("utf-8", errors="ignore")
        rows = [line.strip() for line in decoded.splitlines() if line.strip()]

        transactions: list[TransactionCreateDTO] = []
        rows_scanned = 0
        rows_skipped = 0

        for line in rows:
            rows_scanned += 1
            columns = [part.strip() for part in re.split(r"\s{2,}|,", line) if part.strip()]
            if len(columns) < 3:
                rows_skipped += 1
                continue

            normalized = normalize_transaction(
                date_value=columns[0],
                description_value=columns[1],
                debit_value=columns[2] if len(columns) > 2 else None,
                credit_value=columns[3] if len(columns) > 3 else None,
                amount_value=columns[4] if len(columns) > 4 else None,
                balance_value=columns[5] if len(columns) > 5 else None,
                currency=None,
                reference_number=None,
                raw_row={"line": line},
            )
            if normalized is None:
                rows_skipped += 1
                continue
            transactions.append(normalized)

        return ParserResultDTO(
            parser_name=self.parser_name,
            rows_scanned=rows_scanned,
            rows_skipped=rows_skipped,
            transactions=transactions,
            errors=[],
        )


class OCRParser(GenericPDFParser):
    parser_name = "ocr_pipeline"


class ParserRegistry:
    """Registry for parser implementations."""

    def __init__(self) -> None:
        self._parsers: dict[str, BaseStatementParser] = {
            "csv_parser": GenericCSVParser(),
            "excel_parser": GenericExcelParser(),
            "pdf_parser": GenericPDFParser(),
            "ocr_parser": OCRParser(),
            "generic_csv_parser": GenericCSVParser(),
            "generic_excel_parser": GenericExcelParser(),
            "generic_pdf_parser": GenericPDFParser(),
            "ocr_pipeline": OCRParser(),
            "unknown": GenericCSVParser(),
        }

    def get(self, parser_name: str) -> BaseStatementParser:
        return self._parsers.get(parser_name, self._parsers["generic_csv_parser"])


@dataclass
class ParserExecutionMetrics:
    parser_name: str
    duration_ms: int


class ParserFactory:
    """Factory facade that selects parser from registry and executes parse."""

    def __init__(self, *, registry: ParserRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        *,
        parser_name: str,
        content: bytes,
        filename: str,
        content_type: str | None,
    ) -> tuple[ParserResultDTO, ParserExecutionMetrics]:
        started = perf_counter()
        parser = self._registry.get(parser_name)
        result = parser.parse(content=content, filename=filename, content_type=content_type)
        metrics = ParserExecutionMetrics(
            parser_name=result.parser_name,
            duration_ms=int((perf_counter() - started) * 1000),
        )
        return result, metrics


def serialize_raw_row(raw_row: dict[str, Any]) -> str:
    """Serialize a raw row to stable JSON string for storage."""

    return json.dumps(raw_row, ensure_ascii=True, sort_keys=True)
