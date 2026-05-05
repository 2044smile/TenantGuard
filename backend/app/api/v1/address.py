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
    bun: str = "0000"       # 번지 4자리
    ji: str = "0000"        # 지번 4자리
    plat_gb_cd: str = "0"   # 대지구분코드 (0: 대지, 1: 산, 2: 블록)


def _parse_juso_item(item: dict) -> AddressInfo:
    bd_mgtsn: str = item.get("bdMgtSn", "")
    # bdMgtSn 구조: [5자리 시군구][5자리 법정동][4자리 번][4자리 지][1자리 구분]
    bun = bd_mgtsn[10:14] if len(bd_mgtsn) >= 14 else "0000"
    ji  = bd_mgtsn[14:18] if len(bd_mgtsn) >= 18 else "0000"
    # 지번주소에 "산"이 포함되면 산(1), 블록이면 2, 나머지 대지(0)
    jibun = item.get("jibunAddr", "")
    plat_gb_cd = "1" if jibun.startswith("산") or " 산" in jibun else "0"
    return AddressInfo(
        road_address=item.get("roadAddr", ""),
        jibun_address=jibun,
        sigungu_code=bd_mgtsn[:5] if len(bd_mgtsn) >= 5 else "",
        bdong_code=bd_mgtsn[5:10] if len(bd_mgtsn) >= 10 else "",
        building_mgmt_no=bd_mgtsn,
        bun=bun,
        ji=ji,
        plat_gb_cd=plat_gb_cd,
    )


async def _fetch_juso(query: str, count: int = 10) -> list[dict]:
    if not settings.JUSO_API_KEY:
        raise ValueError("JUSO_API_KEY가 설정되지 않았습니다.")

    params = {
        "currentPage": 1,
        "countPerPage": count,
        "keyword": query,
        "confmKey": settings.JUSO_API_KEY,
        "resultType": "json",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(settings.JUSO_API_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    return data.get("results", {}).get("juso", [])


async def lookup_address(query: str) -> Optional[AddressInfo]:
    """도로명주소 API로 주소 검색 → 첫 번째 결과 반환 (내부 용도)"""
    items = await _fetch_juso(query, count=1)
    if not items:
        return None
    return _parse_juso_item(items[0])


@router.get("/lookup")
async def address_lookup(
    query: str = Query(..., description="검색할 주소 (도로명 또는 지번)"),
):
    """주소로 법정동코드 및 건물관리번호 조회 (단일 결과)."""
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
        "bun": info.bun,
        "ji": info.ji,
        "plat_gb_cd": info.plat_gb_cd,
    }


@router.get("/search")
async def address_search(
    query: str = Query(..., description="검색할 주소 (도로명 또는 지번)"),
    count: int = Query(10, ge=1, le=20, description="반환할 최대 결과 수"),
):
    """주소 검색 — 목록 반환 (프론트 주소 검색 팝업용)."""
    try:
        items = await _fetch_juso(query, count=count)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return [_parse_juso_item(item).__dict__ for item in items]
