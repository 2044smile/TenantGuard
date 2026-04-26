"""
AI 문서 분석기
사용자가 직접 발급·업로드한 서류를 OCR로 파싱하고 교차 검증한다.

지원 서류:
  - 등기사항전부증명서 (등기부등본)
  - 주민등록초본 (주소변동 이력 포함)
  - 임대차계약서 (확정일자 포함)
  - 계약해지통지서

OCR 엔진:
  - pdfplumber (텍스트 레이어 있는 PDF — 인터넷등기소/정부24 발급본 해당)
  - PaddleOCR (이미지 스캔본 / 스마트폰 사진 — 설치 시 자동 활성화)
  - pytesseract (fallback)
"""
import re
import logging
from datetime import datetime
from typing import Optional
import io

logger = logging.getLogger(__name__)


class DocumentAnalyzer:

    def __init__(self, ocr_engine: str = "paddle"):
        self.ocr_engine = ocr_engine
        self._ocr = None

    # ── OCR 공통 ──────────────────────────────────────────────────────────────

    def _load_ocr(self):
        if self._ocr is not None:
            return
        if self.ocr_engine == "paddle":
            try:
                from paddleocr import PaddleOCR
                self._ocr = PaddleOCR(use_angle_cls=True, lang="korean", show_log=False)
            except ImportError:
                logger.warning("PaddleOCR 미설치 — pytesseract로 fallback")
                self.ocr_engine = "tesseract"

    def extract_text(self, file_bytes: bytes, filename: str = "") -> str:
        self._load_ocr()
        if filename.lower().endswith(".pdf") or file_bytes[:4] == b"%PDF":
            return self._extract_from_pdf(file_bytes)
        return self._extract_from_image(file_bytes)

    def _extract_from_pdf(self, pdf_bytes: bytes) -> str:
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                pages = [p.extract_text() for p in pdf.pages if p.extract_text()]
            text = "\n".join(pages)
            if len(text.strip()) > 50:
                return text
        except Exception as e:
            logger.warning(f"pdfplumber 추출 실패: {e}")

        try:
            from pdf2image import convert_from_bytes
            images = convert_from_bytes(pdf_bytes)
            return "\n".join(self._ocr_image(img) for img in images)
        except Exception as e:
            logger.error(f"PDF OCR 실패: {e}")
            return ""

    def _extract_from_image(self, image_bytes: bytes) -> str:
        from PIL import Image
        return self._ocr_image(Image.open(io.BytesIO(image_bytes)))

    def _ocr_image(self, image) -> str:
        try:
            if self.ocr_engine == "paddle" and self._ocr:
                import numpy as np
                result = self._ocr.ocr(np.array(image), cls=True)
                return "\n".join(line[1][0] for group in result for line in group)
            else:
                import pytesseract
                return pytesseract.image_to_string(image, lang="kor+eng")
        except Exception as e:
            logger.error(f"OCR 실패: {e}")
            return ""

    # ── 등기사항전부증명서 파싱 ───────────────────────────────────────────────

    def parse_building_registry(self, text: str) -> dict:
        """
        등기사항전부증명서(등기부등본)에서 핵심 정보 추출.

        확인 항목:
          - 부동산 주소
          - 소유자 (현재 소유권자)
          - 근저당 / 압류 / 가압류 존재 여부
          - 발급일
        """
        result: dict = {}

        # 부동산 주소 (표제부)
        addr = re.search(
            r"소\s*재\s*지\s*[:：]?\s*(.+?)(?:\n|건물|구조|면적)",
            text,
            re.DOTALL,
        )
        if addr:
            result["property_address"] = addr.group(1).strip()

        # 소유자 (현재 소유권 이전 등기 - 말소되지 않은 가장 마지막)
        owners = re.findall(
            r"소유권\s*이전.*?소유자\s+([가-힣A-Za-z0-9\s]{2,30})",
            text,
        )
        if owners:
            result["owner"] = owners[-1].strip()

        # 근저당 / 압류 / 가압류 여부 (말소 여부 포함)
        has_mortgage = bool(re.search(r"근저당권\s*설정", text))
        has_seizure = bool(re.search(r"압\s*류|가압류", text))
        erased_mortgage = bool(re.search(r"근저당권.*말소|말소.*근저당권", text))

        result["has_mortgage"] = has_mortgage and not erased_mortgage
        result["has_seizure"] = has_seizure
        result["warnings"] = []

        if result["has_mortgage"]:
            result["warnings"].append("근저당권이 설정되어 있습니다. 보증금 회수에 주의하세요.")
        if result["has_seizure"]:
            result["warnings"].append("압류/가압류가 있습니다. 임차권등기 전에 법률 상담을 받으세요.")

        # 발급일
        issue_date = self._find_date(text, patterns=[
            r"발행일\s*[:：]?\s*(\d{4})[.\-년](\d{1,2})[.\-월](\d{1,2})",
            r"열람\s*일시.*?(\d{4})\.(\d{2})\.(\d{2})",
        ])
        if issue_date:
            result["issue_date"] = issue_date

        return result

    def validate_building_registry(self, data: dict) -> list[str]:
        errors = []
        if "property_address" not in data:
            errors.append("등기부등본에서 부동산 주소를 확인할 수 없습니다.")
        if "owner" not in data:
            errors.append("소유자 정보를 확인할 수 없습니다.")
        if "issue_date" not in data:
            errors.append("발급일을 확인할 수 없습니다. 최신 서류인지 확인하세요.")
        return errors

    # ── 주민등록초본 파싱 ─────────────────────────────────────────────────────

    def parse_resident_registration(self, text: str) -> dict:
        """
        주민등록초본에서 핵심 정보 추출.

        확인 항목:
          - 현재 주소 (임차 목적물 주소와 일치 여부 확인용)
          - 전입일 (임차 목적물 전입 날짜)
          - 주소 변동 이력 (전입 증명용)
        """
        result: dict = {}

        # 성명
        name = re.search(r"성\s*명\s*[:：]?\s*([가-힣]{2,5})", text)
        if name:
            result["name"] = name.group(1)

        # 현재 주소
        current_addr = re.search(
            r"현\s*주\s*소\s*[:：]?\s*(.+?)(?:\n|전입|세대)",
            text,
            re.DOTALL,
        )
        if current_addr:
            result["current_address"] = current_addr.group(1).strip()

        # 주소 변동 이력 전체 추출 (날짜 + 주소)
        history_pattern = re.findall(
            r"(\d{4})[.\-년]\s*(\d{1,2})[.\-월]\s*(\d{1,2})일?\s+전입\s+(.+?)(?:\n|$)",
            text,
        )
        move_in_history = []
        for y, m, d, addr in history_pattern:
            try:
                date = datetime(int(y), int(m), int(d))
                move_in_history.append({"date": date, "address": addr.strip()})
            except ValueError:
                pass

        result["move_in_history"] = move_in_history

        # 임차 목적물 전입일 (가장 최근 전입)
        if move_in_history:
            latest = max(move_in_history, key=lambda x: x["date"])
            result["latest_move_in_date"] = latest["date"]
            result["latest_move_in_address"] = latest["address"]

        # 발급일
        issue_date = self._find_date(text, patterns=[
            r"발급일\s*[:：]?\s*(\d{4})[.\-년](\d{1,2})[.\-월](\d{1,2})",
            r"출력일\s*[:：]?\s*(\d{4})\.(\d{2})\.(\d{2})",
        ])
        if issue_date:
            result["issue_date"] = issue_date

        return result

    def validate_resident_registration(self, data: dict, property_address: str = "") -> list[str]:
        errors = []
        if "name" not in data:
            errors.append("주민등록초본에서 성명을 확인할 수 없습니다.")
        if not data.get("move_in_history"):
            errors.append("주소 변동 이력이 없습니다. '주소변동사항 포함' 옵션으로 재발급하세요.")
        if "issue_date" not in data:
            errors.append("발급일을 확인할 수 없습니다.")
        # 임차 목적물 주소 일치 여부
        if property_address and data.get("current_address"):
            addr_short = property_address.replace(" ", "")[:10]
            current_short = data["current_address"].replace(" ", "")[:10]
            if addr_short not in data["current_address"] and current_short not in property_address:
                errors.append(
                    f"현재 주소({data['current_address']})가 임차 목적물 주소와 다릅니다. "
                    "전입신고가 되어 있는지 확인하세요."
                )
        return errors

    # ── 임대차계약서 파싱 ─────────────────────────────────────────────────────

    def parse_contract(self, text: str) -> dict:
        result: dict = {}

        contract_date = self._find_date(text, patterns=[
            r"계약일.*?(\d{4}).*?년.*?(\d{1,2}).*?월.*?(\d{1,2}).*?일",
            r"계약\s*체결일.*?(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})",
        ])
        if contract_date:
            result["contract_date"] = contract_date

        confirmed_date = self._find_date(text, patterns=[
            r"확정일자.*?(\d{4}).*?(\d{1,2}).*?(\d{1,2})",
            r"확정\s*일자.*?(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})",
        ])
        if confirmed_date:
            result["confirmed_date"] = confirmed_date

        # 보증금 (숫자 형태)
        deposit = re.search(r"보증금[^0-9]*([0-9]{1,3}(?:,[0-9]{3})*)\s*원", text)
        if deposit:
            try:
                result["deposit_amount"] = int(deposit.group(1).replace(",", ""))
            except ValueError:
                pass

        # 보증금 (한국어 단위: 3억 5천만원)
        if "deposit_amount" not in result:
            m = re.search(
                r"보증금[^0-9억만천백]*([0-9]+억)?([0-9]+천만)?([0-9]+백만)?([0-9]+만)?원",
                text,
            )
            if m:
                total = 0
                if m.group(1): total += int(m.group(1).replace("억", "")) * 100_000_000
                if m.group(2): total += int(m.group(2).replace("천만", "")) * 10_000_000
                if m.group(3): total += int(m.group(3).replace("백만", "")) * 1_000_000
                if m.group(4): total += int(m.group(4).replace("만", "")) * 10_000
                if total:
                    result["deposit_amount"] = total

        tenant = re.search(r"임차인\s*[:：]\s*([가-힣]{2,5})", text)
        if tenant:
            result["tenant_name"] = tenant.group(1)

        landlord = re.search(r"임대인\s*[:：]\s*([가-힣A-Za-z0-9\s]{2,20})", text)
        if landlord:
            result["landlord_name"] = landlord.group(1).strip()

        address = re.search(r"임대\s*목적물\s*[:：]?\s*(.+?(?:동|호|층))", text, re.MULTILINE)
        if address:
            result["property_address"] = address.group(1).strip()

        return result

    def validate_contract(self, data: dict) -> list[str]:
        errors = []
        if "contract_date" not in data:
            errors.append("계약일을 확인할 수 없습니다.")
        if "deposit_amount" not in data:
            errors.append("보증금을 확인할 수 없습니다.")
        elif data["deposit_amount"] <= 0:
            errors.append("보증금 금액이 올바르지 않습니다.")
        if "confirmed_date" not in data:
            errors.append("확정일자 도장이 없거나 확인되지 않습니다. 확정일자가 있는 원본을 업로드하세요.")
        if "tenant_name" not in data:
            errors.append("임차인 이름을 확인할 수 없습니다.")
        if "landlord_name" not in data:
            errors.append("임대인 이름을 확인할 수 없습니다.")
        return errors

    # ── 계약해지통지서 파싱 ───────────────────────────────────────────────────

    def parse_termination_notice(self, text: str) -> dict:
        result: dict = {}

        sent_date = self._find_date(text, patterns=[
            r"발송일.*?(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})",
            r"(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일",
        ])
        if sent_date:
            result["sent_date"] = sent_date

        recipient = re.search(r"수신\s*[:：]\s*([가-힣]{2,5})", text)
        if recipient:
            result["recipient"] = recipient.group(1)

        result["has_termination_content"] = any(
            kw in text for kw in ["계약 해지", "계약해지", "해지 통보", "해지통보", "임대차 종료"]
        )
        return result

    # ── 서류 간 교차 검증 ─────────────────────────────────────────────────────

    def cross_validate(
        self,
        contract: dict,
        registry: dict,
        resident: dict,
    ) -> list[str]:
        """
        3개 서류의 내용이 서로 일치하는지 교차 검증.
        불일치 항목을 경고로 반환 (오류가 아닌 확인 요청).
        """
        warnings = []

        # 계약서 임대인 == 등기부 소유자
        if contract.get("landlord_name") and registry.get("owner"):
            if contract["landlord_name"] not in registry["owner"] and \
               registry["owner"] not in contract["landlord_name"]:
                warnings.append(
                    f"계약서 임대인({contract['landlord_name']})과 "
                    f"등기부 소유자({registry['owner']})가 다릅니다. "
                    "전대차 계약이거나 소유권 변동이 있을 수 있습니다."
                )

        # 계약서 주소 == 등기부 주소
        if contract.get("property_address") and registry.get("property_address"):
            c_addr = contract["property_address"].replace(" ", "")[:15]
            r_addr = registry["property_address"].replace(" ", "")[:15]
            if c_addr not in registry["property_address"] and r_addr not in contract["property_address"]:
                warnings.append(
                    "계약서와 등기부등본의 주소가 일치하지 않습니다. 확인이 필요합니다."
                )

        # 주민등록초본 — 임차 목적물 전입 확인
        if not resident.get("move_in_history"):
            warnings.append("주민등록초본에 전입 이력이 없습니다. 대항력이 없을 수 있습니다.")

        return warnings

    # ── 헬퍼 ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _find_date(text: str, patterns: list[str]) -> Optional[datetime]:
        for pattern in patterns:
            m = re.search(pattern, text)
            if m:
                try:
                    return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                except (ValueError, IndexError):
                    continue
        return None
