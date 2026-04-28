'use client'

import { Shield, FileSearch, Cpu, ArrowRight, Lock } from 'lucide-react'
import Link from 'next/link'

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen px-5 animate-fade-in">
      {/* 헤더 */}
      <header className="pt-14 pb-8">
        <div className="flex items-center gap-2.5 mb-6">
          <div
            className="w-9 h-9 rounded-xl flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}
          >
            <Shield className="w-5 h-5 text-white" />
          </div>
          <span className="text-base font-bold tracking-tight" style={{ color: 'var(--text)' }}>
            TenantGuard
          </span>
        </div>

        <h1 className="text-[2rem] font-bold leading-[1.2] tracking-tight mb-3" style={{ color: 'var(--text)' }}>
          임차권등기명령<br />
          <span style={{ color: 'var(--primary)' }}>자동으로</span> 신청하세요
        </h1>
        <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
          전세사기 피해자를 위한 무료 자동화 서비스
        </p>
      </header>

      {/* 단계 카드 */}
      <div className="space-y-3 mb-6">
        {[
          {
            icon: FileSearch,
            num: '01',
            title: '기본 정보 입력',
            desc: '임차인·임대인·계약 정보를 입력합니다',
            color: 'var(--primary)',
            bg: 'rgba(99,102,241,0.12)',
          },
          {
            icon: Cpu,
            num: '02',
            title: '서류 자동 수집',
            desc: '등기부등본·주민등록초본을 자동으로 발급합니다',
            color: '#a855f7',
            bg: 'rgba(168,85,247,0.12)',
          },
          {
            icon: Shield,
            num: '03',
            title: '전자소송 자동 입력',
            desc: '대법원 전자소송 시스템에 신청서를 자동 작성합니다',
            color: '#22c55e',
            bg: 'rgba(34,197,94,0.12)',
          },
        ].map(({ icon: Icon, num, title, desc, color, bg }) => (
          <div key={num} className="card flex items-start gap-4" style={{ background: 'var(--surface)' }}>
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
              style={{ background: bg }}
            >
              <Icon className="w-5 h-5" style={{ color }} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-0.5">
                <span className="text-[10px] font-bold tracking-widest" style={{ color: 'var(--text-muted)' }}>
                  {num}
                </span>
                <p className="text-sm font-semibold" style={{ color: 'var(--text)' }}>{title}</p>
              </div>
              <p className="text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{desc}</p>
            </div>
          </div>
        ))}
      </div>

      {/* 비용 안내 */}
      <div
        className="rounded-2xl p-4 mb-6"
        style={{
          background: 'var(--surface-2)',
          border: '1px solid var(--border)',
        }}
      >
        <p
          className="text-xs font-bold uppercase tracking-widest mb-3"
          style={{ color: 'var(--warning)' }}
        >
          신청 비용 (법정 수수료)
        </p>
        <div className="space-y-2">
          {[
            ['인지대', '1,800원'],
            ['송달료', '31,200원'],
            ['등록면허세', '7,200원'],
            ['등기촉탁수수료', '3,000원'],
          ].map(([label, amount]) => (
            <div key={label} className="flex justify-between text-xs" style={{ color: 'var(--text-secondary)' }}>
              <span>{label}</span>
              <span>{amount}</span>
            </div>
          ))}
          <div
            className="flex justify-between text-sm font-bold pt-2 mt-1"
            style={{
              color: 'var(--text)',
              borderTop: '1px solid var(--border)',
            }}
          >
            <span>합계</span>
            <span style={{ color: 'var(--warning)' }}>43,200원</span>
          </div>
        </div>
      </div>

      {/* CTA */}
      <div className="mb-4">
        <Link href="/apply">
          <button className="btn-primary flex items-center justify-center gap-2">
            임차권등기명령 신청 시작
            <ArrowRight className="w-4 h-4" />
          </button>
        </Link>
      </div>

      {/* 보안 안내 */}
      <div className="flex items-center justify-center gap-1.5 pb-10">
        <Lock className="w-3 h-3" style={{ color: 'var(--text-muted)' }} />
        <p className="text-[11px] text-center" style={{ color: 'var(--text-muted)' }}>
          개인정보는 신청 완료 후 즉시 삭제 · SSL 암호화 보호
        </p>
      </div>
    </div>
  )
}
