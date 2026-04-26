import json
import uuid
from typing import Optional, Any
import redis.asyncio as aioredis
from app.config import settings


_redis: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


async def create_session(data: dict) -> str:
    """새 세션 생성, session_id 반환"""
    r = await get_redis()
    session_id = str(uuid.uuid4())
    await r.setex(f"session:{session_id}", settings.SESSION_TTL, json.dumps(data))
    return session_id


async def get_session(session_id: str) -> Optional[dict]:
    r = await get_redis()
    raw = await r.get(f"session:{session_id}")
    return json.loads(raw) if raw else None


async def delete_session(session_id: str) -> None:
    r = await get_redis()
    await r.delete(f"session:{session_id}")


async def store_cert(session_id: str, cert_data: bytes) -> None:
    """공동인증서를 짧은 TTL로 저장 (5분)"""
    r = await get_redis()
    await r.setex(f"cert:{session_id}", settings.CERT_TTL, cert_data)


async def get_cert(session_id: str) -> Optional[bytes]:
    r = await get_redis()
    return await r.get(f"cert:{session_id}")


async def delete_cert(session_id: str) -> None:
    r = await get_redis()
    await r.delete(f"cert:{session_id}")


async def set_progress(application_id: str, data: dict) -> None:
    """작업 진행률 저장 (WebSocket 브로드캐스트용)"""
    r = await get_redis()
    await r.setex(f"progress:{application_id}", 3600, json.dumps(data))


async def get_progress(application_id: str) -> Optional[dict]:
    r = await get_redis()
    raw = await r.get(f"progress:{application_id}")
    return json.loads(raw) if raw else None
