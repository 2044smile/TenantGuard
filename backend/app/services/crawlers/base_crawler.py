"""모든 크롤러의 공통 베이스 클래스 (Playwright 기반)"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

logger = logging.getLogger(__name__)


class BaseCrawler(ABC):
    """
    서버사이드 헤드리스 브라우저 크롤러 베이스.
    모바일/데스크톱 클라이언트는 FastAPI 엔드포인트를 통해 간접 호출한다.
    """

    MAX_RETRY = 3
    RETRY_DELAY = 5  # seconds

    def __init__(self, cert_path: Optional[str] = None, cert_password: Optional[str] = None):
        self.cert_path = cert_path
        self.cert_password = cert_password
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    async def __aenter__(self):
        await self._init_browser()
        return self

    async def __aexit__(self, *args):
        await self.cleanup()

    async def _init_browser(self) -> None:
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        self._context = await self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="ko-KR",
            timezone_id="Asia/Seoul",
        )
        self._page = await self._context.new_page()

    async def cleanup(self) -> None:
        try:
            if self._page:
                await self._page.close()
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
        except Exception as e:
            logger.warning(f"[{self.__class__.__name__}] cleanup 오류: {e}")

    async def _retry(self, coro_fn, *args, **kwargs):
        """지수 백오프로 최대 MAX_RETRY 회 재시도"""
        last_exc = None
        for attempt in range(self.MAX_RETRY):
            try:
                return await coro_fn(*args, **kwargs)
            except Exception as e:
                last_exc = e
                wait = self.RETRY_DELAY * (2 ** attempt)
                logger.warning(
                    f"[{self.__class__.__name__}] 시도 {attempt + 1}/{self.MAX_RETRY} 실패: {e} "
                    f"— {wait}초 후 재시도"
                )
                await asyncio.sleep(wait)
        raise RuntimeError(f"최대 재시도 횟수 초과: {last_exc}") from last_exc

    @abstractmethod
    async def login(self) -> bool:
        """공동인증서로 로그인"""
        ...
