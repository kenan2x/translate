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
        """Translate a PDF file using PDFMathTranslate (pdf2zh).

        Returns:
            Path to translated PDF
        """
        os.makedirs(output_dir, exist_ok=True)

        input_file = Path(input_path)
        output_path = str(Path(output_dir) / f"{input_file.stem}_tr.pdf")

        # pdf2zh env variable'lardan okur
        os.environ["OPENAI_BASE_URL"] = self.vllm_base_url
        os.environ["OPENAI_API_KEY"] = self.vllm_api_key
        os.environ["OPENAI_MODEL"] = self.vllm_model

        try:
            from pdf2zh import translate as pdf2zh_translate
            from pdf2zh.doclayout import OnnxModel

            logger.info(
                "pdf2zh baslatiyor: model=%s, endpoint=%s, thread=%d",
                self.vllm_model, self.vllm_base_url, self.thread_count,
            )

            # DocLayout-YOLO model yukle
            layout_model = OnnxModel.load_available()
            if layout_model is None:
                raise RuntimeError("DocLayout-YOLO model yuklenemedi")
            logger.info("DocLayout-YOLO model yuklendi")

            params = {
                "lang_in": "en",
                "lang_out": "tr",
                "service": f"openai:{self.vllm_model}",
                "thread": self.thread_count,
                "callback": callback,
                "model": layout_model,
            }

            # pdf2zh.translate dosya listesi alir, tuple doner (mono, dual)
            file_mono, file_dual = pdf2zh_translate(
                files=[input_path], **params
            )[0]

            # mono = sadece ceviri, dual = iki dilli
            # mono dosyayi output_path'e kopyala
            result = file_mono if file_mono and Path(file_mono).exists() else file_dual

            if result and Path(result).exists():
                import shutil
                shutil.copy(result, output_path)
                logger.info("Ceviri tamamlandi: %s", output_path)
            else:
                raise RuntimeError(f"pdf2zh cikti dosyasi bulunamadi: mono={file_mono}, dual={file_dual}")

        except ImportError:
            logger.warning("pdf2zh not installed, using mock translation")
            import shutil
            shutil.copy(input_path, output_path)
            if callback:
                callback(1, 1)

        return output_path
