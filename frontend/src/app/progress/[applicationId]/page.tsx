'use client'

import { useEffect, useState } from 'react'
import { useParams, useSearchParams, useRouter } from 'next/navigation'
import { connectProgressSocket } from '@/lib/api'
import type { ProgressUpdate } from '@/types/application'
import { DOCUMENT_LABELS } from '@/types/application'
import ProgressBar from '@/components/ui/ProgressBar'
import { CheckCircle, XCircle, Loader2, Shield } from 'lucide-react'

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

  return (
    <div className="flex flex-col min-h-screen px-5 pt-12">
      <div className="flex items-center gap-2 mb-8">
        <Shield className="w-6 h-6 text-[#e94560]" />
        <span className="font-bold text-lg">서류 자동 수집</span>
      </div>

      {/* 진행률 */}
      <div className="card mb-6">
        <div className="flex justify-between items-center mb-3">
          <span className="text-sm font-semibold">
            {progress ? STATUS_MESSAGES[progress.status] || progress.message : '처리 준비 중...'}
          </span>
          <span className="text-sm font-bold text-[#1a1a2e]">
            {progress?.progress ?? 0}%
          </span>
        </div>
        <ProgressBar value={progress?.progress ?? 0} animated />
      </div>

      {/* 서류 수집 현황 */}
      <div className="space-y-3">
        {progress?.completedDocs.map((doc) => (
          <div key={doc} className="flex items-center gap-3 p-3 bg-green-50 rounded-xl">
            <CheckCircle className="w-5 h-5 text-green-500 shrink-0" />
            <span className="text-sm font-medium text-green-700">
              {DOCUMENT_LABELS[doc] || doc}
            </span>
          </div>
        ))}

        {progress?.status === 'collecting' && (
          <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-xl">
            <Loader2 className="w-5 h-5 text-blue-500 animate-spin shrink-0" />
            <span className="text-sm font-medium text-blue-700">
              {progress.currentStep || '수집 중...'}
            </span>
          </div>
        )}

        {progress?.failedDocs.map((doc) => (
          <div key={doc} className="flex items-center gap-3 p-3 bg-red-50 rounded-xl">
            <XCircle className="w-5 h-5 text-red-500 shrink-0" />
            <span className="text-sm font-medium text-red-700">
              {DOCUMENT_LABELS[doc] || doc} — 수집 실패
            </span>
          </div>
        ))}
      </div>

      {/* 미리보기 이동 버튼 */}
      {progress?.status === 'preview' && (
        <div className="mt-8">
          <button className="btn-primary" onClick={handleGoToPreview}>
            신청서 확인하기
          </button>
        </div>
      )}

      {/* 실패 메시지 */}
      {progress?.status === 'failed' && (
        <div className="mt-6 p-4 bg-red-50 rounded-2xl border border-red-100">
          <p className="text-sm text-red-600">{progress.message}</p>
          <button
            className="mt-3 text-sm font-semibold text-red-700 underline"
            onClick={() => router.push('/apply')}
          >
            처음부터 다시 시도
          </button>
        </div>
      )}
    </div>
  )
}
