"""
정부24 Playwright 크롤러
- 주민등록초본 (주소변동 이력 포함) 자동 발급
  → www.gov.kr 은 plus.gov.kr 로 리다이렉트됨 (2024년 이후)
- 건축물대장은 OpenAPI(gov24_api.py → BuildingLedgerApiClient)로 대체
"""
import logging
from typing import Optional
from .base_crawler import BaseCrawler

logger = logging.getLogger(__name__)

# www.gov.kr → plus.gov.kr 로 리다이렉트 확인 (2026-04-26)
GOV24_URL = "https://plus.gov.kr"


class GOV24Crawler(BaseCrawler):
    """
    정부24 자동 크롤러.

    사용 예시:
        async with GOV24Crawler(cert_path, cert_password) as crawler:
            ok = await crawler.login()
            pdf = await crawler.get_resident_registration("홍길동", "900101-1234567")
    """

    async def login(self) -> bool:
        """공동인증서로 정부24 로그인"""
        try:
            await self._page.goto(f"{GOV24_URL}", wait_until="domcontentloaded")
            await self._page.click("text=공동인증서 로그인")
            await self._page.wait_for_selector(".cert-login-form", timeout=10_000)

            await self._page.fill("#certPwd", self.cert_password or "")
            await self._page.click("#certLoginBtn")

            await self._page.wait_for_selector(".user-info", timeout=15_000)
            logger.info("[GOV24Crawler] 로그인 성공")
            return True

        except Exception as e:
            logger.error(f"[GOV24Crawler] 로그인 실패: {e}")
            return False

    async def get_resident_registration(
        self,
        name: str,
        resident_number: str,
        include_history: bool = True,
    ) -> Optional[bytes]:
        """
        주민등록초본 발급 (주소변동 이력 포함)

        Args:
            name: 임차인 이름
            resident_number: 주민등록번호 (13자리)
            include_history: 주소변동 이력 포함 여부 (임차권등기명령 신청에는 필수)

        Returns:
            PDF 바이트
        """
        async def _do_fetch():
            # 민원24 > 주민등록 발급 페이지
            await self._page.goto(
                f"{GOV24_URL}/mw/AA020InfoCappView.do?HighCtgCD=A01001&CappBizCD=13100000015",
                wait_until="networkidle",
            )

            # 주민등록초본 선택
            await self._page.click("text=주민등록표초본(등본)교부")
            await self._page.wait_for_selector(".apply-form", timeout=10_000)

            # 주소변동 이력 옵션
            if include_history:
                await self._page.check("#addrHistoryChk")

            # 신청인 정보 (로그인 상태이면 자동 입력되는 경우가 많음)
            # 혹시 빈 필드가 있으면 채움
            name_input = await self._page.query_selector("#applicantName")
            if name_input:
                current_val = await name_input.input_value()
                if not current_val:
                    await name_input.fill(name)

            await self._page.click("#applyBtn")
            await self._page.wait_for_selector(".issue-complete", timeout=60_000)

            async with self._page.expect_download() as download_info:
                await self._page.click("#downloadPdfBtn")
            download = await download_info.value

            pdf_bytes = await download.read()
            logger.info(
                f"[GOV24Crawler] 주민등록초본 발급 완료: {name} ({len(pdf_bytes)} bytes)"
            )
            return pdf_bytes

        return await self._retry(_do_fetch)

    async def get_building_ledger(self, address: str) -> Optional[bytes]:
        """
        건축물대장 발급 (일반건축물대장 갑)

        Args:
            address: 건물 주소 (도로명 또는 지번)

        Returns:
            PDF 바이트
        """
        async def _do_fetch():
            await self._page.goto(
                f"{GOV24_URL}/mw/AA020InfoCappView.do?HighCtgCD=A01001&CappBizCD=11100000060",
                wait_until="networkidle",
            )

            await self._page.fill("#buildingAddr", address)
            await self._page.click("#searchBuildingBtn")
            await self._page.wait_for_selector(".building-search-result", timeout=15_000)

            # 첫 번째 결과 선택
            await self._page.click(".building-search-result tbody tr:first-child")
            await self._page.click("#applyBtn")
            await self._page.wait_for_selector(".issue-complete", timeout=60_000)

            async with self._page.expect_download() as download_info:
                await self._page.click("#downloadPdfBtn")
            download = await download_info.value

            pdf_bytes = await download.read()
            logger.info(
                f"[GOV24Crawler] 건축물대장 발급 완료: {address} ({len(pdf_bytes)} bytes)"
            )
            return pdf_bytes

        return await self._retry(_do_fetch)
