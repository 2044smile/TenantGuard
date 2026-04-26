"""
임차권등기명령 신청 API
POST /api/v1/applications          — 신청 생성 & 서류 수집 시작
GET  /api/v1/applications/{id}     — 신청 상태 조회
POST /api/v1/applications/{id}/documents — 서류 업로드 (계약서, 해지통지서)
GET  /api/v1/applications/{id}/preview   — 전자소송 미리보기
POST /api/v1/applications/{id}/submit    — 최종 제출
WS   /api/v1/applications/{id}/ws        — 진행률 실시간 스트림
"""
import uuid
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, WebSocket, Depends
from fastapi.responses import JSONResponse
from app.schemas.application import (
    ApplicationCreate,
    ApplicationResponse,
    PreviewResponse,
    SubmitResponse,
    FeeCalculation,
)
from app.core.redis_client import (
    create_session,
    get_session,
    store_cert,
    get_progress,
    delete_session,
    delete_cert,
)
from app.core.storage import upload_document
from app.workers.tasks import collect_documents, analyze_documents, delete_application_data

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/applications", tags=["Applications"])


# ── 신청 생성 ─────────────────────────────────────────────────────────────────

@router.post("", response_model=dict, status_code=202)
async def create_application(
    application_data: ApplicationCreate,
    cert_password: str = Form(...),
    cert_file: UploadFile = File(...),
):
    """
    임차권등기명령 신청 생성.
    공동인증서 + 기본 정보 수신 → 서류 자동 수집 시작.
    """
    application_id = str(uuid.uuid4())

    # 공동인증서 Redis에 임시 저장 (5분 TTL)
    cert_bytes = await cert_file.read()
    if not cert_bytes:
        raise HTTPException(status_code=400, detail="공동인증서 파일이 비어있습니다.")

    session_id = await create_session(
        {
            "application_id": application_id,
            "tenant_name": application_data.tenant.name,
            "created_at": datetime.utcnow().isoformat(),
        }
    )
    await store_cert(session_id, cert_bytes)

    # 비동기 서류 수집 태스크 발행
    task_data = {
        **application_data.model_dump(),
        "cert_password": cert_password,  # 메모리에서만 사용, DB 미저장
    }
    # resident_number는 크롤링에만 사용, 로그에 남기지 않음
    collect_documents.delay(application_id, session_id, task_data)

    return {
        "application_id": application_id,
        "session_id": session_id,
        "status": "collecting",
        "message": "서류 자동 수집을 시작했습니다. 진행 상황을 WebSocket으로 확인하세요.",
        "fee": FeeCalculation().model_dump() | {"total": FeeCalculation().total},
    }


# ── 상태 조회 ─────────────────────────────────────────────────────────────────

@router.get("/{application_id}/status")
async def get_application_status(application_id: str):
    """서류 수집 진행 상태 조회"""
    progress = await get_progress(application_id)
    if not progress:
        raise HTTPException(status_code=404, detail="신청 건을 찾을 수 없습니다.")
    return progress


# ── 서류 업로드 (계약서, 해지통지서) ─────────────────────────────────────────

@router.post("/{application_id}/documents")
async def upload_document_file(
    application_id: str,
    doc_type: str = Form(...),    # "lease_contract" | "termination_notice" | "floor_plan"
    file: UploadFile = File(...),
):
    """
    사용자가 직접 업로드하는 서류 처리.
    업로드 즉시 AI 분석 태스크 발행.
    """
    allowed_types = {"lease_contract", "termination_notice", "floor_plan"}
    if doc_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"허용되지 않는 서류 유형: {doc_type}")

    file_bytes = await file.read()
    if len(file_bytes) > 20 * 1024 * 1024:  # 20MB 제한
        raise HTTPException(status_code=413, detail="파일 크기는 20MB를 초과할 수 없습니다.")

    storage_key = f"applications/{application_id}/{doc_type}.pdf"
    upload_document(storage_key, file_bytes, content_type=file.content_type or "application/pdf")

    # 계약서 / 해지통지서는 즉시 AI 분석
    if doc_type in {"lease_contract", "termination_notice"}:
        analyze_documents.delay(application_id, {doc_type: storage_key})

    return {
        "application_id": application_id,
        "doc_type": doc_type,
        "storage_key": storage_key,
        "message": "업로드 완료. 분석을 시작합니다.",
    }


# ── 전자소송 미리보기 ─────────────────────────────────────────────────────────

@router.get("/{application_id}/preview", response_model=PreviewResponse)
async def get_preview(application_id: str, session_id: str):
    """
    전자소송 신청서 미리보기 HTML 반환.
    이 단계에서 사용자가 내용을 최종 확인한다.
    """
    session = await get_session(session_id)
    if not session or session.get("application_id") != application_id:
        raise HTTPException(status_code=403, detail="세션이 유효하지 않습니다.")

    # TODO: EcourtFiller.preview() 결과를 Redis/DB에서 조회
    return PreviewResponse(
        application_id=application_id,
        preview_html="<p>미리보기 생성 중...</p>",
        fee_breakdown={
            "stamp_duty": 1800,
            "delivery_fee": 31200,
            "registration_tax": 7200,
            "registry_commission": 3000,
        },
        total_fee=43200,
    )


# ── 최종 제출 ─────────────────────────────────────────────────────────────────

@router.post("/{application_id}/submit", response_model=SubmitResponse)
async def submit_application(application_id: str, session_id: str):
    """
    사용자 최종 승인 → 전자소송 제출.
    제출 후 개인정보 즉시 삭제 예약.
    """
    session = await get_session(session_id)
    if not session or session.get("application_id") != application_id:
        raise HTTPException(status_code=403, detail="세션이 유효하지 않습니다.")

    # TODO: EcourtFiller.submit() 실행 및 접수번호 획득
    receipt_number = f"TG-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    # 개인정보 삭제 태스크 예약 (1분 후)
    delete_application_data.apply_async(
        args=[application_id, session_id],
        countdown=60,
    )

    return SubmitResponse(
        application_id=application_id,
        receipt_number=receipt_number,
        submitted_at=datetime.utcnow(),
    )


# ── WebSocket 진행률 스트림 ────────────────────────────────────────────────────

@router.websocket("/{application_id}/ws")
async def progress_websocket(websocket: WebSocket, application_id: str):
    """실시간 진행률을 WebSocket으로 푸시"""
    import asyncio
    await websocket.accept()
    try:
        while True:
            progress = await get_progress(application_id)
            if progress:
                await websocket.send_json(progress)
                if progress.get("status") in {"ready", "submitted", "failed"}:
                    break
            await asyncio.sleep(2)
    except Exception:
        pass
    finally:
        await websocket.close()
