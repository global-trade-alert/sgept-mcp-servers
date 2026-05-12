"""FastAPI routes:
- POST /v1/queries           → 202 + query_id (enqueue)
- GET  /v1/queries/{id}      → status-aware response
- GET  /.well-known/...      → public verify key
- GET  /healthz              → liveness
"""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request, Response, status
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse

from .. import db
from ..config import get_settings
from ..errors import APIError, ErrorCode
from ..models import (
    AuditRecord,
    CreateQueryRequest,
    CreateQueryResponse,
    PerspectiveOutput,
    QueryCompletedResponse,
    QueryFailedResponse,
    QueryInProgressResponse,
    QueryResult,
    Status,
    Tier,
    new_query_id,
    utc_now,
)
from ..orchestrator import resolve_perspectives
from . import rate_limit
from .auth import require_api_key

router = APIRouter()


# ── POST /v1/queries ─────────────────────────────────────────────────────────


@router.post("/v1/queries", status_code=status.HTTP_202_ACCEPTED)
async def create_query(
    body: CreateQueryRequest,
    auth: tuple[str, str] = Depends(require_api_key),
) -> CreateQueryResponse:
    api_key, org_id = auth
    rate_limit.check_and_record(org_id, body.tier)

    settings = get_settings()
    perspectives = resolve_perspectives(body.perspectives)
    qid = new_query_id()
    submitted = utc_now()
    ceiling = (
        settings.standard_ceiling_seconds
        if body.tier == Tier.STANDARD
        else settings.premium_ceiling_seconds
    )
    estimated = submitted + timedelta(seconds=ceiling)

    db.enqueue_query(
        query_id=qid,
        org_id=org_id,
        api_key=api_key,
        scenario=body.scenario,
        horizon=body.horizon.value,
        tier=body.tier,
        perspectives_invoked=perspectives,
    )

    return CreateQueryResponse(
        query_id=qid,
        status=Status.QUEUED,
        tier=body.tier,
        submitted_at_utc=submitted,
        estimated_completion_utc=estimated,
    )


# ── GET /v1/queries/{id} ──────────────────────────────────────────────────────


@router.get("/v1/queries/{query_id}")
async def get_query(
    query_id: UUID,
    auth: tuple[str, str] = Depends(require_api_key),
) -> Response:
    _, org_id = auth
    row = db.get_query(query_id)
    if row is None:
        raise APIError(ErrorCode.QUERY_NOT_FOUND, f"unknown query_id {query_id}")
    if row["org_id"] != org_id:
        # Don't leak existence — same as not found
        raise APIError(ErrorCode.QUERY_NOT_FOUND, f"unknown query_id {query_id}")

    perspectives_invoked = json.loads(row["perspectives_invoked"])
    perspectives_completed = json.loads(row["perspectives_completed"] or "[]")
    failed_perspectives = json.loads(row["failed_perspectives"] or "[]")
    status_val = Status(row["status"])

    if status_val in (Status.QUEUED, Status.RUNNING):
        started = row["started_at_utc"]
        elapsed = 0
        if started:
            from datetime import datetime
            elapsed = int((utc_now() - datetime.fromisoformat(started)).total_seconds())
        body = QueryInProgressResponse(
            query_id=query_id,
            status=status_val,
            perspectives_total=len(perspectives_invoked),
            perspectives_completed=len(perspectives_completed),
            elapsed_seconds=elapsed,
        )
        return JSONResponse(body.model_dump(mode="json"), status_code=200)

    if status_val == Status.FAILED:
        audit_dict = json.loads(row["audit_record_json"])
        sig = row["audit_signature"]
        body = QueryFailedResponse(
            query_id=query_id,
            status=Status.FAILED,
            audit_record=AuditRecord.model_validate(audit_dict),
            audit_signature=sig,
            failed_perspectives=failed_perspectives,
        )
        return JSONResponse(body.model_dump(mode="json"), status_code=503)

    # completed or partial
    audit_dict = json.loads(row["audit_record_json"])
    sig = row["audit_signature"]
    result_dict = json.loads(row["result_json"])
    result = QueryResult.model_validate(
        {k: v for k, v in result_dict.items() if k != "failed_perspectives"}
    )
    body = QueryCompletedResponse(
        query_id=query_id,
        status=status_val,
        partial=(status_val == Status.PARTIAL),
        failed_perspectives=failed_perspectives,
        result=result,
        audit_record=AuditRecord.model_validate(audit_dict),
        audit_signature=sig,
    )
    return JSONResponse(body.model_dump(mode="json"), status_code=200)


# ── Public key + liveness ────────────────────────────────────────────────────


@router.get("/.well-known/iran-monitor-signing-key.pub")
async def public_key() -> Response:
    settings = get_settings()
    p = settings.signing_pub_key_path
    if not p.exists():
        raise APIError(ErrorCode.WORKER_DOWN, "signing key not provisioned")
    return FileResponse(p, media_type="application/octet-stream")


@router.get("/healthz")
async def healthz() -> PlainTextResponse:
    return PlainTextResponse("ok")
