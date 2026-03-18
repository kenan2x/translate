from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import fitz  # PyMuPDF
from openai import OpenAI

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Sen profesyonel bir teknik dokuman cevirmensin. "
    "Asagidaki Ingilizce metni Turkce'ye cevir.\n\n"
    "Kurallar:\n"
    "- Teknik terimleri oldugu gibi birak (API, HTTP, SSL, TCP, GPU, vb.)\n"
    "- Dogal ve akici Turkce kullan\n"
    "- Sadece cevirilmis metni don, ek aciklama ekleme\n"
    "- Bos metin gelirse bos dondur\n"
    "- Tablo ve liste yapisini koru"
)


@dataclass
class PageResult:
    page: int
    total: int
    original: str
    translated: str
    elapsed_ms: int


class PDFTranslator:
    def __init__(
        self,
        vllm_base_url: str,
        vllm_model: str,
        vllm_api_key: str = "dummy",
        thread_count: int = 4,
    ):
        self.vllm_base_url = vllm_base_url
        self.vllm_model = vllm_model
        self.vllm_api_key = vllm_api_key
        self.thread_count = thread_count
        self.client = OpenAI(
            base_url=vllm_base_url,
            api_key=vllm_api_key,
            timeout=120.0,
        )

    def extract_pages(self, pdf_path: str) -> list[dict]:
        """Extract text from each page using PyMuPDF."""
        doc = fitz.open(pdf_path)
        pages = []
        for i in range(doc.page_count):
            page = doc[i]
            text = page.get_text().strip()
            pages.append({"page": i + 1, "text": text})
        doc.close()
        return pages

    def translate_page(self, text: str) -> str:
        """Translate a single page text using vLLM (OpenAI-compatible API)."""
        if not text or len(text.strip()) < 3:
            return text

        response = self.client.chat.completions.create(
            model=self.vllm_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0.3,
            max_tokens=4096,
        )
        return response.choices[0].message.content or ""

    def translate(
        self,
        pdf_path: str,
        callback: Optional[Callable[[PageResult], None]] = None,
    ) -> list[PageResult]:
        """Translate all pages of a PDF, calling callback per page.

        Returns:
            List of PageResult with original and translated text per page.
        """
        pages = self.extract_pages(pdf_path)
        total = len(pages)
        results: list[PageResult] = []

        logger.info(
            "Ceviri basliyor: %d sayfa, model=%s, endpoint=%s",
            total, self.vllm_model, self.vllm_base_url,
        )

        for page_data in pages:
            page_num = page_data["page"]
            text = page_data["text"]

            start = time.monotonic()
            try:
                translated = self.translate_page(text)
            except Exception:
                logger.exception("Sayfa %d cevirisi basarisiz", page_num)
                translated = f"[Ceviri hatasi — sayfa {page_num}]"
            elapsed_ms = int((time.monotonic() - start) * 1000)

            result = PageResult(
                page=page_num,
                total=total,
                original=text,
                translated=translated,
                elapsed_ms=elapsed_ms,
            )
            results.append(result)

            logger.info(
                "Sayfa %d/%d cevirildi (%d ms)", page_num, total, elapsed_ms,
            )

            if callback:
                callback(result)

        return results
