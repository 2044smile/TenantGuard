import uuid
import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, BigInteger, Boolean,
    DateTime, Enum, ForeignKey, Text, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base


class ApplicationStatus(str, enum.Enum):
    PENDING = "pending"             # 접수 대기
    COLLECTING = "collecting"       # 서류 수집 중
    ANALYZING = "analyzing"         # AI 분석 중
    READY = "ready"                 # 신청 준비 완료
    FILLING = "filling"             # 전자소송 자동 입력 중
    PREVIEW = "preview"             # 미리보기 대기
    SUBMITTED = "submitted"         # 제출 완료
    FAILED = "failed"               # 실패


class DocumentType(str, enum.Enum):
    BUILDING_REGISTRY = "building_registry"         # 건물등기부등본
    RESIDENT_REGISTRATION = "resident_registration" # 주민등록초본
    LEASE_CONTRACT = "lease_contract"               # 임대차계약서
    TERMINATION_NOTICE = "termination_notice"       # 계약해지통지서
    CORPORATE_REGISTRY = "corporate_registry"       # 법인등기부등본
    BUILDING_LEDGER = "building_ledger"             # 건축물대장
    FLOOR_PLAN = "floor_plan"                       # 별지 도면


class Application(Base):
    """임차권등기명령 신청 건"""
    __tablename__ = "applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(64), nullable=False, index=True)
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.PENDING)

    # ── 임차인 정보 ──────────────────────────────────────────────────────
    tenant_name = Column(String(50))
    tenant_resident_number_masked = Column(String(20))   # 앞 6자리만 저장
    tenant_address = Column(String(200))
    tenant_phone = Column(String(20))

    # ── 임대인 정보 ──────────────────────────────────────────────────────
    landlord_name = Column(String(100))
    landlord_address = Column(String(200))
    landlord_corp_number = Column(String(20), nullable=True)   # 법인번호 (법인인 경우)
    is_corporate_landlord = Column(Boolean, default=False)

    # ── 부동산 정보 ──────────────────────────────────────────────────────
    property_address = Column(String(200))
    property_area = Column(String(50))    # 면적 (㎡)
    property_floor = Column(String(20))   # 층
    property_type = Column(String(50))    # 아파트/주택/오피스텔 등

    # ── 계약 정보 ──────────────────────────────────────────────────────
    contract_date = Column(DateTime, nullable=True)
    deposit_amount = Column(BigInteger, nullable=True)      # 보증금
    confirmed_date = Column(DateTime, nullable=True)         # 확정일자
    move_in_date = Column(DateTime, nullable=True)           # 전입일

    # ── 처리 결과 ──────────────────────────────────────────────────────
    ecourt_receipt_number = Column(String(50), nullable=True)   # 전자소송 접수번호
    error_message = Column(Text, nullable=True)
    extra_data = Column(JSON, default=dict)

    # ── 타임스탬프 ─────────────────────────────────────────────────────
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)   # soft delete (개인정보 삭제 시점)

    documents = relationship("DocumentRecord", back_populates="application")


class DocumentRecord(Base):
    """수집/업로드된 서류 레코드 (메타데이터만, 실제 파일은 S3)"""
    __tablename__ = "document_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False)
    doc_type = Column(Enum(DocumentType), nullable=False)

    # S3 경로 (TTL 만료 후 삭제됨)
    storage_key = Column(String(500), nullable=True)

    is_auto_collected = Column(Boolean, default=True)   # True: 자동수집, False: 사용자 업로드
    collected_at = Column(DateTime, nullable=True)
    parsed_data = Column(JSON, default=dict)             # OCR/파싱 결과
    is_valid = Column(Boolean, nullable=True)
    validation_errors = Column(JSON, default=list)

    created_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="documents")
