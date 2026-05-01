"""Celery 비동기 작업 — 크롤링은 시간이 오래 걸리므로 백그라운드에서 실행"""
import asyncio
import logging
from celery import Celery
from app.config import settings

logger = logging.getLogger(__name__)

celery_app = Celery(
    "tenantguard",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Seoul",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,   # 크롤링은 1건씩 처리
)


@celery_app.task(bind=True, name="collect_documents", max_retries=2)
def collect_documents(self, application_id: str, session_id: str, application_data: dict):
    """서류 자동 수집 태스크"""
    try:
        from app.services.orchestrator import DocumentOrchestrator
        orchestrator = DocumentOrchestrator(application_id, session_id)
        result = asyncio.run(orchestrator.run(application_data))
        return result
    except Exception as exc:
        logger.error(f"[collect_documents] 실패: {exc}")
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(bind=True, name="analyze_documents", max_retries=1)
def analyze_documents(self, application_id: str, doc_paths: dict):
    """AI 문서 분석 태스크 (업로드된 계약서 / 해지통지서 분석)"""
    try:
        from app.services.document_analyzer import DocumentAnalyzer
        from app.core.storage import download_document

        analyzer = DocumentAnalyzer()
        results = {}

        for doc_type, storage_key in doc_paths.items():
            file_bytes = download_document(storage_key)
            if not file_bytes:
                logger.warning(f"파일 없음: {storage_key}")
                continue

            text = analyzer.extract_text(file_bytes, filename=storage_key)

            if doc_type == "lease_contract":
                parsed = analyzer.parse_contract(text)
                errors = analyzer.validate_contract(parsed)
                results[doc_type] = {"parsed": parsed, "errors": errors}
            elif doc_type == "termination_notice":
                parsed = analyzer.parse_termination_notice(text)
                results[doc_type] = {"parsed": parsed, "errors": []}

        return results
    except Exception as exc:
        logger.error(f"[analyze_documents] 실패: {exc}")
        raise self.retry(exc=exc, countdown=10)


@celery_app.task(name="delete_application_data")
def delete_application_data(application_id: str, session_id: str):
    """제출 완료 후 개인정보 삭제"""
    from app.core.storage import delete_application_documents
    from app.core.redis_client import delete_session

    delete_application_documents(application_id)
    asyncio.run(delete_session(session_id))
    logger.info(f"[delete_application_data] 개인정보 삭제 완료: {application_id}")
