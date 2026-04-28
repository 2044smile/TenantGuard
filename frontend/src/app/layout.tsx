import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
})

export const metadata: Metadata = {
  title: 'TenantGuard — 임차권등기명령 자동화',
  description: '전세사기 피해자를 위한 임차권등기명령 신청 자동화 서비스',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko" className="dark">
      <body className={`${inter.variable} font-sans bg-bg text-text`}>
        {/* 반응형: 모바일 full-width, 데스크톱 중앙 카드 */}
        <div className="min-h-screen bg-bg">
          {/* 배경 그라디언트 장식 */}
          <div
            className="fixed inset-0 pointer-events-none"
            aria-hidden="true"
            style={{
              background:
                'radial-gradient(ellipse 80% 50% at 50% -10%, rgba(99,102,241,0.12) 0%, transparent 60%)',
            }}
          />
          <div className="relative mx-auto max-w-md min-h-screen flex flex-col">
            {children}
          </div>
        </div>
      </body>
    </html>
  )
}
