import json

from app.core.sse import SSEEventType, format_sse_event, format_sse_keepalive


def test_format_job_status_event():
    result = format_sse_event(
        SSEEventType.JOB_STATUS,
        {"job_id": "abc", "status": "processing", "queue_position": 2},
    )
    assert result.startswith("event: job_status\n")
    assert '"job_id": "abc"' in result
    assert result.endswith("\n\n")


def test_format_page_done_event():
    result = format_sse_event(
        SSEEventType.PAGE_DONE,
        {"page": 3, "content": "translated text", "elapsed_ms": 4200},
    )
    assert "event: page_done" in result
    data_line = result.split("\n")[1]
    assert data_line.startswith("data: ")
    parsed = json.loads(data_line[6:])
    assert parsed["page"] == 3
    assert parsed["elapsed_ms"] == 4200


def test_format_validation_event():
    result = format_sse_event(
        SSEEventType.VALIDATION,
        {"step": "QUOTA_CHECK", "status": "passed"},
    )
    assert "event: validation" in result


def test_format_job_complete_event():
    result = format_sse_event(
        SSEEventType.JOB_COMPLETE,
        {"job_id": "xyz", "download_url": "/download/xyz", "total_pages": 47},
    )
    assert "event: job_complete" in result


def test_format_error_event():
    result = format_sse_event(
        SSEEventType.ERROR,
        {"code": "QUOTA_EXCEEDED", "message": "Quota full"},
    )
    assert "event: error" in result


def test_keepalive():
    result = format_sse_keepalive()
    assert result == ": keepalive\n\n"
