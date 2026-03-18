from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel

from app.api.v1.admin.users import require_admin

router = APIRouter(prefix="/admin/glossary", tags=["admin"])


class GlossaryTermRequest(BaseModel):
    source_term: str
    target_term: str
    do_not_translate: bool = False
    context: str = ""


@router.get("")
async def list_terms(
    page: int = 1,
    per_page: int = 50,
    admin: Dict = Depends(require_admin),
):
    """List all glossary terms."""
    # TODO: DB query
    return {"terms": [], "total": 0, "page": page, "per_page": per_page}


@router.post("")
async def add_term(
    body: GlossaryTermRequest,
    admin: Dict = Depends(require_admin),
):
    """Add a new glossary term."""
    # TODO: DB insert + audit log
    return {"source_term": body.source_term, "target_term": body.target_term, "created": True}


@router.put("/{term_id}")
async def update_term(
    term_id: int,
    body: GlossaryTermRequest,
    admin: Dict = Depends(require_admin),
):
    """Update an existing glossary term."""
    # TODO: DB update + audit log
    return {"term_id": term_id, "updated": True}


@router.delete("/{term_id}")
async def delete_term(
    term_id: int,
    admin: Dict = Depends(require_admin),
):
    """Delete a glossary term."""
    # TODO: DB delete + audit log
    return {"term_id": term_id, "deleted": True}


@router.post("/import")
async def import_csv(
    file: UploadFile = File(...),
    admin: Dict = Depends(require_admin),
):
    """Bulk import glossary terms from CSV."""
    content = await file.read()
    csv_text = content.decode("utf-8")

    from app.services.glossary import GlossaryService
    svc = GlossaryService.from_csv(csv_text)

    # TODO: Bulk insert to DB + audit log
    return {"imported": len(svc.terms), "terms": len(svc.terms)}
