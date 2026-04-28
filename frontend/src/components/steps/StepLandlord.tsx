'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useState } from 'react'
import type { LandlordInfo } from '@/types/application'

const schema = z.object({
  name: z.string().min(2, '임대인 이름을 입력해주세요.'),
  address: z.string().min(5, '임대인 주소를 입력해주세요.'),
  isCorporate: z.boolean(),
  corpNumber: z.string().optional(),
})

interface Props {
  data?: LandlordInfo
  onNext: (data: LandlordInfo) => void
}

export default function StepLandlord({ data, onNext }: Props) {
  const [isCorporate, setIsCorporate] = useState(data?.isCorporate ?? false)

  const { register, handleSubmit, formState: { errors } } = useForm<LandlordInfo>({
    resolver: zodResolver(schema),
    defaultValues: data ?? { isCorporate: false },
  })

  return (
    <form onSubmit={handleSubmit(onNext)} className="space-y-5">
      {/* 개인 / 법인 토글 */}
      <div
        className="flex gap-2 p-1 rounded-xl"
        style={{ background: 'var(--surface-3)' }}
      >
        {['개인 임대인', '법인 임대인'].map((label, i) => {
          const active = isCorporate === (i === 1)
          return (
            <button
              key={label}
              type="button"
              onClick={() => setIsCorporate(i === 1)}
              className="flex-1 py-2.5 rounded-lg text-sm font-semibold transition-all"
              style={{
                background: active ? 'var(--primary)' : 'transparent',
                color: active ? '#fff' : 'var(--text-secondary)',
                boxShadow: active ? '0 2px 8px rgba(99,102,241,0.3)' : 'none',
              }}
            >
              {label}
            </button>
          )
        })}
      </div>
      <input type="hidden" value={String(isCorporate)} {...register('isCorporate')} />

      <div>
        <label className="label">{isCorporate ? '법인명' : '임대인 이름'}</label>
        <input
          className="input-field"
          placeholder={isCorporate ? '(주)예시부동산' : '홍길동'}
          {...register('name')}
        />
        {errors.name && <p className="error-text">{errors.name.message}</p>}
      </div>

      {isCorporate && (
        <div>
          <label className="label">법인등록번호</label>
          <input className="input-field" placeholder="000000-0000000" {...register('corpNumber')} />
        </div>
      )}

      <div>
        <label className="label">임대인 주소</label>
        <input
          className="input-field"
          placeholder="서울특별시 강남구 테헤란로 123"
          {...register('address')}
        />
        {errors.address && <p className="error-text">{errors.address.message}</p>}
      </div>

      <div className="pt-2">
        <button type="submit" className="btn-primary">다음</button>
      </div>
    </form>
  )
}
