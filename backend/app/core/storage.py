"""MinIO / S3 파일 스토리지 래퍼 — 수집된 서류는 1시간 TTL"""
import io
from typing import Optional
from minio import Minio
from minio.error import S3Error
from app.config import settings


def _get_client() -> Minio:
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_USE_SSL,
    )


def ensure_bucket() -> None:
    client = _get_client()
    if not client.bucket_exists(settings.MINIO_BUCKET):
        client.make_bucket(settings.MINIO_BUCKET)


def upload_document(key: str, data: bytes, content_type: str = "application/pdf") -> str:
    """서류를 스토리지에 업로드, 스토리지 키 반환"""
    client = _get_client()
    ensure_bucket()
    client.put_object(
        settings.MINIO_BUCKET,
        key,
        io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )
    return key


def download_document(key: str) -> Optional[bytes]:
    """스토리지에서 서류 다운로드"""
    client = _get_client()
    try:
        response = client.get_object(settings.MINIO_BUCKET, key)
        return response.read()
    except S3Error:
        return None


def delete_document(key: str) -> None:
    client = _get_client()
    try:
        client.remove_object(settings.MINIO_BUCKET, key)
    except S3Error:
        pass


def delete_application_documents(application_id: str) -> None:
    """신청 건의 모든 서류 삭제 (개인정보 삭제)"""
    client = _get_client()
    prefix = f"applications/{application_id}/"
    objects = client.list_objects(settings.MINIO_BUCKET, prefix=prefix, recursive=True)
    for obj in objects:
        client.remove_object(settings.MINIO_BUCKET, obj.object_name)
