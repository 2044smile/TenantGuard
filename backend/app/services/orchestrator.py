"""
서류 수집 오케스트레이터

수집 방식 요약:
  등기부등본:    고객 직접 업로드 (/documents 엔드포인트)
  주민등록초본:  고객 직접 업로드 (/documents 엔드포인트)
  건축물대장:    OpenAPI → data.go.kr (무료, 자동)
"""
import logging
import json
from app.core.redis_client import set_progress
from app.core.storage import upload_document
from app.services.gov24_api import BuildingLedgerApiClient

logger = logging.getLogger(__name__)


class DocumentOrchestrator:
    def __init__(self, application_id: str, session_id: str):
        self.application_id = application_id
        self.session_id = session_id

    async def run(self, application_data: dict) -> dict:
        """
        건축물대장 API 자동 수집.
        등기부등본·주민등록초본은 고객이 직접 업로드.

        Returns:
            {"building_ledger": "s3-key", "errors": [...]}
        """
        await self._update_progress(10, "건축물대장 조회 중", "collecting")

        prop = application_data["property"]
        results = {}
        errors = []

        try:
            key = await self._collect_building_ledger_api(
                sigungu_code=prop.get("sigungu_code", ""),
                bdong_code=prop.get("bdong_code", ""),
                bun=prop.get("bun", "0000"),
                ji=prop.get("ji", "0000"),
                plat_gb_cd=prop.get("plat_gb_cd", "0"),
            )
            results["building_ledger"] = key
        except Exception as e:
            logger.warning(f"건축물대장 API 수집 실패 (무시): {e}")
            errors.append(f"건축물대장 조회 실패: {e}")

        results["errors"] = errors
        await self._update_progress(100, "준비 완료", "ready")
        return results

    async def _collect_building_ledger_api(
        self, sigungu_code: str, bdong_code: str,
        bun: str = "0000", ji: str = "0000", plat_gb_cd: str = "0",
    ) -> str:
        """건축물대장 표제부 OpenAPI 조회 → JSON 저장"""
        if not sigungu_code or not bdong_code:
            raise RuntimeError("시군구코드/법정동코드 없음")
        client = BuildingLedgerApiClient()
        info = await client.get_building_info(sigungu_code, bdong_code, bun, ji, plat_gb_cd)
        if not info:
            raise RuntimeError("건축물대장 조회 결과 없음")
        key = f"applications/{self.application_id}/building_ledger.json"
        upload_document(key, json.dumps(info, ensure_ascii=False).encode(), content_type="application/json")
        logger.info(f"[orchestrator] 건축물대장 API 수집 완료: {key}")
        return key

    async def _update_progress(self, progress: int, message: str, status: str) -> None:
        await set_progress(
            self.application_id,
            {
                "application_id": self.application_id,
                "status": status,
                "progress": progress,
                "message": message,
            },
        )
