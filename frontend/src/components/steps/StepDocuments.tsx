'use client'

import { useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, CheckCircle, AlertCircle } from 'lucide-react'
import { uploadDocument } from '@/lib/api'

interface DocUploadState {
  file: File | null
  uploaded: boolean
  error: string
}

interface Props {
  applicationId?: string
  onStart: (certPassword: string, file: File) => void
  isSubmitting: boolean
}

export default function StepDocuments({ applicationId, onStart, isSubmitting }: Props) {
  const [leaseContract, setLeaseContract] = useState<DocUploadState>({ file: null, uploaded: false, error: '' })
  const [terminationNotice, setTerminationNotice] = useState<DocUploadState>({ file: null, uploaded: false, error: '' })

  const makeDropzone = (
    docType: string,
    setState: React.Dispatch<React.SetStateAction<DocUploadState>>,
  ) => useDropzone({
    accept: { 'application/pdf': ['.pdf'], 'image/*': ['.jpg', '.jpeg', '.png'] },
    maxFiles: 1,
    onDrop: async (files) => {
      if (!files[0]) return
      setState((s) => ({ ...s, file: files[0], uploaded: false, error: '' }))
    },
  })

  const leaseDropzone = makeDropzone('lease_contract', setLeaseContract)
  const terminationDropzone = makeDropzone('termination_notice', setTerminationNotice)

  return (
    <div className="space-y-5">
      <p className="text-sm text-gray-500">
        자동 수집이 불가능한 서류를 직접 업로드해주세요.
        임대차계약서는 <span className="font-semibold text-[#1a1a2e]">확정일자 도장이 있는 원본</span>이어야 합니다.
      </p>

      {/* 임대차계약서 */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <label className="text-sm font-medium">임대차계약서</label>
          <span className="text-xs bg-red-100 text-red-600 px-2 py-0.5 rounded-full">필수</span>
        </div>
        <div
          {...leaseDropzone.getRootProps()}
          className={`border-2 border-dashed rounded-2xl p-5 text-center cursor-pointer transition-colors ${
            leaseContract.file
              ? 'border-green-400 bg-green-50'
              : 'border-gray-200 bg-gray-50'
          }`}
        >
          <input {...leaseDropzone.getInputProps()} />
          {leaseContract.file ? (
            <div className="flex items-center justify-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-500" />
              <span className="text-sm text-green-700">{leaseContract.file.name}</span>
            </div>
          ) : (
            <div>
              <Upload className="w-6 h-6 mx-auto mb-1 text-gray-400" />
              <p className="text-xs text-gray-400">PDF 또는 이미지 업로드</p>
            </div>
          )}
        </div>
      </div>

      {/* 계약해지통지서 */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <label className="text-sm font-medium">계약해지통지서</label>
          <span className="text-xs bg-yellow-100 text-yellow-600 px-2 py-0.5 rounded-full">권장</span>
        </div>
        <div
          {...terminationDropzone.getRootProps()}
          className={`border-2 border-dashed rounded-2xl p-5 text-center cursor-pointer transition-colors ${
            terminationNotice.file
              ? 'border-green-400 bg-green-50'
              : 'border-gray-200 bg-gray-50'
          }`}
        >
          <input {...terminationDropzone.getInputProps()} />
          {terminationNotice.file ? (
            <div className="flex items-center justify-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-500" />
              <span className="text-sm text-green-700">{terminationNotice.file.name}</span>
            </div>
          ) : (
            <div>
              <Upload className="w-6 h-6 mx-auto mb-1 text-gray-400" />
              <p className="text-xs text-gray-400">문자/카카오톡 캡처 이미지도 가능</p>
            </div>
          )}
        </div>
        <p className="text-xs text-gray-400 mt-1">
          내용증명, 문자 메시지, 카카오톡 대화 캡처 모두 가능합니다.
        </p>
      </div>

      {!leaseContract.file && (
        <div className="flex items-center gap-2 p-3 bg-amber-50 rounded-xl border border-amber-100">
          <AlertCircle className="w-4 h-4 text-amber-500 shrink-0" />
          <p className="text-xs text-amber-600">임대차계약서는 필수 서류입니다.</p>
        </div>
      )}

      <button
        type="button"
        className="btn-primary"
        disabled={!leaseContract.file || isSubmitting}
        onClick={() => {
          // StepDocuments는 마지막 단계 — 상위에서 certFile을 관리
          // 실제로는 apply page에서 처리
          onStart('', new File([], ''))
        }}
      >
        {isSubmitting ? '서류 수집 시작 중...' : '서류 자동 수집 시작'}
      </button>
    </div>
  )
}
