'use client'

import { useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Lock, FileKey, Eye, EyeOff, CheckCircle } from 'lucide-react'

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
      <div
        className="p-4 rounded-2xl"
        style={{ background: 'var(--info-bg)', border: '1px solid rgba(59,130,246,0.2)' }}
      >
        <p className="text-xs font-bold uppercase tracking-wide mb-2" style={{ color: 'var(--info)' }}>
          공동인증서 사용 목적
        </p>
        <ul className="text-xs space-y-1.5 list-disc list-inside" style={{ color: 'rgba(59,130,246,0.85)' }}>
          <li>인터넷등기소 자동 로그인 (등기부등본 발급)</li>
          <li>정부24 자동 로그인 (주민등록초본 발급)</li>
          <li>대법원 전자소송 자동 로그인 (신청서 제출)</li>
        </ul>
        <p className="text-xs mt-2" style={{ color: 'var(--text-muted)' }}>
          인증서는 5분간만 메모리에 보관되며 디스크에 저장되지 않습니다.
        </p>
      </div>

      {/* 파일 업로드 */}
      <div>
        <label className="label">공동인증서 파일 (.pfx / .p12)</label>
        <div
          {...getRootProps()}
          className="border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all"
          style={{
            borderColor: isDragActive
              ? 'var(--primary)'
              : certFile
              ? 'var(--success)'
              : 'var(--border)',
            background: isDragActive
              ? 'rgba(99,102,241,0.06)'
              : certFile
              ? 'var(--success-bg)'
              : 'var(--surface-2)',
          }}
        >
          <input {...getInputProps()} />
          {certFile ? (
            <div className="flex items-center justify-center gap-2">
              <CheckCircle className="w-5 h-5" style={{ color: 'var(--success)' }} />
              <span className="text-sm font-medium" style={{ color: 'var(--success)' }}>
                {certFile.name}
              </span>
            </div>
          ) : (
            <>
              <FileKey className="w-8 h-8 mx-auto mb-2" style={{ color: 'var(--text-muted)' }} />
              <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                파일을 드래그하거나 클릭하여 업로드
              </p>
            </>
          )}
        </div>
      </div>

      {/* 비밀번호 */}
      <div>
        <label className="label">인증서 비밀번호</label>
        <div className="relative">
          <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: 'var(--text-muted)' }} />
          <input
            className="input-field pl-10 pr-11"
            type={showPassword ? 'text' : 'password'}
            placeholder="인증서 비밀번호"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="off"
          />
          <button
            type="button"
            onClick={() => setShowPassword((v) => !v)}
            className="absolute right-3.5 top-1/2 -translate-y-1/2"
            style={{ color: 'var(--text-muted)' }}
          >
            {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {error && <p className="error-text">{error}</p>}

      <div className="pt-2">
        <button type="button" className="btn-primary" onClick={handleSubmit}>
          다음
        </button>
      </div>
    </div>
  )
}
