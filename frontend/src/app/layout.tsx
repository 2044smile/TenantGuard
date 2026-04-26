import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

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
    <html lang="ko">
      <body className={inter.className}>
        {/* 무신사 스타일: 모바일은 전체 폭, 데스크톱은 중앙 컨테이너 */}
        <div className="min-h-screen bg-gray-50">
          <div className="mx-auto max-w-screen-sm min-h-screen bg-white shadow-sm">
            {children}
          </div>
        </div>
      </body>
    </html>
  )
}
