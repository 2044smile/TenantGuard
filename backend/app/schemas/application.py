from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, field_validator
import re


# ── 하위 스키마 ──────────────────────────────────────────────────────────────

class TenantInfo(BaseModel):
    name: str
    resident_number: str          # 전송 시에만 사용, DB에 저장 안 함
    address: str
    address_detail: Optional[str] = None  # 동, 호수
    phone: Optional[str] = None

    @field_validator("resident_number")
    @classmethod
    def validate_resident_number(cls, v: str) -> str:
        cleaned = v.replace("-", "")
        if not re.match(r"^\d{13}$", cleaned):
            raise ValueError("주민등록번호 형식이 올바르지 않습니다.")
        return cleaned


class LandlordInfo(BaseModel):
    name: str
    address: str
    address_detail: Optional[str] = None  # 동, 호수
    phone: Optional[str] = None
    corp_number: Optional[str] = None     # 법인번호 (법인 임대인인 경우)
    is_corporate: bool = False


class PropertyInfo(BaseModel):
    address: str
    address_detail: Optional[str] = None  # 동, 호수


class ContractInfo(BaseModel):
    contract_date: datetime
    deposit_amount: int                 # 보증금 (원 단위)
    confirmed_date: Optional[datetime] = None
    move_in_date: Optional[datetime] = None


# ── 요청 스키마 ──────────────────────────────────────────────────────────────

class ApplicationCreate(BaseModel):
    tenant: TenantInfo
    landlord: LandlordInfo
    property: PropertyInfo
    contract: ContractInfo


class DocumentUpload(BaseModel):
    """사용자가 직접 업로드하는 서류 메타데이터"""
    doc_type: str  # "lease_contract" | "termination_notice" | "floor_plan"
    filename: str


# ── 응답 스키마 ──────────────────────────────────────────────────────────────

class ApplicationStatus(str):
    PENDING = "pending"
    COLLECTING = "collecting"
    ANALYZING = "analyzing"
    READY = "ready"
    FILLING = "filling"
    PREVIEW = "preview"
    SUBMITTED = "submitted"
    FAILED = "failed"


class DocumentInfo(BaseModel):
    doc_type: str
    is_auto_collected: bool
    collected_at: Optional[datetime]
    is_valid: Optional[bool]
    validation_errors: List[str] = []


class ApplicationResponse(BaseModel):
    id: str
    session_id: str
    status: str
    documents: List[DocumentInfo] = []
    ecourt_receipt_number: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProgressUpdate(BaseModel):
    """WebSocket 진행률 업데이트"""
    application_id: str
    status: str
    progress: int           # 0 ~ 100
    current_step: str
    completed_docs: List[str] = []
    failed_docs: List[str] = []
    message: str = ""


class PreviewResponse(BaseModel):
    application_id: str
    preview_html: str
    fee_breakdown: dict     # 비용 내역 (인지대, 송달료, 등록면허세, 등기촉탁수수료)
    total_fee: int


class SubmitResponse(BaseModel):
    application_id: str
    receipt_number: str
    submitted_at: datetime
    message: str = "임차권등기명령 신청이 완료되었습니다."


# ── 비용 계산 ─────────────────────────────────────────────────────────────────

class FeeCalculation(BaseModel):
    stamp_duty: int = 1800          # 인지대
    delivery_fee: int = 31200       # 송달료
    registration_tax: int = 7200    # 등록면허세
    registry_commission: int = 3000 # 등기촉탁수수료

    @property
    def total(self) -> int:
        return self.stamp_duty + self.delivery_fee + self.registration_tax + self.registry_commission
