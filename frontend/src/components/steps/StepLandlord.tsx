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
    <form onSubmit={handleSubmit(onNext)} className="space-y-4">
      {/* 개인 / 법인 선택 */}
      <div className="flex gap-3">
        <button
          type="button"
          onClick={() => setIsCorporate(false)}
          className={`flex-1 py-3 rounded-xl border text-sm font-medium transition-colors ${
            !isCorporate
              ? 'bg-[#1a1a2e] text-white border-[#1a1a2e]'
              : 'bg-white text-gray-500 border-gray-200'
          }`}
        >
          개인 임대인
        </button>
        <button
          type="button"
          onClick={() => setIsCorporate(true)}
          className={`flex-1 py-3 rounded-xl border text-sm font-medium transition-colors ${
            isCorporate
              ? 'bg-[#1a1a2e] text-white border-[#1a1a2e]'
              : 'bg-white text-gray-500 border-gray-200'
          }`}
        >
          법인 임대인
        </button>
      </div>
      <input type="hidden" value={String(isCorporate)} {...register('isCorporate')} />

      <div>
        <label className="block text-sm font-medium mb-1">
          {isCorporate ? '법인명' : '임대인 이름'}
        </label>
        <input
          className="input-field"
          placeholder={isCorporate ? '(주)예시부동산' : '홍길동'}
          {...register('name')}
        />
        {errors.name && <p className="text-xs text-red-500 mt-1">{errors.name.message}</p>}
      </div>

      {isCorporate && (
        <div>
          <label className="block text-sm font-medium mb-1">법인등록번호</label>
          <input
            className="input-field"
            placeholder="000000-0000000"
            {...register('corpNumber')}
          />
        </div>
      )}

      <div>
        <label className="block text-sm font-medium mb-1">임대인 주소</label>
        <input
          className="input-field"
          placeholder="서울특별시 강남구 테헤란로 123"
          {...register('address')}
        />
        {errors.address && <p className="text-xs text-red-500 mt-1">{errors.address.message}</p>}
      </div>

      <div className="pt-4">
        <button type="submit" className="btn-primary">다음</button>
      </div>
    </form>
  )
}
