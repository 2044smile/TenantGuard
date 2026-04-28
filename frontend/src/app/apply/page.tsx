'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import StepTenant from '@/components/steps/StepTenant'
import StepLandlord from '@/components/steps/StepLandlord'
import StepProperty from '@/components/steps/StepProperty'
import StepContract from '@/components/steps/StepContract'
import StepCertificate from '@/components/steps/StepCertificate'
import StepDocuments from '@/components/steps/StepDocuments'
import ProgressBar from '@/components/ui/ProgressBar'
import { createApplication } from '@/lib/api'
import type { ApplicationFormData } from '@/types/application'
import { ArrowLeft, Shield } from 'lucide-react'

const STEPS = [
  { id: 1, label: '임차인' },
  { id: 2, label: '임대인' },
  { id: 3, label: '부동산' },
  { id: 4, label: '계약' },
  { id: 5, label: '인증서' },
  { id: 6, label: '서류' },
]

export default function ApplyPage() {
  const router = useRouter()
  const [step, setStep] = useState(1)
  const [formData, setFormData] = useState<Partial<ApplicationFormData>>({})
  const [certFile, setCertFile] = useState<File | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const updateFormData = (partial: Partial<ApplicationFormData>) => {
    setFormData((prev) => ({ ...prev, ...partial }))
  }

  const handleNext = () => setStep((s) => Math.min(s + 1, STEPS.length))
  const handleBack = () => {
    if (step === 1) router.push('/')
    else setStep((s) => s - 1)
  }

  const handleStart = async (certPassword: string, file: File) => {
    if (!formData.tenant || !formData.landlord || !formData.property || !formData.contract) {
      setError('모든 정보를 입력해주세요.')
      return
    }

    setIsSubmitting(true)
    setError(null)

    try {
      const fullData: ApplicationFormData = {
        ...formData as ApplicationFormData,
        certPassword,
      }

      const result = await createApplication(fullData, file)
      router.push(`/progress/${result.applicationId}?sessionId=${result.sessionId}`)
    } catch (e: any) {
      setError(e.response?.data?.detail || '오류가 발생했습니다. 다시 시도해주세요.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex flex-col min-h-screen animate-fade-in">
      {/* 헤더 */}
      <header
        className="flex items-center gap-3 px-5 pt-12 pb-5"
        style={{ borderBottom: '1px solid var(--border)' }}
      >
        <button
          onClick={handleBack}
          className="w-9 h-9 rounded-xl flex items-center justify-center transition-colors"
          style={{ background: 'var(--surface-2)', color: 'var(--text-secondary)' }}
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div className="flex-1">
          <p className="text-[10px] font-bold uppercase tracking-widest" style={{ color: 'var(--text-muted)' }}>
            STEP {step} / {STEPS.length}
          </p>
          <h2 className="font-bold text-base" style={{ color: 'var(--text)' }}>
            {STEPS[step - 1].label} 정보
          </h2>
        </div>
        <div
          className="w-9 h-9 rounded-xl flex items-center justify-center"
          style={{ background: 'rgba(99,102,241,0.12)' }}
        >
          <Shield className="w-4 h-4" style={{ color: 'var(--primary)' }} />
        </div>
      </header>

      {/* 진행 바 + 스텝 라벨 */}
      <div className="px-5 pt-5 pb-2">
        <ProgressBar value={(step / STEPS.length) * 100} />
        <div className="flex justify-between mt-2.5">
          {STEPS.map((s) => (
            <span
              key={s.id}
              className="text-[9px] font-semibold transition-colors"
              style={{ color: step >= s.id ? 'var(--primary)' : 'var(--text-muted)' }}
            >
              {s.label}
            </span>
          ))}
        </div>
      </div>

      {/* 에러 */}
      {error && (
        <div
          className="mx-5 mt-4 p-3 rounded-xl text-sm"
          style={{
            background: 'var(--error-bg)',
            border: '1px solid rgba(239,68,68,0.2)',
            color: 'var(--error)',
          }}
        >
          {error}
        </div>
      )}

      {/* 스텝 컨텐츠 */}
      <div className="flex-1 px-5 pt-6 pb-8">
        {step === 1 && (
          <StepTenant
            data={formData.tenant}
            onNext={(tenant) => { updateFormData({ tenant }); handleNext() }}
          />
        )}
        {step === 2 && (
          <StepLandlord
            data={formData.landlord}
            onNext={(landlord) => { updateFormData({ landlord }); handleNext() }}
          />
        )}
        {step === 3 && (
          <StepProperty
            data={formData.property}
            onNext={(property) => { updateFormData({ property }); handleNext() }}
          />
        )}
        {step === 4 && (
          <StepContract
            data={formData.contract}
            onNext={(contract) => { updateFormData({ contract }); handleNext() }}
          />
        )}
        {step === 5 && (
          <StepCertificate
            onNext={(certPassword, file) => {
              setCertFile(file)
              updateFormData({ certPassword })
              handleNext()
            }}
          />
        )}
        {step === 6 && (
          <StepDocuments
            applicationId={undefined}
            onStart={(certPassword, file) => handleStart(certPassword, file)}
            isSubmitting={isSubmitting}
          />
        )}
      </div>
    </div>
  )
}
