"""
서류 수집 오케스트레이터

수집 방식 요약:
  등기부등본(건물/법인): Playwright → iros.go.kr            (공동인증서 로그인)
  주민등록초본:         Playwright  → plus.gov.kr           (OpenAPI 미제공)
  건축물대장:           OpenAPI     → data.go.kr             (무료)
"""
import asyncio
import logging
import tempfile
import os
import json
from typing import Optional
from app.core.redis_client import set_progress, get_cert
from app.core.storage import upload_document
from app.services.crawlers.iros_crawler import IROSCrawler
from app.services.crawlers.gov24_crawler import GOV24Crawler
from app.services.gov24_api import BuildingLedgerApiClient

logger = logging.getLogger(__name__)


class DocumentOrchestrator:
    def __init__(self, application_id: str, session_id: str):
        self.application_id = application_id
        self.session_id = session_id

    async def run(self, application_data: dict) -> dict:
        """
        서류 수집 전체 파이프라인 실행 (병렬)

        Returns:
            {
                "building_registry": "s3-key",
                "resident_registration": "s3-key",
                "corporate_registry": "s3-key" (optional),
                "errors": [...]
            }
        """
        await self._update_progress(10, "서류 수집 시작", "collecting")

        cert_bytes = await get_cert(self.session_id)
        cert_password = application_data.get("cert_password", "")

        # Playwright용: 인증서를 임시 파일로 저장
        cert_path = None
        if cert_bytes:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pfx")
            tmp.write(cert_bytes)
            tmp.close()
            cert_path = tmp.name

        results = {}
        errors = []

        # ── 병렬 수집 태스크 구성 ────────────────────────────────────────────
        # [Playwright] iros.go.kr   — 등기부등본
        # [Playwright] plus.gov.kr  — 주민등록초본 (OpenAPI 미제공)
        # [OpenAPI]    data.go.kr   — 건축물대장 (무료)
        prop = application_data["property"]
        tasks = [
            self._collect_building_registry_iros(
                address=prop["address"],
                cert_path=cert_path,
                cert_password=cert_password,
            ),
            self._collect_resident_registration(
                application_data["tenant"]["name"],
                application_data["tenant"]["resident_number"],
                cert_path,
                cert_password,
            ),
            self._collect_building_ledger_api(
                sigungu_code=prop.get("sigungu_code", ""),
                bdong_code=prop.get("bdong_code", ""),
                bun=prop.get("bun", "0000"),
                ji=prop.get("ji", "0000"),
                plat_gb_cd=prop.get("plat_gb_cd", "0"),
            ),
        ]

        # 법인 임대인인 경우 법인등기부등본도 수집
        if application_data["landlord"].get("is_corporate"):
            tasks.append(
                self._collect_corporate_registry_iros(
                    corp_number=application_data["landlord"]["corp_number"],
                    cert_path=cert_path,
                    cert_password=cert_password,
                )
            )

        task_results = await asyncio.gather(*tasks, return_exceptions=True)
        building_result, resident_result, ledger_result, *corp_result = task_results

        if isinstance(building_result, Exception):
            errors.append(f"건물등기부등본 수집 실패: {building_result}")
            logger.error(f"건물등기부등본 수집 실패: {building_result}")
        else:
            results["building_registry"] = building_result

        if isinstance(resident_result, Exception):
            errors.append(f"주민등록초본 수집 실패: {resident_result}")
        else:
            results["resident_registration"] = resident_result

        if isinstance(ledger_result, Exception):
            logger.warning(f"건축물대장 API 수집 실패 (무시): {ledger_result}")
        else:
            results["building_ledger"] = ledger_result

        if corp_result:
            cr = corp_result[0]
            if isinstance(cr, Exception):
                errors.append(f"법인등기부등본 수집 실패: {cr}")
            else:
                results["corporate_registry"] = cr

        # 임시 인증서 파일 삭제
        if cert_path and os.path.exists(cert_path):
            os.unlink(cert_path)

        results["errors"] = errors
        progress = 90 if not errors else 60
        status = "analyzing" if not errors else "failed"
        await self._update_progress(progress, "서류 수집 완료", status)
        return results

    async def _collect_building_registry_iros(
        self, address: str, cert_path: Optional[str], cert_password: str
    ) -> str:
        """인터넷등기소 Playwright로 건물 등기사항전부증명서 발급 → PDF 저장"""
        async with IROSCrawler(cert_path, cert_password) as crawler:
            if not await crawler.login():
                raise RuntimeError("인터넷등기소 로그인 실패")
            pdf = await crawler.get_building_registry(address)
            if not pdf:
                raise RuntimeError("건물등기부등본 발급 실패")
            key = f"applications/{self.application_id}/building_registry.pdf"
            upload_document(key, pdf)
            await self._update_progress(40, "건물등기부등본 수집 완료", "collecting")
            return key

    async def _collect_resident_registration(
        self, name: str, resident_number: str, cert_path: Optional[str], cert_password: str
    ) -> str:
        async with GOV24Crawler(cert_path, cert_password) as crawler:
            if not await crawler.login():
                raise RuntimeError("정부24 로그인 실패")
            pdf = await crawler.get_resident_registration(name, resident_number, include_history=True)
            if not pdf:
                raise RuntimeError("주민등록초본 발급 실패")
            key = f"applications/{self.application_id}/resident_registration.pdf"
            upload_document(key, pdf)
            await self._update_progress(70, "주민등록초본 수집 완료", "collecting")
            return key

    async def _collect_building_ledger_api(
        self, sigungu_code: str, bdong_code: str,
        bun: str = "0000", ji: str = "0000", plat_gb_cd: str = "0",
    ) -> str:
        """건축물대장 표제부 OpenAPI 조회 → JSON 저장"""
        if not sigungu_code or not bdong_code:
            raise RuntimeError("시군구코드/법정동코드 없음 — 도로명주소 API 조회 필요")
        client = BuildingLedgerApiClient()
        info = await client.get_building_info(sigungu_code, bdong_code, bun, ji, plat_gb_cd)
        if not info:
            raise RuntimeError("건축물대장 조회 결과 없음")
        key = f"applications/{self.application_id}/building_ledger.json"
        upload_document(key, json.dumps(info, ensure_ascii=False).encode(), content_type="application/json")
        logger.info(f"[orchestrator] 건축물대장 API 수집 완료: {key}")
        return key

    async def _collect_corporate_registry_iros(
        self, corp_number: str, cert_path: Optional[str], cert_password: str
    ) -> str:
        """인터넷등기소 Playwright로 법인 등기사항전부증명서 발급 → PDF 저장"""
        async with IROSCrawler(cert_path, cert_password) as crawler:
            if not await crawler.login():
                raise RuntimeError("인터넷등기소 로그인 실패")
            pdf = await crawler.get_corporate_registry(corp_number)
            if not pdf:
                raise RuntimeError("법인등기부등본 발급 실패")
            key = f"applications/{self.application_id}/corporate_registry.pdf"
            upload_document(key, pdf)
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
