"""Statement parser engine and parser registry for F-2.4."""

from __future__ import annotations

from abc import ABC, abstractmethod
import csv
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
import io
import json
import logging
import re
from time import perf_counter
from typing import Any
from xml.etree import ElementTree as ET
from zipfile import ZipFile

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

    if re.fullmatch(r"\d+(?:\.\d+)?", text):
        try:
            serial = int(float(text))
            if serial > 0:
                excel_epoch = datetime(1899, 12, 30)
                return (excel_epoch + timedelta(days=serial)).date()
        except (ValueError, OverflowError):
            pass

    formats = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%y",
        "%Y/%m/%d",
        "%d-%b-%Y",
        "%d-%b-%y",
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

    if text.startswith("(") and text.endswith(")"):
        text = f"-{text[1:-1].strip()}"

    sign = Decimal("1")
    if text.endswith("CR"):
        text = text.removesuffix("CR").strip()
        sign = Decimal("1")
    elif text.endswith("DR"):
        text = text.removesuffix("DR").strip()
        sign = Decimal("-1")

    text = text.replace(" ", "")
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
    parser_name = "csv_parser"

    _ROW_SKIP_TOKENS = {
        "opening balance",
        "closing balance",
        "grand total",
        "total",
        "summary",
        "statement summary",
        "generated on",
        "end of statement",
        "balance brought forward",
        "balance carried forward",
        "page",
    }

    @dataclass
    class ColumnMapping:
        date: int | None = None
        description: int | None = None
        debit: int | None = None
        credit: int | None = None
        amount: int | None = None
        balance: int | None = None
        reference_number: int | None = None
        transaction_type: int | None = None

    class StatementColumnMapper:
        _ALIASES: dict[str, tuple[str, ...]] = {
            "date": ("date", "txn date", "transaction date", "posting date", "value date", "tran date"),
            "description": (
                "description",
                "narration",
                "remarks",
                "transaction details",
                "particulars",
                "details",
            ),
            "debit": ("debit", "withdrawal", "dr", "withdrawals"),
            "credit": ("credit", "deposit", "cr", "deposits"),
            "amount": ("amount", "txn amount"),
            "balance": ("balance", "closing balance", "running balance", "available balance", "bal"),
            "reference_number": (
                "reference",
                "ref",
                "reference no",
                "txn id",
                "utr",
                "cheque no",
                "chqno",
                "chq no",
            ),
            "transaction_type": ("transaction type", "type"),
        }

        @staticmethod
        def _normalize_header(value: str) -> str:
            token = value.strip().lower().replace("_", " ").replace("-", " ")
            token = re.sub(r"[^a-z0-9\s]", "", token)
            token = re.sub(r"\s+", " ", token)
            return token.strip()

        def _match_field(self, token: str) -> str | None:
            for field, aliases in self._ALIASES.items():
                if token in aliases:
                    return field
                if len(token) >= 4 and any(
                    token.startswith(f"{alias} ")
                    or token.endswith(f" {alias}")
                    or alias.startswith(f"{token} ")
                    or alias.endswith(f" {token}")
                    for alias in aliases
                ):
                    return field
            return None

        def find_mapping(self, rows: list[list[str]]) -> tuple[int | None, GenericCSVParser.ColumnMapping]:
            best_idx: int | None = None
            best_mapping = GenericCSVParser.ColumnMapping()
            best_score = -1

            for idx, row in enumerate(rows[:40]):
                mapping = GenericCSVParser.ColumnMapping()
                score = 0
                for col_idx, raw_header in enumerate(row):
                    token = self._normalize_header(raw_header)
                    if not token:
                        continue
                    field = self._match_field(token)
                    if field is None:
                        continue
                    if getattr(mapping, field) is None:
                        setattr(mapping, field, col_idx)
                        score += 1

                if mapping.date is None or mapping.description is None:
                    continue

                if score > best_score:
                    best_score = score
                    best_idx = idx
                    best_mapping = mapping

            return best_idx, best_mapping

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

    @staticmethod
    def _value_at(row: list[str], idx: int | None) -> str | float | None:
        if idx is None or idx < 0 or idx >= len(row):
            return None
        raw = row[idx]
        if raw is None:
            return None
        value = str(raw).strip()
        if value == "":
            return None
        return value

    @staticmethod
    def _is_footer_or_summary(row: list[str], description: str | None) -> bool:
        joined = " ".join(cell.strip().lower() for cell in row if cell.strip())
        if not joined:
            return True

        if any(token in joined for token in GenericCSVParser._ROW_SKIP_TOKENS):
            return True

        if description and should_skip_row(description):
            return True

        return False

    @staticmethod
    def _read_delimited_rows(content: bytes) -> list[list[str]]:
        decoded = content.decode("utf-8", errors="ignore")
        lines = decoded.splitlines()
        reader = csv.reader(lines)
        return [list(row) for row in reader]

    @staticmethod
    def _column_index_from_cell_ref(cell_ref: str) -> int:
        col = 0
        for ch in cell_ref:
            if not ch.isalpha():
                break
            col = (col * 26) + (ord(ch.upper()) - ord("A") + 1)
        return max(col - 1, 0)

    def _read_xlsx_rows(self, content: bytes) -> list[list[str]]:
        rows: list[list[str]] = []
        with ZipFile(io.BytesIO(content)) as archive:
            shared_strings: list[str] = []
            if "xl/sharedStrings.xml" in archive.namelist():
                root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
                for si in root.findall("{*}si"):
                    text_parts = [node.text or "" for node in si.findall(".//{*}t")]
                    shared_strings.append("".join(text_parts))

            sheet_name = None
            for candidate in archive.namelist():
                if candidate.startswith("xl/worksheets/sheet") and candidate.endswith(".xml"):
                    sheet_name = candidate
                    break
            if sheet_name is None:
                return []

            sheet_root = ET.fromstring(archive.read(sheet_name))
            for row in sheet_root.findall(".//{*}row"):
                parsed_row: list[str] = []
                for cell in row.findall("{*}c"):
                    idx = self._column_index_from_cell_ref(cell.get("r", "A1"))
                    while len(parsed_row) <= idx:
                        parsed_row.append("")

                    cell_type = cell.get("t")
                    value_node = cell.find("{*}v")
                    inline_node = cell.find(".//{*}t")
                    value = ""
                    if cell_type == "s" and value_node is not None:
                        try:
                            value = shared_strings[int(value_node.text or "0")]
                        except (ValueError, IndexError):
                            value = value_node.text or ""
                    elif inline_node is not None:
                        value = inline_node.text or ""
                    elif value_node is not None:
                        value = value_node.text or ""

                    parsed_row[idx] = value

                rows.append(parsed_row)
        return rows

    def _read_rows(self, *, content: bytes, filename: str) -> list[list[str]]:
        lower = filename.lower()
        if lower.endswith(".xlsx"):
            try:
                return self._read_xlsx_rows(content)
            except Exception:
                return self._read_delimited_rows(content)
        return self._read_delimited_rows(content)

    def _normalize_from_row(
        self,
        *,
        row: list[str],
        row_number: int,
        mapping: ColumnMapping,
        metadata: dict[str, str],
    ) -> TransactionCreateDTO | None:
        date_value = self._value_at(row, mapping.date)
        description_value = self._value_at(row, mapping.description)
        debit_value = self._value_at(row, mapping.debit)
        credit_value = self._value_at(row, mapping.credit)
        amount_value = self._value_at(row, mapping.amount)
        balance_value = self._value_at(row, mapping.balance)
        reference_value = self._value_at(row, mapping.reference_number)
        tx_type_value = self._value_at(row, mapping.transaction_type)

        normalized = normalize_transaction(
            date_value=date_value,
            description_value=description_value,
            debit_value=debit_value,
            credit_value=credit_value,
            amount_value=amount_value,
            balance_value=balance_value,
            currency=metadata.get("currency"),
            reference_number=str(reference_value) if reference_value is not None else None,
            raw_row={"row_number": row_number, "columns": row},
        )
        if normalized is None:
            return None

        if tx_type_value:
            forced = str(tx_type_value).strip().lower()
            if forced in {"dr", "debit"}:
                normalized.transaction_type = "debit"
                if normalized.amount > 0:
                    normalized.amount = -normalized.amount
            elif forced in {"cr", "credit"}:
                normalized.transaction_type = "credit"
                if normalized.amount < 0:
                    normalized.amount = -normalized.amount

        return normalized

    def parse(self, *, content: bytes, filename: str, content_type: str | None) -> ParserResultDTO:
        logger.info("CSV opened", extra={"filename": filename, "content_type": content_type})
        rows = self._read_rows(content=content, filename=filename)
        decoded = content.decode("utf-8", errors="ignore")
        lines = decoded.splitlines()

        metadata = self._extract_metadata(lines)
        mapper = self.StatementColumnMapper()
        header_index, mapping = mapper.find_mapping(rows)

        if header_index is None:
            return ParserResultDTO(
                parser_name=self.parser_name,
                rows_read=len(rows),
                rows_parsed=0,
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
                "column_map": mapping.__dict__,
            },
        )

        transactions: list[TransactionCreateDTO] = []
        rows_read = 0
        rows_scanned = 0
        rows_skipped = 0
        errors: list[str] = []

        for row_number, row in enumerate(rows[header_index + 1 :], start=header_index + 2):
            rows_read += 1
            rows_scanned += 1
            try:
                if all(not cell.strip() for cell in row):
                    rows_skipped += 1
                    continue

                description_value = self._value_at(row, mapping.description)
                if self._is_footer_or_summary(row, description_value):
                    rows_skipped += 1
                    continue

                normalized = self._normalize_from_row(
                    row=row,
                    row_number=row_number,
                    mapping=mapping,
                    metadata=metadata,
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
            rows_read=rows_read,
            rows_parsed=len(transactions),
            rows_scanned=rows_scanned,
            rows_skipped=rows_skipped,
            transactions=transactions,
            errors=errors,
            metadata=metadata,
        )


class GenericExcelParser(GenericCSVParser):
    parser_name = "excel_parser"


class GenericPDFParser(BaseStatementParser):
    parser_name = "pdf_parser"

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
            rows_read=rows_scanned,
            rows_parsed=len(transactions),
            rows_scanned=rows_scanned,
            rows_skipped=rows_skipped,
            transactions=transactions,
            errors=[],
        )


class OCRParser(GenericPDFParser):
    parser_name = "ocr_parser"


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
