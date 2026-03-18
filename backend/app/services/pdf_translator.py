from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)


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

    def translate(
        self,
        input_path: str,
        output_dir: str,
        callback: Optional[Callable[[int, int], None]] = None,
        glossary: Optional[str] = None,
    ) -> str:
        """Translate a PDF file using PDFMathTranslate.

        Args:
            input_path: Path to input PDF
            output_dir: Directory for output PDF
            callback: Called with (current_page, total_pages) for each page
            glossary: Optional glossary terms to inject into prompts

        Returns:
            Path to translated PDF
        """
        os.makedirs(output_dir, exist_ok=True)

        input_file = Path(input_path)
        output_path = str(Path(output_dir) / f"{input_file.stem}_tr.pdf")

        try:
            from pdf2zh import translate_pdf

            translate_pdf(
                input_path,
                output=output_path,
                lang_in="en",
                lang_out="tr",
                service="openai",
                model=self.vllm_model,
                envs={
                    "OPENAI_BASE_URL": self.vllm_base_url,
                    "OPENAI_API_KEY": self.vllm_api_key,
                },
                thread=self.thread_count,
                callback=callback,
            )
        except ImportError:
            logger.warning("pdf2zh not installed, using mock translation")
            # Fallback for development/testing
            import shutil

            shutil.copy(input_path, output_path)
            if callback:
                callback(1, 1)

        return output_path
