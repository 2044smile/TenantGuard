"""
대법원 전자소송 (ecfs.scourt.go.kr) 자동 입력기
- 임차권등기명령 신청서 자동 작성
- 수집된 서류 자동 첨부
- 사용자 최종 확인 후 제출
"""
import logging
from typing import Optional, List
from .base_crawler import BaseCrawler

logger = logging.getLogger(__name__)

ECOURT_URL = "https://ecfs.scourt.go.kr"


class EcourtFiller(BaseCrawler):
    """
    대법원 전자소송 자동 입력기.

    사용 예시:
        async with EcourtFiller(cert_path, cert_password) as filler:
            ok = await filler.login()
            ok = await filler.fill_application(application_data)
            ok = await filler.attach_documents(document_paths)
            html = await filler.preview()
    """

    async def login(self) -> bool:
        """공동인증서로 전자소송 로그인"""
        try:
            await self._page.goto(f"{ECOURT_URL}/CSFS10/index.do", wait_until="networkidle")
            await self._page.click("#certLoginBtn")
            await self._page.wait_for_selector(".cert-modal", timeout=10_000)

            await self._page.fill("#certPwd", self.cert_password or "")
            await self._page.click("#certConfirmBtn")

            await self._page.wait_for_selector(".main-menu", timeout=20_000)
            logger.info("[EcourtFiller] 로그인 성공")
            return True

        except Exception as e:
            logger.error(f"[EcourtFiller] 로그인 실패: {e}")
            return False

    async def fill_application(self, data: dict) -> bool:
        """
        임차권등기명령 신청서 자동 입력

        Args:
            data: {
                "tenant": { "name", "resident_number", "address" },
                "landlord": { "name", "address", "corp_number" },
                "property": { "address", "area", "floor", "type" },
                "contract": { "contract_date", "deposit_amount", "confirmed_date", "move_in_date" },
                "application_type": "전부" | "일부" | "한층전부"
            }
        """
        try:
            # 임차권등기명령 신청 메뉴 이동
            await self._page.goto(
                f"{ECOURT_URL}/CSFS10/pages/CSFS10/CSFS1001R01.do?gubun=02",
                wait_until="networkidle",
            )

            # 신청서 유형 선택 (아파트전부/주택일부/한층전부)
            app_type = data.get("application_type", "전부")
            await self._page.select_option("#appTypeSelect", label=app_type)

            # ── 임차인 정보 입력 ────────────────────────────────────────────
            tenant = data["tenant"]
            await self._page.fill("#tenantName", tenant["name"])
            await self._page.fill("#tenantResidentNo", tenant["resident_number"])
            await self._page.fill("#tenantAddr", tenant["address"])

            # ── 임대인 정보 입력 ────────────────────────────────────────────
            landlord = data["landlord"]
            await self._page.fill("#landlordName", landlord["name"])
            await self._page.fill("#landlordAddr", landlord["address"])
            if landlord.get("corp_number"):
                await self._page.check("#isCorporate")
                await self._page.fill("#landlordCorpNo", landlord["corp_number"])

            # ── 부동산 정보 입력 ────────────────────────────────────────────
            prop = data["property"]
            await self._page.fill("#propertyAddr", prop["address"])
            await self._page.fill("#propertyArea", str(prop.get("area", "")))
            await self._page.fill("#propertyFloor", str(prop.get("floor", "")))

            # ── 계약 정보 입력 ────────────────────────────────────────────
            contract = data["contract"]
            await self._page.fill(
                "#contractDate",
                contract["contract_date"].strftime("%Y%m%d") if hasattr(contract["contract_date"], "strftime") else str(contract["contract_date"]),
            )
            await self._page.fill("#depositAmount", str(contract["deposit_amount"]))
            if contract.get("confirmed_date"):
                confirmed = contract["confirmed_date"]
                await self._page.fill(
                    "#confirmedDate",
                    confirmed.strftime("%Y%m%d") if hasattr(confirmed, "strftime") else str(confirmed),
                )
            if contract.get("move_in_date"):
                move_in = contract["move_in_date"]
                await self._page.fill(
                    "#moveInDate",
                    move_in.strftime("%Y%m%d") if hasattr(move_in, "strftime") else str(move_in),
                )

            # 신청 취지 자동 생성 (표준 문안)
            await self._page.click("#autoFillPurposeBtn")
            await self._page.wait_for_selector("#purposeText:not(:empty)", timeout=5_000)

            logger.info("[EcourtFiller] 신청서 자동 입력 완료")
            return True

        except Exception as e:
            logger.error(f"[EcourtFiller] 신청서 입력 실패: {e}")
            return False

    async def attach_documents(self, document_paths: List[str]) -> bool:
        """
        첨부 서류 업로드

        Args:
            document_paths: 서버 임시 파일 경로 목록
        """
        try:
            await self._page.click("#attachDocTab")
            await self._page.wait_for_selector(".attach-section", timeout=10_000)

            for file_path in document_paths:
                file_input = await self._page.query_selector("input[type='file']:not([disabled])")
                if file_input:
                    await file_input.set_input_files(file_path)
                    await self._page.wait_for_selector(".upload-complete", timeout=30_000)
                    logger.info(f"[EcourtFiller] 서류 첨부 완료: {file_path}")

            return True

        except Exception as e:
            logger.error(f"[EcourtFiller] 서류 첨부 실패: {e}")
            return False

    async def preview(self) -> Optional[str]:
        """
        작성된 신청서 미리보기 HTML 반환 (사용자 최종 확인용)
        """
        try:
            await self._page.click("#previewBtn")
            await self._page.wait_for_selector(".preview-frame", timeout=15_000)
            html = await self._page.inner_html(".preview-frame")
            return html
        except Exception as e:
            logger.error(f"[EcourtFiller] 미리보기 실패: {e}")
            return None

    async def submit(self) -> Optional[dict]:
        """
        최종 제출 — 사용자가 명시적으로 승인한 뒤에만 호출

        Returns:
            { "receipt_number": "20240101-123456", "submitted_at": datetime }
        """
        try:
            await self._page.click("#finalSubmitBtn")

            # 제출 확인 팝업
            await self._page.wait_for_selector(".confirm-modal", timeout=10_000)
            await self._page.click(".confirm-modal #confirmBtn")

            await self._page.wait_for_selector(".receipt-number", timeout=30_000)
            receipt_el = await self._page.query_selector(".receipt-number")
            receipt_number = (await receipt_el.inner_text()).strip() if receipt_el else ""

            logger.info(f"[EcourtFiller] 제출 완료 — 접수번호: {receipt_number}")
            return {
                "receipt_number": receipt_number,
                "submitted_at": __import__("datetime").datetime.now(),
            }

        except Exception as e:
            logger.error(f"[EcourtFiller] 제출 실패: {e}")
            return None
