import pytest

from app.services.pdf_validator import PDFValidator, ValidationResult, ValidationStep


class TestFormatCheck:
    def test_valid_pdf_passes(self, tmp_path):
        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake content")
        result = PDFValidator.check_format(pdf)
        assert result.status == "passed"
        assert result.step == ValidationStep.FORMAT_CHECK

    def test_non_pdf_fails(self, tmp_path):
        txt = tmp_path / "test.txt"
        txt.write_bytes(b"not a pdf")
        result = PDFValidator.check_format(txt)
        assert result.status == "failed"
        assert result.step == ValidationStep.FORMAT_CHECK

    def test_empty_file_fails(self, tmp_path):
        f = tmp_path / "empty.pdf"
        f.write_bytes(b"")
        result = PDFValidator.check_format(f)
        assert result.status == "failed"

    def test_nonexistent_file_fails(self, tmp_path):
        f = tmp_path / "nope.pdf"
        result = PDFValidator.check_format(f)
        assert result.status == "failed"


class TestSizeCheck:
    def test_within_limit_passes(self, tmp_path):
        pdf = tmp_path / "small.pdf"
        pdf.write_bytes(b"%PDF-" + b"x" * 1000)
        result = PDFValidator.check_size(pdf, max_mb=50)
        assert result.status == "passed"

    def test_over_limit_fails(self, tmp_path):
        pdf = tmp_path / "big.pdf"
        # 51 MB
        pdf.write_bytes(b"%PDF-" + b"x" * (51 * 1024 * 1024))
        result = PDFValidator.check_size(pdf, max_mb=50)
        assert result.status == "failed"
        assert result.step == ValidationStep.SIZE_CHECK

    def test_no_limit_always_passes(self, tmp_path):
        pdf = tmp_path / "any.pdf"
        pdf.write_bytes(b"%PDF-" + b"x" * 1000)
        result = PDFValidator.check_size(pdf, max_mb=None)
        assert result.status == "passed"


class TestQuotaCheck:
    def test_sufficient_quota_passes(self):
        result = PDFValidator.check_quota(
            pages=10,
            daily_used=40,
            daily_limit=50,
            monthly_used=400,
            monthly_limit=500,
        )
        assert result.status == "passed"

    def test_daily_exceeded_fails(self):
        result = PDFValidator.check_quota(
            pages=10,
            daily_used=45,
            daily_limit=50,
            monthly_used=0,
            monthly_limit=500,
        )
        assert result.status == "failed"

    def test_monthly_exceeded_fails(self):
        result = PDFValidator.check_quota(
            pages=10,
            daily_used=0,
            daily_limit=50,
            monthly_used=495,
            monthly_limit=500,
        )
        assert result.status == "failed"

    def test_unlimited_quota_always_passes(self):
        result = PDFValidator.check_quota(
            pages=999,
            daily_used=999,
            daily_limit=None,
            monthly_used=999,
            monthly_limit=None,
        )
        assert result.status == "passed"

    def test_exact_at_daily_limit_passes(self):
        result = PDFValidator.check_quota(
            pages=5,
            daily_used=45,
            daily_limit=50,
            monthly_used=0,
            monthly_limit=500,
        )
        assert result.status == "passed"


class TestMalwareScan:
    def test_returns_warning_when_not_configured(self, tmp_path):
        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"%PDF-1.4")
        result = PDFValidator.check_malware(pdf)
        assert result.status == "warning"
        assert result.step == ValidationStep.MALWARE_SCAN
