"""
외부 API 연결 상태 확인 엔드포인트
GET /api/v1/connectivity

서비스 기동 전 또는 관리자가 API 키 유효성을 확인할 때 사용한다.
민감한 엔드포인트이므로 실제 배포 시 인증 미들웨어 추가 필요.
"""
import asyncio
import logging
import httpx
from fastapi import APIRouter
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/connectivity", tags=["System"])


async def _check_juso() -> dict:
    """도로명주소 API (행정안전부)"""
    if not settings.JUSO_API_KEY:
        return {"ok": False, "reason": "JUSO_API_KEY 미설정"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                settings.JUSO_API_URL,
                params={
                    "confmKey": settings.JUSO_API_KEY,
                    "currentPage": "1",
                    "countPerPage": "1",
                    "keyword": "서울",
                    "resultType": "json",
                },
            )
            data = resp.json()
            code = data.get("results", {}).get("common", {}).get("errorCode", "-1")
            return {"ok": code == "0", "error_code": code}
    except Exception as e:
        return {"ok": False, "reason": str(e)}


async def _check_building_api() -> dict:
    """건축물대장 API (data.go.kr)"""
    if not settings.BUILDING_API_KEY:
        return {"ok": False, "reason": "BUILDING_API_KEY 미설정"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{settings.BUILDING_API_URL}/getBrBasisOulnInfo",
                params={
                    "serviceKey": settings.BUILDING_API_KEY,
                    "sigunguCd": "11650",
                    "bjdongCd": "10100",
                    "bun": "0000",
                    "ji": "0000",
                    "numOfRows": "1",
                    "pageNo": "1",
                    "_type": "json",
                },
            )
            return {"ok": resp.status_code == 200, "http_status": resp.status_code}
    except Exception as e:
        return {"ok": False, "reason": str(e)}


async def _check_gov24_api() -> dict:
    """정부24 OpenAPI (odcloud.kr)"""
    if not settings.GOV24_API_KEY:
        return {"ok": False, "reason": "GOV24_API_KEY 미설정"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{settings.GOV24_API_URL}/15013005/v1/uddi:3573aaa7-a81e-4b17-9e47-0d5a9e3aee42",
                params={"page": "1", "perPage": "1", "serviceKey": settings.GOV24_API_KEY},
            )
            return {"ok": resp.status_code == 200, "http_status": resp.status_code}
    except Exception as e:
        return {"ok": False, "reason": str(e)}


async def _check_iros_site() -> dict:
    """인터넷등기소 사이트 접근 가능 여부 (HTTP)"""
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get("https://www.iros.go.kr")
            return {"ok": resp.status_code == 200, "http_status": resp.status_code}
    except Exception as e:
        return {"ok": False, "reason": str(e)}


async def _check_gov24_site() -> dict:
    """정부24 사이트 접근 가능 여부 (HTTP)"""
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get("https://plus.gov.kr")
            return {"ok": resp.status_code == 200, "http_status": resp.status_code}
    except Exception as e:
        return {"ok": False, "reason": str(e)}


async def _check_ecourt_site() -> dict:
    """전자소송 사이트 접근 가능 여부 (HTTP)"""
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get("https://ecfs.scourt.go.kr")
            return {"ok": resp.status_code == 200, "http_status": resp.status_code}
    except Exception as e:
        return {"ok": False, "reason": str(e)}


@router.get("")
async def check_connectivity():
    """
    외부 API 및 사이트 연결 상태를 한꺼번에 확인한다.

    Returns:
        각 서비스별 ok/reason 딕셔너리
    """
    (
        juso,
        building,
        gov24_api,
        iros_site,
        gov24_site,
        ecourt_site,
    ) = await asyncio.gather(
        _check_juso(),
        _check_building_api(),
        _check_gov24_api(),
        _check_iros_site(),
        _check_gov24_site(),
        _check_ecourt_site(),
    )

    results = {
        "apis": {
            "juso": juso,
            "building_ledger": building,
            "gov24_openapi": gov24_api,
        },
        "sites": {
            "iros": iros_site,
            "gov24": gov24_site,
            "ecourt": ecourt_site,
        },
    }

    all_sites_ok = all(v["ok"] for v in results["sites"].values())
    results["summary"] = {
        "all_sites_reachable": all_sites_ok,
        "api_keys_configured": juso["ok"] or building["ok"],
    }

    logger.info(f"[connectivity] 결과: {results['summary']}")
    return results
