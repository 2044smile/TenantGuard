'use client'

import { useEffect, useState } from 'react'
import { useParams, useSearchParams, useRouter } from 'next/navigation'
import { connectProgressSocket } from '@/lib/api'
import type { ProgressUpdate } from '@/types/application'
import { DOCUMENT_LABELS } from '@/types/application'
import ProgressBar from '@/components/ui/ProgressBar'
import { CheckCircle, XCircle, Loader2, Shield, ArrowRight, RefreshCw } from 'lucide-react'

const STATUS_MESSAGES: Record<string, string> = {
  collecting: '서류를 자동 수집하고 있습니다...',
  analyzing: 'AI가 서류를 분석하고 있습니다...',
  ready: '모든 서류 준비 완료!',
  filling: '전자소송 시스템에 신청서를 작성하고 있습니다...',
  preview: '신청서 작성 완료. 최종 확인이 필요합니다.',
  submitted: '임차권등기명령 신청이 완료되었습니다.',
  failed: '오류가 발생했습니다.',
}

export default function ProgressPage() {
  const { applicationId } = useParams<{ applicationId: string }>()
  const searchParams = useSearchParams()
  const sessionId = searchParams.get('sessionId') || ''
  const router = useRouter()

  const [progress, setProgress] = useState<ProgressUpdate | null>(null)

  useEffect(() => {
    const ws = connectProgressSocket(
      applicationId,
      (data) => setProgress(data),
      () => console.log('WebSocket 연결 종료'),
    )
    return () => ws.close()
  }, [applicationId])

  const handleGoToPreview = () => {
    router.push(`/preview/${applicationId}?sessionId=${sessionId}`)
  }

  const pct = progress?.progress ?? 0
  const status = progress?.status

  return (
    <div className="flex flex-col min-h-screen px-5 pt-12 pb-10 animate-fade-in">
      {/* 헤더 */}
      <div className="flex items-center gap-3 mb-8">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center"
          style={{ background: 'rgba(99,102,241,0.12)' }}
        >
          <Shield className="w-5 h-5" style={{ color: 'var(--primary)' }} />
        </div>
        <div>
          <p className="text-[10px] font-bold uppercase tracking-widest" style={{ color: 'var(--text-muted)' }}>
            자동 처리 중
          </p>
          <h2 className="font-bold text-base" style={{ color: 'var(--text)' }}>
            서류 자동 수집
          </h2>
        </div>
      </div>

      {/* 진행률 카드 */}
      <div
        className="rounded-2xl p-5 mb-5"
        style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}
      >
        <div className="flex justify-between items-end mb-3">
          <p className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>
            {progress ? STATUS_MESSAGES[progress.status] || progress.message : '처리 준비 중...'}
          </p>
          <span
            className="text-2xl font-bold tabular-nums"
            style={{ color: 'var(--primary)' }}
          >
            {pct}%
          </span>
        </div>
        <ProgressBar value={pct} animated={status === 'collecting' || status === 'analyzing'} />
      </div>

      {/* 서류 현황 */}
      <div className="space-y-2">
        {(progress?.completedDocs ?? []).map((doc) => (
          <div key={doc} className="badge-success">
            <CheckCircle className="w-4 h-4 shrink-0" />
            <span>{DOCUMENT_LABELS[doc] || doc}</span>
          </div>
        ))}

        {(status === 'collecting' || status === 'analyzing') && (
          <div className="badge-info">
            <Loader2 className="w-4 h-4 shrink-0 animate-spin" />
            <span>{progress?.currentStep || '수집 중...'}</span>
          </div>
        )}

        {(progress?.failedDocs ?? []).map((doc) => (
          <div key={doc} className="badge-error">
            <XCircle className="w-4 h-4 shrink-0" />
            <span>{DOCUMENT_LABELS[doc] || doc} — 수집 실패</span>
          </div>
        ))}
      </div>

      {/* 완료 → 미리보기 버튼 */}
      {status === 'preview' && (
        <div className="mt-8">
          <button className="btn-primary flex items-center justify-center gap-2" onClick={handleGoToPreview}>
            신청서 확인하기
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* 실패 */}
      {status === 'failed' && (
        <div
          className="mt-6 p-4 rounded-2xl"
          style={{ background: 'var(--error-bg)', border: '1px solid rgba(239,68,68,0.2)' }}
        >
          <p className="text-sm mb-3" style={{ color: 'var(--error)' }}>
            {progress?.message}
          </p>
          <button
            className="flex items-center gap-1.5 text-sm font-semibold"
            style={{ color: 'var(--error)' }}
            onClick={() => router.push('/apply')}
          >
            <RefreshCw className="w-3.5 h-3.5" />
            처음부터 다시 시도
          </button>
        </div>
      )}
    </div>
  )
}
