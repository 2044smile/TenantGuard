"""
OpenCV + Tesseract OCR 서비스

파이프라인:
  이미지/PDF 입력
    → pdfplumber (텍스트 레이어 있는 PDF)
    → pdf2image (스캔 PDF → 이미지 변환)
    → OpenCV 전처리 (그레이스케일 / CLAHE / 적응형 이진화 / 기울기보정)
    → Tesseract (한국어+영어, 3가지 이미지 × 3가지 PSM 조합)
    → 후처리 노이즈 제거
    → 정규식 필드 파싱
"""
import io
import re
import time
import logging
from typing import Optional
from datetime import datetime

import cv2
import numpy as np
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)


class OCRService:

    # ── 전처리 ────────────────────────────────────────────────────────────────

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Tesseract가 글자를 잘 인식하도록 이미지를 정제하는 4단계 파이프라인.

        [1단계] 그레이스케일(Grayscale) 변환
          컬러 이미지(R, G, B 3채널)를 밝기값만 있는 흑백(1채널)으로 변환합니다.
          Tesseract는 흑백 이미지를 기준으로 설계되어 있어 컬러 정보가 오히려 방해됩니다.
          예) [255, 0, 0](빨간색) → 29(어두운 회색)
              [255, 255, 255](흰색) → 255(흰색)

        [2단계] 해상도 업스케일
          이미지 폭이 1800px 미만이면 비율을 유지하며 확대합니다.
          Tesseract는 글자 높이가 20~30px 미만이면 인식률이 급격히 떨어지기 때문입니다.
          INTER_CUBIC: 주변 4×4 픽셀을 참고해 부드럽게 확대 (단순 복사보다 품질 우수)

        [3단계] CLAHE (Contrast Limited Adaptive Histogram Equalization)
          이미지 전체에 하나의 밝기 기준을 적용하지 않고,
          이미지를 8×8 격자로 나눠 각 구역마다 명암 대비를 독립적으로 강화합니다.
          - clipLimit=2.0: 과도한 대비 강화를 막는 상한선
          - 효과: 한쪽은 밝고 한쪽은 어두운 문서(그림자, 스캔 불균일)에서 전체 텍스트가 선명해짐

        [4단계] 적응형 이진화 (Adaptive Thresholding)
          픽셀을 0(검정) 또는 255(흰색) 둘 중 하나로 결정합니다.
          전역 임계값(Otsu) 방식과 달리, 각 픽셀 주변 31×31 블록의 평균 밝기를 기준으로 판단합니다.
          - ADAPTIVE_THRESH_GAUSSIAN_C: 주변 픽셀에 가우시안 가중치 적용 (중심 픽셀 영향력 큼)
          - C=10: 계산된 평균에서 10을 빼서 기준값으로 사용 (미세 조정)
          - 효과: 초록 배경에 흰 글씨, 그림자가 드리운 계약서 등 전역 임계값으로 처리 불가한 경우 대응
        """
        # [1단계] 그레이스케일 변환 — 컬러면 변환, 이미 흑백이면 그대로
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image.copy()

        # [2단계] 해상도 업스케일 — 1800px 미만이면 확대
        h, w = gray.shape
        if w < 1800:
            scale = 1800 / w
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        # [3단계] CLAHE — 구역별 명암 대비 강화
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # [4단계] 적응형 이진화 — 완전한 흑백으로 변환
        binary = cv2.adaptiveThreshold(
            enhanced, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=31,   # 판단 기준이 되는 주변 블록 크기 (31×31 픽셀)
            C=10,           # 평균에서 빼는 보정값 (클수록 더 많은 픽셀이 흰색으로)
        )
        return binary

    def deskew(self, image: np.ndarray) -> np.ndarray:
        """
        기울기 보정 (Deskewing)

        스캔하거나 촬영할 때 문서가 살짝 기울면 Tesseract가 줄 단위 인식을 실패합니다.
        텍스트 픽셀(어두운 픽셀)들의 좌표 분포로 기울기 각도를 계산한 뒤 반대로 회전시킵니다.

        동작 원리:
          1) 어두운 픽셀(값 < 128)의 좌표를 모두 수집
          2) 그 좌표들을 감싸는 최소 면적 직사각형(minAreaRect)의 각도 추출
          3) 회전 행렬(getRotationMatrix2D)로 이미지를 반대 방향으로 회전
          4) 0.5도 미만은 무시 (오히려 미세하게 망가질 수 있음)
        """
        coords = np.column_stack(np.where(image < 128))  # 어두운 픽셀 좌표 수집
        if len(coords) < 10:
            return image  # 픽셀이 너무 적으면 보정 불가 → 원본 반환

        angle = cv2.minAreaRect(coords)[-1]
        # minAreaRect 각도 규칙: -90~0도 범위로 반환 → 실제 기울기로 변환
        angle = -(90 + angle) if angle < -45 else -angle

        if abs(angle) < 0.5:
            return image  # 0.5도 미만은 보정 불필요

        h, w = image.shape
        M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)  # 중심 기준 회전 행렬
        return cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC,
                              borderMode=cv2.BORDER_REPLICATE)  # 빈 가장자리를 인접 픽셀로 채움

    # ── 텍스트 추출 ───────────────────────────────────────────────────────────

    def _ocr_pil(self, pil_image: Image.Image) -> str:
        """
        이미지 1장에서 텍스트를 추출하는 핵심 메서드.

        단순히 한 가지 방법으로 OCR하지 않고, 3가지 이미지 × 3가지 PSM = 최대 9회 시도합니다.
        한글 글자([가-힣])가 가장 많이 추출된 결과를 최선으로 채택합니다.

        [3가지 이미지 변형]
          processed : 적응형 이진화 완료본 → 밝은 배경에 어두운 글씨 (일반 문서)
          inverted  : processed를 색 반전  → 어두운 배경에 밝은 글씨 (카카오톡, 야간 캡처)
          gray      : 원본 그레이스케일    → 이진화가 오히려 텍스트를 손상시키는 경우 대비

        [3가지 PSM (Page Segmentation Mode)]
          PSM 3  : 완전 자동 페이지 분할 — 레이아웃이 복잡한 문서 (혼합 레이아웃)
          PSM 6  : 단일 텍스트 블록 가정 — 깔끔하게 인쇄된 계약서·등본
          PSM 11 : 분산 텍스트 모드      — UI 캡처, 메시지, 라벨이 흩어진 이미지

        [조기 종료 최적화]
          첫 번째 이미지(processed)에서 한글 30자 이상 추출되면 나머지 6회 생략.
          대부분의 일반 문서는 첫 번째에서 해결됩니다.
        """
        img_np = np.array(pil_image.convert("RGB"))

        # 3가지 이미지 변형 준비
        processed = self.deskew(self.preprocess(img_np))   # 전처리 + 기울기 보정
        inverted  = cv2.bitwise_not(processed)             # 색 반전 (0↔255)
        gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)
        if gray.shape[1] < 1800:
            scale = 1800 / gray.shape[1]
            gray  = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        variants = [processed, inverted, gray]

        # 3가지 PSM 설정 (OEM 3 = LSTM 신경망 엔진 사용)
        configs = [
            "--oem 3 --psm 3 -c preserve_interword_spaces=1",   # 자동 분할
            "--oem 3 --psm 6 -c preserve_interword_spaces=1",   # 단일 블록
            "--oem 3 --psm 11 -c preserve_interword_spaces=1",  # 분산 텍스트
        ]

        best, best_ko = "", 0
        for img_variant in variants:
            for cfg in configs:
                text = pytesseract.image_to_string(
                    Image.fromarray(img_variant), lang="kor+eng", config=cfg
                )
                ko_count = len(re.findall(r"[가-힣]", text))
                if ko_count > best_ko:
                    best, best_ko = text, ko_count

            # 조기 종료: 한글 30자 이상이면 충분 → 나머지 이미지 변형 생략
            if best_ko >= 30:
                break

        return _clean_text(best)

    def extract_text_from_image(self, image_bytes: bytes) -> str:
        """이미지 바이트 → PIL Image 변환 후 OCR"""
        pil = Image.open(io.BytesIO(image_bytes))
        return self._ocr_pil(pil)

    def extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """
        PDF에서 텍스트를 추출합니다. 두 단계로 시도합니다.

        [1단계] pdfplumber — 텍스트 레이어 직접 추출 (빠름, 100% 정확)
          인터넷등기소·정부24에서 발급한 PDF는 텍스트가 이미 파일 안에 내장돼 있습니다.
          이 경우 OCR 없이 바로 텍스트를 꺼낼 수 있습니다.
          50자 이상 추출되면 성공으로 판단하고 즉시 반환합니다.

        [2단계] pdf2image + OCR — 스캔 PDF 처리 (느림)
          텍스트 레이어가 없는 스캔본 PDF는 페이지를 이미지(300dpi)로 변환 후 OCR합니다.
          dpi=300: 해상도 기준값. 낮으면 글자가 뭉개지고, 너무 높으면 처리가 오래 걸림.
        """
        # [1단계] 텍스트 레이어 직접 추출
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                pages = [p.extract_text() or "" for p in pdf.pages]
            text = "\n".join(pages).strip()
            if len(text) > 50:
                logger.info(f"[OCR] pdfplumber 직접 추출 성공 ({len(text)}자)")
                return text
        except Exception as e:
            logger.warning(f"[OCR] pdfplumber 실패: {e}")

        # [2단계] 스캔 PDF → 이미지 변환 후 OCR
        try:
            from pdf2image import convert_from_bytes
            images = convert_from_bytes(pdf_bytes, dpi=300)
            texts = [self._ocr_pil(img) for img in images]
            result = "\n".join(texts)
            logger.info(f"[OCR] 스캔 PDF OCR 완료 ({len(images)}페이지, {len(result)}자)")
            return result
        except Exception as e:
            logger.error(f"[OCR] 스캔 PDF OCR 실패: {e}")
            return ""

    def extract_text(self, file_bytes: bytes, filename: str = "") -> tuple[str, float]:
        """
        파일 확장자/시그니처로 PDF vs 이미지를 자동 판별 후 텍스트 추출.

        PDF 판별 기준:
          - 파일명이 .pdf로 끝나거나
          - 파일 첫 4바이트가 b"%PDF" (PDF 파일 시그니처)

        Returns: (추출된 텍스트, 처리 시간(초))
        """
        t0 = time.time()
        is_pdf = filename.lower().endswith(".pdf") or file_bytes[:4] == b"%PDF"
        text = self.extract_text_from_pdf(file_bytes) if is_pdf \
            else self.extract_text_from_image(file_bytes)
        return text, round(time.time() - t0, 2)

    # ── 서류별 필드 파싱 ──────────────────────────────────────────────────────

    def parse(self, text: str, doc_type: str) -> dict:
        """서류 종류에 맞는 파서를 선택해 정규식으로 필드를 추출합니다."""
        parsers = {
            "building_registry":     self._parse_building_registry,
            "resident_registration": self._parse_resident_registration,
            "lease_contract":        self._parse_lease_contract,
            "termination_notice":    self._parse_termination_notice,
        }
        fn = parsers.get(doc_type)
        return fn(text) if fn else {}

    def _find_date(self, text: str, *patterns: str) -> Optional[str]:
        """
        여러 날짜 패턴을 순서대로 시도해 처음 매칭되는 날짜를 반환합니다.
        반환 형식: "YYYY-MM-DD"
        """
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                try:
                    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
                    return datetime(y, mo, d).strftime("%Y-%m-%d")
                except (ValueError, IndexError):
                    continue
        return None

    def _find_phone(self, text: str) -> Optional[str]:
        """
        전화번호 추출.
        패턴: 0으로 시작, 2~3자리 지역번호/휴대폰번호, 하이픈·공백 허용
        예) 010-7710-4604, 02 123 4567
        """
        m = re.search(r"(0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4})", text)
        return m.group(1) if m else None

    def _find_amount(self, text: str) -> Optional[int]:
        """
        금액 추출. 두 가지 표기법을 모두 지원합니다.

        숫자 표기: 300,000,000원 → 300000000
        한국어 표기: 3억 5천만원 → 350000000
          - 억(×1억), 천만(×1000만), 백만(×100만), 만(×1만) 단위 파싱
        """
        # 숫자 표기: 쉼표 포함 숫자
        m = re.search(r"([0-9]{1,3}(?:,[0-9]{3})+)\s*원", text)
        if m:
            return int(m.group(1).replace(",", ""))

        # 한국어 단위 표기
        m = re.search(
            r"([0-9]+억)?\s*([0-9]+천만)?\s*([0-9]+백만)?\s*([0-9]+만)?\s*원",
            text,
        )
        if m and any(m.group(i) for i in range(1, 5)):
            total = 0
            if m.group(1): total += int(m.group(1).replace("억","")) * 100_000_000
            if m.group(2): total += int(m.group(2).replace("천만","")) * 10_000_000
            if m.group(3): total += int(m.group(3).replace("백만","")) * 1_000_000
            if m.group(4): total += int(m.group(4).replace("만","")) * 10_000
            return total if total else None
        return None

    def _parse_building_registry(self, text: str) -> dict:
        """
        건물등기사항증명서(등기부등본) 파싱.

        추출 항목:
          - property_address : 표제부의 소재지 (임차 부동산 주소)
          - owner            : 현재 소유자 (소유권 이전 등기 중 마지막 = 현재 소유자)
          - has_mortgage     : 근저당권 설정 여부 (말소된 것은 제외)
          - has_seizure      : 압류/가압류 여부
          - issue_date       : 발급일
          - warnings         : 주의사항 (근저당·압류 있으면 경고 추가)
        """
        result: dict = {"doc_type": "건물등기사항증명서"}

        addr = re.search(r"소\s*재\s*지\s*[:：]?\s*(.+?)(?:\n|건물|구조|면적)", text, re.DOTALL)
        if addr:
            result["property_address"] = addr.group(1).strip()

        # 소유권 이전 등기가 여러 개일 수 있으므로 findall로 전부 찾아 마지막(현재 소유자) 사용
        owners = re.findall(r"소유권\s*이전.*?소유자\s+([가-힣A-Za-z0-9\s]{2,20})", text)
        if owners:
            result["owner"] = owners[-1].strip()

        # 근저당: 설정됐으나 말소되지 않은 경우만 True
        result["has_mortgage"] = bool(re.search(r"근저당권\s*설정", text)) and \
                                  not bool(re.search(r"근저당권.*말소", text))
        result["has_seizure"]  = bool(re.search(r"압\s*류|가압류", text))

        result["issue_date"] = self._find_date(
            text,
            r"발행일\s*[:：]?\s*(\d{4})[.\-년](\d{1,2})[.\-월](\d{1,2})",
            r"열람\s*일시.*?(\d{4})\.(\d{2})\.(\d{2})",
        )

        warnings = []
        if result["has_mortgage"]:
            warnings.append("근저당권 설정 — 보증금 회수 주의")
        if result["has_seizure"]:
            warnings.append("압류/가압류 있음 — 법률 상담 권장")
        result["warnings"] = warnings
        return result

    def _parse_resident_registration(self, text: str) -> dict:
        """
        주민등록초본 파싱.

        추출 항목:
          - name             : 성명
          - current_address  : 현재 주소 (임차 목적물 주소와 일치 여부 확인용)
          - move_in_history  : 전입 이력 목록 [{date, address}, ...]
          - issue_date       : 발급일
        """
        result: dict = {"doc_type": "주민등록초본"}

        m = re.search(r"성\s*명\s*[:：]?\s*([가-힣]{2,5})", text)
        if m:
            result["name"] = m.group(1)

        addr = re.search(r"현\s*주\s*소\s*[:：]?\s*(.+?)(?:\n|전입|세대)", text, re.DOTALL)
        if addr:
            result["current_address"] = addr.group(1).strip()

        # 전입 이력: "2023년 3월 15일 전입 서울특별시..." 형태 파싱
        history = re.findall(
            r"(\d{4})[.\-년]\s*(\d{1,2})[.\-월]\s*(\d{1,2})일?\s+전입\s+(.+?)(?:\n|$)", text
        )
        move_ins = []
        for y, mo, d, addr_str in history:
            try:
                move_ins.append({
                    "date": datetime(int(y), int(mo), int(d)).strftime("%Y-%m-%d"),
                    "address": addr_str.strip(),
                })
            except ValueError:
                pass
        result["move_in_history"] = move_ins

        result["issue_date"] = self._find_date(
            text,
            r"발급일\s*[:：]?\s*(\d{4})[.\-년](\d{1,2})[.\-월](\d{1,2})",
            r"출력일\s*[:：]?\s*(\d{4})\.(\d{2})\.(\d{2})",
        )
        return result

    def _parse_lease_contract(self, text: str) -> dict:
        """
        임대차계약서 파싱.

        추출 항목:
          - landlord_name    : 임대인 이름
          - tenant_name      : 임차인 이름
          - phone            : 전화번호 (첫 번째 발견)
          - deposit_amount   : 보증금 (원 단위 정수)
          - deposit_display  : 보증금 (한국어 표기, eg. "3억원")
          - contract_date    : 계약일
          - confirmed_date   : 확정일자
          - property_address : 임대 목적물 주소
        """
        result: dict = {"doc_type": "임대차계약서"}

        m = re.search(r"임대인\s*[:：]\s*([가-힣A-Za-z0-9\s]{2,20})", text)
        if m:
            result["landlord_name"] = m.group(1).strip()

        m = re.search(r"임차인\s*[:：]\s*([가-힣]{2,5})", text)
        if m:
            result["tenant_name"] = m.group(1)

        phone = self._find_phone(text)
        if phone:
            result["phone"] = phone

        amount = self._find_amount(text)
        if amount:
            result["deposit_amount"] = amount
            result["deposit_display"] = _format_krw(amount)

        result["contract_date"] = self._find_date(
            text,
            r"계약일.*?(\d{4}).*?년.*?(\d{1,2}).*?월.*?(\d{1,2}).*?일",
            r"(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})\s*계약",
        )
        result["confirmed_date"] = self._find_date(
            text,
            r"확정일자.*?(\d{4}).*?(\d{1,2}).*?(\d{1,2})",
        )

        addr = re.search(r"임대\s*목적물\s*[:：]?\s*(.+?(?:동|호|층))", text, re.MULTILINE)
        if addr:
            result["property_address"] = addr.group(1).strip()

        return result

    def _parse_termination_notice(self, text: str) -> dict:
        """
        계약해지통지서 파싱.

        추출 항목:
          - recipient               : 수신인 (임대인 이름)
          - sent_date               : 발송일
          - phone                   : 전화번호
          - requested_amount        : 반환 요구 금액
          - has_termination_keyword : 해지 의사 표시 키워드 포함 여부
        """
        result: dict = {"doc_type": "계약해지통지서"}

        m = re.search(r"수신\s*[:：]\s*([가-힣]{2,5})", text)
        if m:
            result["recipient"] = m.group(1)

        result["sent_date"] = self._find_date(
            text,
            r"(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일",
        )

        phone = self._find_phone(text)
        if phone:
            result["phone"] = phone

        amount = self._find_amount(text)
        if amount:
            result["requested_amount"] = amount
            result["requested_display"] = _format_krw(amount)

        # 해지 의사 표시 키워드 존재 여부 확인
        result["has_termination_keyword"] = any(
            kw in text for kw in ["계약 해지", "계약해지", "해지 통보", "임대차 종료"]
        )
        return result


def _clean_text(text: str) -> str:
    """
    OCR 후처리 — 노이즈 줄 제거.

    스마트폰 상태바(배터리, 시간), 앱 UI 아이콘, 버튼 텍스트는
    한글이 없고 짧은 줄로 나타나는 경향이 있습니다.

    제거 기준:
      1) 한글이 없고 길이 10자 이하인 줄 → UI 노이즈 (eg. "20140", "Vv", "CR.")
      2) 특수문자·알파벳만 있고 1~6자인 줄 → 아이콘 오인식

    정리:
      - 연속 빈 줄 3개 이상 → 2개로 압축 (가독성)
    """
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            cleaned.append("")
            continue
        korean_count = len(re.findall(r"[가-힣]", stripped))

        # 한글 없고 짧은 줄 제거
        if korean_count == 0 and len(stripped) <= 10:
            continue
        # 특수문자·알파벳만 있는 매우 짧은 줄 제거
        if korean_count == 0 and re.fullmatch(r"[^가-힣ㄱ-ㅎ0-9\s]{1,6}", stripped):
            continue
        cleaned.append(line)

    result = re.sub(r"\n{3,}", "\n\n", "\n".join(cleaned))
    return result.strip()


def _format_krw(amount: int) -> str:
    """
    금액을 한국어 단위로 표기합니다.
    예) 350000000 → "3억 5,000만원"
        10000000  → "1,000만원"
    """
    eok = amount // 100_000_000
    man = (amount % 100_000_000) // 10_000
    parts = []
    if eok: parts.append(f"{eok}억")
    if man: parts.append(f"{man:,}만")
    return " ".join(parts) + "원" if parts else f"{amount:,}원"
