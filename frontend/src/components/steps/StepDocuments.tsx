'use client'

import { useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, CheckCircle, AlertCircle, ExternalLink } from 'lucide-react'

interface DocUploadState {
  file: File | null
}

interface Props {
  onStart: (files: Record<string, File>) => void
  isSubmitting: boolean
}

type DocKey = 'building_registry' | 'resident_registration' | 'lease_contract' | 'termination_notice'

const DOC_CONFIG: Record<DocKey, {
  label: string
  required: boolean
  hint: string
  guide: string
}> = {
  building_registry: {
    label: '건물등기사항증명서',
    required: true,
    hint: 'PDF 또는 이미지 업로드',
    guide: '인터넷등기소(iros.go.kr) → 부동산 열람·발급 → 무료 열람 후 저장',
  },
  resident_registration: {
    label: '주민등록초본 (주소변동이력 포함)',
    required: true,
    hint: 'PDF 또는 이미지 업로드',
    guide: '정부24(gov.kr) → 주민등록표초본 → 주소변동사항 포함 선택 후 발급',
  },
  lease_contract: {
    label: '임대차계약서',
    required: true,
    hint: '확정일자 도장이 있는 원본',
    guide: '확정일자 도장이 찍힌 계약서 원본을 스캔 또는 촬영해주세요.',
  },
  termination_notice: {
    label: '계약해지통지서',
    required: false,
    hint: '문자·카카오톡 캡처 이미지도 가능',
    guide: '내용증명, 문자 메시지, 카카오톡 대화 캡처 모두 가능합니다.',
  },
}

const DOC_KEYS: DocKey[] = ['building_registry', 'resident_registration', 'lease_contract', 'termination_notice']

function DocUploadArea({
  docKey,
  state,
  onDrop,
}: {
  docKey: DocKey
  state: DocUploadState
  onDrop: (file: File) => void
}) {
  const config = DOC_CONFIG[docKey]
  const { getRootProps, getInputProps } = useDropzone({
    accept: { 'application/pdf': ['.pdf'], 'image/*': ['.jpg', '.jpeg', '.png'] },
    maxFiles: 1,
    onDrop: (files) => { if (files[0]) onDrop(files[0]) },
  })

  return (
    <div>
      <div className="flex items-center gap-2 mb-1.5">
        <label className="label mb-0">{config.label}</label>
        <span
          className="text-[10px] font-bold px-2 py-0.5 rounded-full"
          style={{
            background: config.required ? 'var(--error-bg)' : 'var(--warning-bg)',
            color: config.required ? 'var(--error)' : 'var(--warning)',
          }}
        >
          {config.required ? '필수' : '권장'}
        </span>
      </div>
      <div
        {...getRootProps()}
        className="border-2 border-dashed rounded-2xl p-4 text-center cursor-pointer transition-all"
        style={{
          borderColor: state.file ? 'var(--success)' : 'var(--border)',
          background: state.file ? 'var(--success-bg)' : 'var(--surface-2)',
        }}
      >
        <input {...getInputProps()} />
        {state.file ? (
          <div className="flex items-center justify-center gap-2">
            <CheckCircle className="w-4 h-4 shrink-0" style={{ color: 'var(--success)' }} />
            <span className="text-sm font-medium truncate" style={{ color: 'var(--success)' }}>
              {state.file.name}
            </span>
          </div>
        ) : (
          <div>
            <Upload className="w-5 h-5 mx-auto mb-1" style={{ color: 'var(--text-muted)' }} />
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{config.hint}</p>
          </div>
        )}
      </div>
      <p className="text-[11px] mt-1.5 leading-relaxed flex items-start gap-1" style={{ color: 'var(--text-muted)' }}>
        <ExternalLink className="w-3 h-3 mt-0.5 shrink-0" />
        {config.guide}
      </p>
    </div>
  )
}

export default function StepDocuments({ onStart, isSubmitting }: Props) {
  const [docs, setDocs] = useState<Record<DocKey, DocUploadState>>({
    building_registry: { file: null },
    resident_registration: { file: null },
    lease_contract: { file: null },
    termination_notice: { file: null },
  })

  const setFile = (key: DocKey, file: File) => {
    setDocs((prev) => ({ ...prev, [key]: { file } }))
  }

  const requiredKeys: DocKey[] = ['building_registry', 'resident_registration', 'lease_contract']
  const allRequiredUploaded = requiredKeys.every((k) => docs[k].file !== null)

  const handleStart = () => {
    const files: Record<string, File> = {}
    for (const key of DOC_KEYS) {
      if (docs[key].file) files[key] = docs[key].file!
    }
    onStart(files)
  }

  return (
    <div className="space-y-5">
      <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
        아래 서류를 준비하여 업로드해주세요. 건축물대장은 자동으로 수집됩니다.
      </p>

      {DOC_KEYS.map((key) => (
        <DocUploadArea
          key={key}
          docKey={key}
          state={docs[key]}
          onDrop={(file) => setFile(key, file)}
        />
      ))}

      {!allRequiredUploaded && (
        <div
          className="flex items-center gap-2.5 p-3 rounded-xl"
          style={{ background: 'var(--warning-bg)', border: '1px solid rgba(245,158,11,0.2)' }}
        >
          <AlertCircle className="w-4 h-4 shrink-0" style={{ color: 'var(--warning)' }} />
          <p className="text-xs" style={{ color: 'var(--warning)' }}>
            필수 서류 3종을 모두 업로드해야 진행할 수 있습니다.
          </p>
        </div>
      )}

      <div className="pt-2">
        <button
          type="button"
          className="btn-primary"
          disabled={!allRequiredUploaded || isSubmitting}
          onClick={handleStart}
        >
          {isSubmitting ? '업로드 중...' : '서류 제출 및 신청 시작'}
        </button>
      </div>
    </div>
  )
}
