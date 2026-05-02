"""
정부24 OpenAPI 클라이언트
공공데이터포털(data.go.kr) → Base URL: https://api.odcloud.kr/api

제공 데이터:
  - 대한민국 공공서비스(혜택) 정보 조회 (서비스 목록/상세)
  - 건축물대장은 별도 data.go.kr API 사용 (building_api.py)

※ 주민등록초본 발급은 OpenAPI로 제공되지 않음 → Playwright(plus.gov.kr) 유지
"""
import logging
from typing import Optional
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


class Gov24ApiClient:
    """
    정부24 OpenAPI 래퍼.
    data.go.kr 에서 서비스키(GOV24_API_KEY) 발급 필요.
    """

    BASE_URL = "https://api.odcloud.kr/api"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GOV24_API_KEY
        if not self.api_key:
            raise ValueError("GOV24_API_KEY가 설정되지 않았습니다. data.go.kr에서 발급하세요.")

    # ── 공공서비스 목록 조회 ──────────────────────────────────────────────────

    async def get_service_list(
        self,
        page: int = 1,
        per_page: int = 10,
        keyword: Optional[str] = None,
    ) -> dict:
        """
        공공서비스(혜택) 정보 목록 조회

        Args:
            page: 페이지 번호 (1부터)
            per_page: 페이지당 결과 수
            keyword: 검색 키워드 (예: "임차권", "전세사기")

        Returns:
            {
                "currentCount": 10,
                "data": [...],
                "matchCount": 150,
                "page": 1,
                "perPage": 10,
                "totalCount": 150
            }
        """
        params = {
            "page": page,
            "perPage": per_page,
            "serviceKey": self.api_key,
        }
        if keyword:
            params["cond[svcNm::LIKE]"] = keyword

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{self.BASE_URL}/15013005/v1/uddi:3573aaa7-a81e-4b17-9e47-0d5a9e3aee42",
                params=params,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_service_detail(self, service_id: str) -> dict:
        """
        공공서비스 상세 정보 조회

        Args:
            service_id: 서비스 ID (목록 조회 결과의 svcId)
        """
        params = {
            "page": 1,
            "perPage": 1,
            "serviceKey": self.api_key,
            "cond[svcId::EQ]": service_id,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{self.BASE_URL}/15013005/v1/uddi:3573aaa7-a81e-4b17-9e47-0d5a9e3aee42",
                params=params,
            )
            resp.raise_for_status()
            return resp.json()

    async def search_tenant_services(self) -> list[dict]:
        """
        임차인 관련 공공서비스 검색 (임차권등기명령 관련 안내 서비스 조회)
        """
        result = await self.get_service_list(keyword="임차권")
        return result.get("data", [])

    # ── 연결 테스트 ───────────────────────────────────────────────────────────

    async def ping(self) -> bool:
        """API 키 유효성 및 연결 확인"""
        try:
            result = await self.get_service_list(per_page=1)
            return "data" in result
        except Exception as e:
            logger.error(f"[Gov24ApiClient] ping 실패: {e}")
            return False


# ── 건축물대장 API (data.go.kr 별도 엔드포인트) ────────────────────────────────

class BuildingLedgerApiClient:
    """
    건축물대장 OpenAPI (공공데이터포털)
    API 키: data.go.kr → "건축물대장정보 서비스" 활용신청
    """

    BASE_URL = "https://apis.data.go.kr/1613000/BldRgstHubService"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.BUILDING_API_KEY
        if not self.api_key:
            raise ValueError("BUILDING_API_KEY가 설정되지 않았습니다.")

    async def get_building_info(
        self,
        sigungu_code: str,
        bdong_code: str,
        bun: str = "0000",
        ji: str = "0000",
    ) -> dict:
        """
        건축물대장 기본개요 조회

        Args:
            sigungu_code: 시군구코드 5자리 (도로명주소 API → bdMgtSn 앞 5자리)
            bdong_code:   법정동코드 5자리 (bdMgtSn 6~10번째 자리)
            bun:          번지 4자리
            ji:           지번 4자리

        Returns:
            건축물대장 기본개요 JSON
        """
        params = {
            "sigunguCd": sigungu_code,
            "bjdongCd": bdong_code,
            "bun": bun.zfill(4),
            "ji": ji.zfill(4),
            "numOfRows": 10,
            "pageNo": 1,
            "_type": "json",
        }
        # serviceKey는 이미 인코딩된 값이므로 URL에 직접 삽입 (이중 인코딩 방지)
        base = f"{self.BASE_URL}/getBrBasisOulnInfo?serviceKey={self.api_key}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(base, params=params)
            resp.raise_for_status()
            data = resp.json()

        items = (
            data.get("response", {})
                .get("body", {})
                .get("items", {})
                .get("item", [])
        )
        return items[0] if isinstance(items, list) and items else {}

    async def get_building_floor_info(
        self,
        sigungu_code: str,
        bdong_code: str,
        bun: str = "0000",
        ji: str = "0000",
    ) -> list[dict]:
        """
        건축물대장 층별개요 조회 (임차 면적 확인용)
        """
        params = {
            "serviceKey": self.api_key,
            "sigunguCd": sigungu_code,
            "bjdongCd": bdong_code,
            "bun": bun.zfill(4),
            "ji": ji.zfill(4),
            "numOfRows": 50,
            "pageNo": 1,
            "_type": "json",
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{self.BASE_URL}/getBrFlrOulnInfo",
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()

        items = (
            data.get("response", {})
                .get("body", {})
                .get("items", {})
                .get("item", [])
        )
        return items if isinstance(items, list) else ([items] if items else [])

    async def ping(self) -> bool:
        """연결 확인"""
        try:
            params = {
                "serviceKey": self.api_key,
                "sigunguCd": "11650",
                "bjdongCd": "10100",
                "bun": "0000",
                "ji": "0000",
                "numOfRows": 1,
                "pageNo": 1,
                "_type": "json",
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.BASE_URL}/getBrBasisOulnInfo", params=params)
                return resp.status_code == 200
        except Exception as e:
            logger.error(f"[BuildingLedgerApiClient] ping 실패: {e}")
            return False
