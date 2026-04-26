'use client'

import { useState } from 'react'
import { Shield, FileText, Clock, CheckCircle } from 'lucide-react'
import Link from 'next/link'

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen">
      {/* 헤더 */}
      <header className="px-5 pt-12 pb-6">
        <div className="flex items-center gap-2 mb-2">
          <Shield className="w-7 h-7 text-[#e94560]" />
          <span className="text-xl font-bold text-[#1a1a2e]">TenantGuard</span>
        </div>
        <h1 className="text-2xl font-bold text-[#1a1a2e] leading-tight">
          임차권등기명령<br />
          <span className="text-[#e94560]">자동으로</span> 신청하세요
        </h1>
        <p className="mt-2 text-sm text-gray-500">
          전세사기 피해자를 위한 무료 자동화 서비스
        </p>
      </header>

      {/* 안내 카드 */}
      <div className="px-5 space-y-3">
        <div className="card flex items-start gap-3">
          <div className="step-indicator bg-blue-50 text-blue-600">1</div>
          <div>
            <p className="font-semibold text-sm">기본 정보 입력</p>
            <p className="text-xs text-gray-400 mt-0.5">임차인·임대인·계약 정보를 입력합니다</p>
          </div>
        </div>
        <div className="card flex items-start gap-3">
          <div className="step-indicator bg-purple-50 text-purple-600">2</div>
          <div>
            <p className="font-semibold text-sm">서류 자동 수집</p>
            <p className="text-xs text-gray-400 mt-0.5">등기부등본·주민등록초본을 자동으로 발급합니다</p>
          </div>
        </div>
        <div className="card flex items-start gap-3">
          <div className="step-indicator bg-green-50 text-green-600">3</div>
          <div>
            <p className="font-semibold text-sm">전자소송 자동 입력</p>
            <p className="text-xs text-gray-400 mt-0.5">대법원 전자소송 시스템에 자동으로 신청서를 작성합니다</p>
          </div>
        </div>
      </div>

      {/* 비용 안내 */}
      <div className="mx-5 mt-4 p-4 bg-amber-50 rounded-2xl border border-amber-100">
        <p className="text-xs font-semibold text-amber-700 mb-2">신청 비용 (법정 수수료)</p>
        <div className="space-y-1 text-xs text-amber-600">
          <div className="flex justify-between"><span>인지대</span><span>1,800원</span></div>
          <div className="flex justify-between"><span>송달료</span><span>31,200원</span></div>
          <div className="flex justify-between"><span>등록면허세</span><span>7,200원</span></div>
          <div className="flex justify-between"><span>등기촉탁수수료</span><span>3,000원</span></div>
          <div className="flex justify-between font-bold text-amber-800 pt-1 border-t border-amber-200">
            <span>합계</span><span>43,200원</span>
          </div>
        </div>
      </div>

      {/* 시작 버튼 */}
      <div className="px-5 mt-6">
        <Link href="/apply">
          <button className="btn-primary">
            임차권등기명령 신청 시작
          </button>
        </Link>
      </div>

      {/* 하단 안내 */}
      <p className="text-center text-xs text-gray-400 mt-4 pb-8 px-5">
        입력하신 개인정보는 신청 완료 후 즉시 삭제됩니다.<br />
        서비스 이용 중 SSL(HTTPS) 암호화로 보호됩니다.
      </p>
    </div>
  )
}
