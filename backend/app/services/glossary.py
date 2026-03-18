from __future__ import annotations

import csv
import io
from typing import Dict, List, Optional


class GlossaryService:
    """Manage translation glossary terms."""

    def __init__(self, terms: Optional[List[Dict[str, str]]] = None):
        self._terms: List[Dict[str, str]] = terms or []

    @classmethod
    def from_csv(cls, csv_content: str) -> "GlossaryService":
        """Load glossary from CSV string (source_term,target_term,do_not_translate)."""
        reader = csv.DictReader(io.StringIO(csv_content))
        terms = []
        for row in reader:
            terms.append({
                "source": row.get("source_term", "").strip(),
                "target": row.get("target_term", "").strip(),
                "do_not_translate": row.get("do_not_translate", "false").lower() == "true",
            })
        return cls(terms)

    def get_prompt_injection(self) -> str:
        """Generate glossary section to inject into translation prompt."""
        if not self._terms:
            return ""

        lines = ["## Glossary / Technical Terms"]
        lines.append("The following terms should be translated or preserved exactly as specified:")
        lines.append("")

        for term in self._terms:
            if term.get("do_not_translate"):
                lines.append(f"- **{term['source']}** → DO NOT TRANSLATE (keep as-is)")
            elif term.get("target"):
                lines.append(f"- **{term['source']}** → **{term['target']}**")

        return "\n".join(lines)

    @property
    def terms(self) -> List[Dict[str, str]]:
        return self._terms

    def add_term(self, source: str, target: str, do_not_translate: bool = False) -> None:
        self._terms.append({
            "source": source,
            "target": target,
            "do_not_translate": do_not_translate,
        })

    def to_csv(self) -> str:
        """Export glossary to CSV string."""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["source_term", "target_term", "do_not_translate"])
        writer.writeheader()
        for term in self._terms:
            writer.writerow({
                "source_term": term["source"],
                "target_term": term["target"],
                "do_not_translate": str(term.get("do_not_translate", False)).lower(),
            })
        return output.getvalue()
