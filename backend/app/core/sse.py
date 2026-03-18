from __future__ import annotations

import enum
import json
from typing import Any, Dict


class SSEEventType(str, enum.Enum):
    JOB_STATUS = "job_status"
    VALIDATION = "validation"
    PAGE_START = "page_start"
    PAGE_DONE = "page_done"
    JOB_COMPLETE = "job_complete"
    ERROR = "error"


def format_sse_event(event_type: SSEEventType, data: Dict[str, Any]) -> str:
    json_data = json.dumps(data, ensure_ascii=False)
    return f"event: {event_type.value}\ndata: {json_data}\n\n"


def format_sse_keepalive() -> str:
    return ": keepalive\n\n"
