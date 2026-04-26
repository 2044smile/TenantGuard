'use client'

import { useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Lock, FileKey, Eye, EyeOff } from 'lucide-react'

interface Props {
  onNext: (certPassword: string, file: File) => void
}

export default function StepCertificate({ onNext }: Props) {
  const [certFile, setCertFile] = useState<File | null>(null)
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { 'application/x-pkcs12': ['.pfx', '.p12'] },
    maxFiles: 1,
    onDrop: (files) => {
      if (files[0]) setCertFile(files[0])
    },
  })

  const handleSubmit = () => {
    if (!certFile) { setError('공동인증서 파일을 업로드해주세요.'); return }
    if (!password) { setError('인증서 비밀번호를 입력해주세요.'); return }
    onNext(password, certFile)
  }

  return (
    <div className="space-y-5">
      {/* 안내 */}
      <div className="p-4 bg-blue-50 rounded-2xl border border-blue-100">
        <p className="text-xs text-blue-700 font-semibold mb-1">공동인증서 사용 목적</p>
        <ul className="text-xs text-blue-600 space-y-1 list-disc list-inside">
          <li>인터넷등기소 자동 로그인 (등기부등본 발급)</li>
          <li>정부24 자동 로그인 (주민등록초본 발급)</li>
          <li>대법원 전자소송 자동 로그인 (신청서 제출)</li>
        </ul>
        <p className="text-xs text-blue-500 mt-2">
          인증서는 5분간만 메모리에 보관되며 디스크에 저장되지 않습니다.
        </p>
      </div>

      {/* 파일 업로드 */}
      <div>
        <label className="block text-sm font-medium mb-2">공동인증서 파일 (.pfx / .p12)</label>
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-colors ${
            isDragActive
              ? 'border-[#1a1a2e] bg-gray-50'
              : certFile
              ? 'border-green-400 bg-green-50'
              : 'border-gray-200 bg-gray-50'
          }`}
        >
          <input {...getInputProps()} />
          <FileKey className="w-8 h-8 mx-auto mb-2 text-gray-400" />
          {certFile ? (
            <p className="text-sm font-medium text-green-700">{certFile.name}</p>
          ) : (
            <p className="text-sm text-gray-400">파일을 드래그하거나 클릭하여 업로드</p>
          )}
        </div>
      </div>

      {/* 비밀번호 */}
      <div>
        <label className="block text-sm font-medium mb-1">인증서 비밀번호</label>
        <div className="relative">
          <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            className="input-field pl-9 pr-10"
            type={showPassword ? 'text' : 'password'}
            placeholder="인증서 비밀번호"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="off"
          />
          <button
            type="button"
            onClick={() => setShowPassword((v) => !v)}
            className="absolute right-3 top-1/2 -translate-y-1/2"
          >
            {showPassword
              ? <EyeOff className="w-4 h-4 text-gray-400" />
              : <Eye className="w-4 h-4 text-gray-400" />
            }
          </button>
        </div>
      </div>

      {error && <p className="text-xs text-red-500">{error}</p>}

      <button type="button" className="btn-primary" onClick={handleSubmit}>
        다음
      </button>
    </div>
  )
}
