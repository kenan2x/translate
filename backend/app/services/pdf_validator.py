from __future__ import annotations

import enum
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


class ValidationStep(str, enum.Enum):
    FORMAT_CHECK = "FORMAT_CHECK"
    SIZE_CHECK = "SIZE_CHECK"
    ENCRYPTION_CHECK = "ENCRYPTION_CHECK"
    PAGE_COUNT = "PAGE_COUNT"
    QUOTA_CHECK = "QUOTA_CHECK"
    MALWARE_SCAN = "MALWARE_SCAN"
    SCAN_DETECTION = "SCAN_DETECTION"


@dataclass
class ValidationResult:
    step: ValidationStep
    status: str  # "passed", "failed", "warning"
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


class PDFValidator:
    @staticmethod
    def check_format(file_path: Path) -> ValidationResult:
        try:
            with open(file_path, "rb") as f:
                header = f.read(5)
            if header == b"%PDF-":
                return ValidationResult(
                    step=ValidationStep.FORMAT_CHECK,
                    status="passed",
                    message="Valid PDF format",
                )
            return ValidationResult(
                step=ValidationStep.FORMAT_CHECK,
                status="failed",
                message="File is not a valid PDF (missing %PDF- header)",
            )
        except Exception as e:
            return ValidationResult(
                step=ValidationStep.FORMAT_CHECK,
                status="failed",
                message=f"Cannot read file: {e}",
            )

    @staticmethod
    def check_size(file_path: Path, max_mb: Optional[int]) -> ValidationResult:
        if max_mb is None:
            return ValidationResult(
                step=ValidationStep.SIZE_CHECK,
                status="passed",
                message="No size limit",
            )
        size_bytes = file_path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        if size_mb <= max_mb:
            return ValidationResult(
                step=ValidationStep.SIZE_CHECK,
                status="passed",
                message=f"File size {size_mb:.1f} MB within limit ({max_mb} MB)",
                details={"size_mb": round(size_mb, 1), "max_mb": max_mb},
            )
        return ValidationResult(
            step=ValidationStep.SIZE_CHECK,
            status="failed",
            message=f"File size {size_mb:.1f} MB exceeds limit ({max_mb} MB)",
            details={"size_mb": round(size_mb, 1), "max_mb": max_mb},
        )

    @staticmethod
    def check_encryption(file_path: Path) -> ValidationResult:
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(str(file_path))
            if doc.is_encrypted:
                doc.close()
                return ValidationResult(
                    step=ValidationStep.ENCRYPTION_CHECK,
                    status="failed",
                    message="PDF is encrypted or password-protected",
                )
            doc.close()
            return ValidationResult(
                step=ValidationStep.ENCRYPTION_CHECK,
                status="passed",
                message="PDF is not encrypted",
            )
        except ImportError:
            return ValidationResult(
                step=ValidationStep.ENCRYPTION_CHECK,
                status="warning",
                message="PyMuPDF not available, skipping encryption check",
            )
        except Exception as e:
            return ValidationResult(
                step=ValidationStep.ENCRYPTION_CHECK,
                status="failed",
                message=f"Error checking encryption: {e}",
            )

    @staticmethod
    def check_page_count(
        file_path: Path, max_pages: Optional[int]
    ) -> ValidationResult:
        try:
            import fitz

            doc = fitz.open(str(file_path))
            pages = doc.page_count
            doc.close()
        except ImportError:
            return ValidationResult(
                step=ValidationStep.PAGE_COUNT,
                status="warning",
                message="PyMuPDF not available, cannot count pages",
                details={"pages": 0},
            )
        except Exception as e:
            return ValidationResult(
                step=ValidationStep.PAGE_COUNT,
                status="failed",
                message=f"Cannot read PDF pages: {e}",
            )

        if max_pages is None or pages <= max_pages:
            return ValidationResult(
                step=ValidationStep.PAGE_COUNT,
                status="passed",
                message=f"PDF has {pages} pages",
                details={"pages": pages, "max_pages": max_pages},
            )
        return ValidationResult(
            step=ValidationStep.PAGE_COUNT,
            status="failed",
            message=f"PDF has {pages} pages, exceeds limit ({max_pages})",
            details={"pages": pages, "max_pages": max_pages},
        )

    @staticmethod
    def check_quota(
        pages: int,
        daily_used: int,
        daily_limit: Optional[int],
        monthly_used: int,
        monthly_limit: Optional[int],
    ) -> ValidationResult:
        # Unlimited
        if daily_limit is None and monthly_limit is None:
            return ValidationResult(
                step=ValidationStep.QUOTA_CHECK,
                status="passed",
                message="Unlimited quota",
            )

        # Daily check
        if daily_limit is not None and (daily_used + pages) > daily_limit:
            return ValidationResult(
                step=ValidationStep.QUOTA_CHECK,
                status="failed",
                message=f"Daily quota would be exceeded ({daily_used + pages}/{daily_limit})",
                details={
                    "daily_used": daily_used,
                    "daily_limit": daily_limit,
                    "pages_requested": pages,
                },
            )

        # Monthly check
        if monthly_limit is not None and (monthly_used + pages) > monthly_limit:
            return ValidationResult(
                step=ValidationStep.QUOTA_CHECK,
                status="failed",
                message=f"Monthly quota would be exceeded ({monthly_used + pages}/{monthly_limit})",
                details={
                    "monthly_used": monthly_used,
                    "monthly_limit": monthly_limit,
                    "pages_requested": pages,
                },
            )

        return ValidationResult(
            step=ValidationStep.QUOTA_CHECK,
            status="passed",
            message="Quota sufficient",
            details={
                "daily_used": daily_used,
                "daily_limit": daily_limit,
                "monthly_used": monthly_used,
                "monthly_limit": monthly_limit,
            },
        )

    @staticmethod
    def check_malware(file_path: Path) -> ValidationResult:
        # ClamAV integration - optional
        return ValidationResult(
            step=ValidationStep.MALWARE_SCAN,
            status="warning",
            message="ClamAV not configured, skipping malware scan",
        )

    @staticmethod
    def check_scan_detection(file_path: Path) -> ValidationResult:
        # Basic heuristic: check if PDF has selectable text
        try:
            import fitz

            doc = fitz.open(str(file_path))
            total_text = ""
            for page_num in range(min(3, doc.page_count)):
                total_text += doc[page_num].get_text()
            doc.close()

            if len(total_text.strip()) < 50:
                return ValidationResult(
                    step=ValidationStep.SCAN_DETECTION,
                    status="warning",
                    message="PDF appears to be scanned (little or no selectable text). OCR may be needed.",
                    details={"text_length": len(total_text.strip())},
                )
            return ValidationResult(
                step=ValidationStep.SCAN_DETECTION,
                status="passed",
                message="PDF has selectable text",
                details={"text_length": len(total_text.strip())},
            )
        except ImportError:
            return ValidationResult(
                step=ValidationStep.SCAN_DETECTION,
                status="warning",
                message="PyMuPDF not available, skipping scan detection",
            )

    @classmethod
    def validate_all(
        cls,
        file_path: Path,
        max_mb: Optional[int],
        max_pages: Optional[int],
        daily_used: int,
        daily_limit: Optional[int],
        monthly_used: int,
        monthly_limit: Optional[int],
    ) -> List[ValidationResult]:
        results = []

        # 1. Format check
        fmt = cls.check_format(file_path)
        results.append(fmt)
        if fmt.status == "failed":
            return results

        # 2. Size check
        size = cls.check_size(file_path, max_mb)
        results.append(size)
        if size.status == "failed":
            return results

        # 3. Encryption check
        enc = cls.check_encryption(file_path)
        results.append(enc)
        if enc.status == "failed":
            return results

        # 4. Page count
        pc = cls.check_page_count(file_path, max_pages)
        results.append(pc)
        if pc.status == "failed":
            return results

        pages = pc.details.get("pages", 0)

        # 5. Quota check
        quota = cls.check_quota(pages, daily_used, daily_limit, monthly_used, monthly_limit)
        results.append(quota)
        if quota.status == "failed":
            return results

        # 6. Malware scan
        results.append(cls.check_malware(file_path))

        # 7. Scan detection
        results.append(cls.check_scan_detection(file_path))

        return results
