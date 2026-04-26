"""
도로명주소 API — 법정동코드 추출
행정안전부 도로명주소 개발자센터 API 연동
"""
import logging
from dataclasses import dataclass
from typing import Optional
import httpx
from fastapi import APIRouter, HTTPException, Query
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/address", tags=["Address"])


@dataclass
class AddressInfo:
    road_address: str       # 도로명주소
    jibun_address: str      # 지번주소
    sigungu_code: str       # 시군구코드 (5자리) — 건축물대장 API용
    bdong_code: str         # 법정동코드 (5자리)
    building_mgmt_no: str   # 건물관리번호 (19자리) — bdMgtSn


async def lookup_address(query: str) -> Optional[AddressInfo]:
    """
    도로명주소 API로 주소 검색 → AddressInfo 반환

    bdMgtSn (건물관리번호 19자리) 구조:
        [5자리 시군구코드][5자리 법정동코드][4자리 번][4자리 지][1자리 구분]
    """
    if not settings.JUSO_API_KEY:
        raise ValueError("JUSO_API_KEY가 설정되지 않았습니다.")

    params = {
        "currentPage": 1,
        "countPerPage": 10,
        "keyword": query,
        "confmKey": settings.JUSO_API_KEY,
        "resultType": "json",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(settings.JUSO_API_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    results = data.get("results", {})
    juso_list = results.get("juso", [])

    if not juso_list:
        return None

    # 여러 결과 중 첫 번째 선택 (정확도 순)
    item = juso_list[0]
    bd_mgtsn: str = item.get("bdMgtSn", "")

    sigungu_code = bd_mgtsn[:5] if len(bd_mgtsn) >= 5 else ""
    bdong_code = bd_mgtsn[5:10] if len(bd_mgtsn) >= 10 else ""

    return AddressInfo(
        road_address=item.get("roadAddr", ""),
        jibun_address=item.get("jibunAddr", ""),
        sigungu_code=sigungu_code,
        bdong_code=bdong_code,
        building_mgmt_no=bd_mgtsn,
    )


@router.get("/lookup")
async def address_lookup(
    query: str = Query(..., description="검색할 주소 (도로명 또는 지번)"),
):
    """
    주소로 법정동코드 및 건물관리번호 조회.
    건축물대장 API 호출에 필요한 코드를 반환한다.
    """
    try:
        info = await lookup_address(query)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not info:
        raise HTTPException(status_code=404, detail="주소를 찾을 수 없습니다.")

    return {
        "road_address": info.road_address,
        "jibun_address": info.jibun_address,
        "sigungu_code": info.sigungu_code,
        "bdong_code": info.bdong_code,
        "building_mgmt_no": info.building_mgmt_no,
    }
