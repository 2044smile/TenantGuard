"""
사이트 연결 및 API 접근성 확인 스크립트
실행: python scripts/check_connectivity.py

테스트 항목:
  [Playwright]  plus.gov.kr       — 주민등록초본 발급 (로그인 페이지 확인)
  [Playwright]  www.iros.go.kr    — 등기부등본 발급 (로그인 페이지 확인)
  [Playwright]  ecfs.scourt.go.kr — 전자소송 (로그인 페이지 확인)
  [OpenAPI]     api.odcloud.kr    — 정부24 공공서비스 정보 API (키 없이 헬스체크)
  [OpenAPI]     apis.data.go.kr   — 건축물대장 API (키 없이 헬스체크)
  [OpenAPI]     business.juso.go.kr — 도로명주소 API (키 없이 헬스체크)
"""
import asyncio
import sys
import os
import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# ── Playwright 테스트 대상 ────────────────────────────────────────────────────
PLAYWRIGHT_TARGETS = [
    {
        "name": "정부24 (plus.gov.kr)",
        "url": "https://plus.gov.kr",
        "note": "주민등록초본 발급 — Playwright",
        "login_indicator": "공동인증서",
    },
    {
        "name": "인터넷등기소",
        "url": "https://www.iros.go.kr/index.jsp",
        "note": "등기부등본 발급 — Playwright",
        "login_indicator": "인터넷등기소",
    },
    {
        "name": "대법원 전자소송",
        "url": "https://ecfs.scourt.go.kr/CSFS10/index.do",
        "note": "임차권등기명령 신청 — Playwright",
        "login_indicator": "전자소송",
    },
]

# ── OpenAPI 테스트 대상 (API 키 없이 HTTP 상태만 확인) ──────────────────────
API_TARGETS = [
    {
        "name": "정부24 OpenAPI (odcloud.kr)",
        "url": "https://api.odcloud.kr/api/15013005/v1/uddi:3573aaa7-a81e-4b17-9e47-0d5a9e3aee42",
        "note": "공공서비스 정보 — API 키 필요 (data.go.kr 발급)",
        "expected_status": [200, 401, 403],
    },
    {
        "name": "건축물대장 API (data.go.kr)",
        "url": "http://apis.data.go.kr/1613000/BldRgstHubService/getBrBasisOulnInfo",
        "note": "건축물대장 기본개요 — API 키 필요 (data.go.kr 발급)",
        "expected_status": [200, 400, 401],
    },
    {
        "name": "도로명주소 API (juso.go.kr)",
        "url": "https://business.juso.go.kr/addrlink/addrLinkApi.do",
        "note": "법정동코드 추출 — API 키 필요 (juso.go.kr 발급)",
        "expected_status": [200, 400, 401],
    },
]


async def check_playwright_site(target: dict) -> dict:
    from playwright.async_api import async_playwright

    result = {
        "name": target["name"],
        "note": target["note"],
        "reachable": False,
        "indicator_found": False,
        "error": None,
    }
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            resp = await page.goto(target["url"], wait_until="domcontentloaded", timeout=20_000)
            result["reachable"] = (resp.status if resp else 0) == 200
            content = await page.content()
            result["indicator_found"] = target["login_indicator"] in content
            await browser.close()
    except Exception as e:
        result["error"] = str(e)
    return result


async def check_api_target(target: dict) -> dict:
    result = {
        "name": target["name"],
        "note": target["note"],
        "reachable": False,
        "status_code": None,
        "error": None,
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(target["url"])
            result["status_code"] = resp.status_code
            result["reachable"] = resp.status_code in target["expected_status"]
    except Exception as e:
        result["error"] = str(e)
    return result


async def main():
    print("\n" + "=" * 65)
    print("  TenantGuard — 연결 테스트")
    print("=" * 65)

    print("\n[ Playwright 크롤링 대상 ]")
    pw_results = await asyncio.gather(*[check_playwright_site(t) for t in PLAYWRIGHT_TARGETS])
    for r in pw_results:
        ok = r["reachable"]
        icon = "✅" if ok else "❌"
        print(f"\n{icon}  {r['name']}")
        print(f"     사이트 접속: {'가능' if r['reachable'] else '불가'}")
        print(f"     키워드 감지: {'감지됨' if r['indicator_found'] else '미감지 (셀렉터 추가 확인 필요)'}")
        print(f"     용도: {r['note']}")
        if r["error"]:
            print(f"     오류: {r['error']}")

    print("\n[ OpenAPI 대상 (키 없이 서버 응답 확인) ]")
    api_results = await asyncio.gather(*[check_api_target(t) for t in API_TARGETS])
    for r in api_results:
        ok = r["reachable"]
        icon = "✅" if ok else "❌"
        print(f"\n{icon}  {r['name']}")
        print(f"     서버 응답: HTTP {r['status_code']}")
        print(f"     용도: {r['note']}")
        if r["error"]:
            print(f"     오류: {r['error']}")

    print("\n" + "=" * 65)
    all_pw_ok = all(r["reachable"] for r in pw_results)
    all_api_ok = all(r["reachable"] for r in api_results)
    if all_pw_ok and all_api_ok:
        print("  결과: 모든 대상 접근 가능 ✅")
    else:
        if not all_pw_ok:
            print("  ⚠️  일부 크롤링 대상 접근 불가")
        if not all_api_ok:
            print("  ⚠️  일부 OpenAPI 서버 응답 없음")
    print("=" * 65 + "\n")

    return 0 if (all_pw_ok and all_api_ok) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
