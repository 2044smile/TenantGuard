"""
인터넷등기소 (IROS) 크롤러
- 건물등기사항전부증명서 (등기부등본) 자동 발급
- 법인등기사항전부증명서 자동 발급
- 발급 수수료: 700원/건
"""
import logging
from typing import Optional
from .base_crawler import BaseCrawler

logger = logging.getLogger(__name__)

IROS_URL = "https://www.iros.go.kr"


class IROSCrawler(BaseCrawler):
    """
    인터넷등기소 자동 크롤러.

    사용 예시:
        async with IROSCrawler(cert_path, cert_password) as crawler:
            ok = await crawler.login()
            pdf = await crawler.get_building_registry("서울특별시 서초구 반포대로 201")
    """

    async def login(self) -> bool:
        """공동인증서로 인터넷등기소 로그인"""
        try:
            await self._page.goto(IROS_URL, wait_until="networkidle")

            # 공동인증서 로그인 버튼 클릭
            await self._page.click("text=공동인증서")
            await self._page.wait_for_selector("#certLoginBtn", timeout=10_000)

            # 인증서 파일 경로 및 비밀번호 입력
            # NOTE: 실제 환경에서는 공동인증서 라이브러리(NPKI)와 연동 필요
            await self._page.fill("#certPwd", self.cert_password or "")
            await self._page.click("#certLoginBtn")

            # 로그인 성공 여부 확인
            await self._page.wait_for_selector(".user-name", timeout=15_000)
            logger.info("[IROSCrawler] 로그인 성공")
            return True

        except Exception as e:
            logger.error(f"[IROSCrawler] 로그인 실패: {e}")
            return False

    async def search_building(self, address: str) -> Optional[dict]:
        """
        주소로 부동산 검색 → 고유번호 반환

        반환값:
            {
                "building_id": "1234567890",
                "address": "서울특별시 서초구 반포대로 201",
                "building_name": "래미안 퍼스티지"
            }
        """
        try:
            await self._page.goto(f"{IROS_URL}/efnSearch/RSC101R01.do", wait_until="networkidle")

            await self._page.fill("#searchAddr", address)
            await self._page.click("#searchBtn")
            await self._page.wait_for_selector(".result-table", timeout=15_000)

            # 첫 번째 결과 선택
            rows = await self._page.query_selector_all(".result-table tbody tr")
            if not rows:
                logger.warning(f"[IROSCrawler] 검색 결과 없음: {address}")
                return None

            first_row = rows[0]
            building_id = await first_row.get_attribute("data-building-id")
            building_name_el = await first_row.query_selector(".building-name")
            building_name = await building_name_el.inner_text() if building_name_el else ""

            return {
                "building_id": building_id,
                "address": address,
                "building_name": building_name.strip(),
            }

        except Exception as e:
            logger.error(f"[IROSCrawler] 부동산 검색 실패: {e}")
            return None

    async def get_building_registry(self, address: str) -> Optional[bytes]:
        """
        건물등기사항전부증명서 PDF 발급

        Args:
            address: 부동산 도로명 또는 지번 주소

        Returns:
            PDF 바이트, 실패 시 None
        """
        async def _do_fetch():
            building = await self.search_building(address)
            if not building:
                raise RuntimeError(f"주소 검색 실패: {address}")

            building_id = building["building_id"]

            # 등기사항증명서 발급 페이지 이동
            await self._page.goto(
                f"{IROS_URL}/efnSearch/RSC201R01.do?buildingId={building_id}",
                wait_until="networkidle",
            )

            # 발급 옵션: 말소사항 포함 전부증명서
            await self._page.check("#includeAllHistory")

            # 수수료 결제 (700원)
            await self._page.click("#payBtn")
            await self._page.wait_for_selector(".payment-complete", timeout=30_000)

            # PDF 다운로드
            async with self._page.expect_download() as download_info:
                await self._page.click("#downloadBtn")
            download = await download_info.value

            pdf_bytes = await download.read()
            logger.info(f"[IROSCrawler] 건물등기부등본 발급 완료: {address} ({len(pdf_bytes)} bytes)")
            return pdf_bytes

        return await self._retry(_do_fetch)

    async def get_corporate_registry(self, corp_number: str) -> Optional[bytes]:
        """
        법인등기사항전부증명서 PDF 발급 (임대인이 법인인 경우)

        Args:
            corp_number: 법인등록번호

        Returns:
            PDF 바이트, 실패 시 None
        """
        async def _do_fetch():
            await self._page.goto(
                f"{IROS_URL}/efnSearch/RSC301R01.do",
                wait_until="networkidle",
            )

            await self._page.fill("#corpNumber", corp_number.replace("-", ""))
            await self._page.click("#searchBtn")
            await self._page.wait_for_selector(".corp-result", timeout=15_000)
            await self._page.click(".corp-result tbody tr:first-child")

            # 수수료 결제 (700원)
            await self._page.click("#payBtn")
            await self._page.wait_for_selector(".payment-complete", timeout=30_000)

            async with self._page.expect_download() as download_info:
                await self._page.click("#downloadBtn")
            download = await download_info.value

            pdf_bytes = await download.read()
            logger.info(f"[IROSCrawler] 법인등기부등본 발급 완료: {corp_number} ({len(pdf_bytes)} bytes)")
            return pdf_bytes

        return await self._retry(_do_fetch)
