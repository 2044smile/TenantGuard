'use client'

import { useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, CheckCircle, AlertCircle } from 'lucide-react'

interface DocUploadState {
  file: File | null
  uploaded: boolean
  error: string
}

interface Props {
  applicationId?: string
  onStart: () => void
  isSubmitting: boolean
}

export default function StepDocuments({ applicationId, onStart, isSubmitting }: Props) {
  const [leaseContract, setLeaseContract] = useState<DocUploadState>({ file: null, uploaded: false, error: '' })
  const [terminationNotice, setTerminationNotice] = useState<DocUploadState>({ file: null, uploaded: false, error: '' })

  const makeDropzone = (
    setState: React.Dispatch<React.SetStateAction<DocUploadState>>,
  ) => useDropzone({
    accept: { 'application/pdf': ['.pdf'], 'image/*': ['.jpg', '.jpeg', '.png'] },
    maxFiles: 1,
    onDrop: async (files) => {
      if (!files[0]) return
      setState((s) => ({ ...s, file: files[0], uploaded: false, error: '' }))
    },
  })

  const leaseDropzone = makeDropzone(setLeaseContract)
  const terminationDropzone = makeDropzone(setTerminationNotice)

  return (
    <div className="space-y-5">
      <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
        자동 수집이 불가능한 서류를 직접 업로드해주세요.
        임대차계약서는{' '}
        <span className="font-semibold" style={{ color: 'var(--text)' }}>
          확정일자 도장이 있는 원본
        </span>
        이어야 합니다.
      </p>

      {/* 임대차계약서 */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <label className="label mb-0">임대차계약서</label>
          <span
            className="text-[10px] font-bold px-2 py-0.5 rounded-full"
            style={{ background: 'var(--error-bg)', color: 'var(--error)' }}
          >
            필수
          </span>
        </div>
        <div
          {...leaseDropzone.getRootProps()}
          className="border-2 border-dashed rounded-2xl p-5 text-center cursor-pointer transition-all"
          style={{
            borderColor: leaseContract.file ? 'var(--success)' : 'var(--border)',
            background: leaseContract.file ? 'var(--success-bg)' : 'var(--surface-2)',
          }}
        >
          <input {...leaseDropzone.getInputProps()} />
          {leaseContract.file ? (
            <div className="flex items-center justify-center gap-2">
              <CheckCircle className="w-5 h-5 shrink-0" style={{ color: 'var(--success)' }} />
              <span className="text-sm font-medium" style={{ color: 'var(--success)' }}>
                {leaseContract.file.name}
              </span>
            </div>
          ) : (
            <div>
              <Upload className="w-6 h-6 mx-auto mb-1.5" style={{ color: 'var(--text-muted)' }} />
              <p className="text-xs" style={{ color: 'var(--text-muted)' }}>PDF 또는 이미지 업로드</p>
            </div>
          )}
        </div>
      </div>

      {/* 계약해지통지서 */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <label className="label mb-0">계약해지통지서</label>
          <span
            className="text-[10px] font-bold px-2 py-0.5 rounded-full"
            style={{ background: 'var(--warning-bg)', color: 'var(--warning)' }}
          >
            권장
          </span>
        </div>
        <div
          {...terminationDropzone.getRootProps()}
          className="border-2 border-dashed rounded-2xl p-5 text-center cursor-pointer transition-all"
          style={{
            borderColor: terminationNotice.file ? 'var(--success)' : 'var(--border)',
            background: terminationNotice.file ? 'var(--success-bg)' : 'var(--surface-2)',
          }}
        >
          <input {...terminationDropzone.getInputProps()} />
          {terminationNotice.file ? (
            <div className="flex items-center justify-center gap-2">
              <CheckCircle className="w-5 h-5 shrink-0" style={{ color: 'var(--success)' }} />
              <span className="text-sm font-medium" style={{ color: 'var(--success)' }}>
                {terminationNotice.file.name}
              </span>
            </div>
          ) : (
            <div>
              <Upload className="w-6 h-6 mx-auto mb-1.5" style={{ color: 'var(--text-muted)' }} />
              <p className="text-xs" style={{ color: 'var(--text-muted)' }}>문자/카카오톡 캡처 이미지도 가능</p>
            </div>
          )}
        </div>
        <p className="hint-text">내용증명, 문자 메시지, 카카오톡 대화 캡처 모두 가능합니다.</p>
      </div>

      {!leaseContract.file && (
        <div
          className="flex items-center gap-2.5 p-3 rounded-xl"
          style={{ background: 'var(--warning-bg)', border: '1px solid rgba(245,158,11,0.2)' }}
        >
          <AlertCircle className="w-4 h-4 shrink-0" style={{ color: 'var(--warning)' }} />
          <p className="text-xs" style={{ color: 'var(--warning)' }}>임대차계약서는 필수 서류입니다.</p>
        </div>
      )}

      <div className="pt-2">
        <button
          type="button"
          className="btn-primary"
          disabled={!leaseContract.file || isSubmitting}
          onClick={() => onStart()}
        >
          {isSubmitting ? '서류 수집 시작 중...' : '서류 자동 수집 시작'}
        </button>
      </div>
    </div>
  )
}
