'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import type { PropertyInfo } from '@/types/application'

const schema = z.object({
  address: z.string().min(5, '부동산 주소를 입력해주세요.'),
  area: z.string().optional(),
  floor: z.string().optional(),
  propertyType: z.string().optional(),
})

const PROPERTY_TYPES = ['아파트', '빌라', '주택', '오피스텔', '상가주택', '기타']

interface Props {
  data?: PropertyInfo
  onNext: (data: PropertyInfo) => void
}

export default function StepProperty({ data, onNext }: Props) {
  const { register, handleSubmit, setValue, watch, formState: { errors } } = useForm<PropertyInfo>({
    resolver: zodResolver(schema),
    defaultValues: data,
  })
  const selectedType = watch('propertyType')

  return (
    <form onSubmit={handleSubmit(onNext)} className="space-y-4">
      <div>
        <label className="block text-sm font-medium mb-1">임차 목적물 주소</label>
        <input
          className="input-field"
          placeholder="서울특별시 서초구 반포대로 201"
          {...register('address')}
        />
        {errors.address && <p className="text-xs text-red-500 mt-1">{errors.address.message}</p>}
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">건물 유형</label>
        <div className="flex flex-wrap gap-2">
          {PROPERTY_TYPES.map((type) => (
            <button
              key={type}
              type="button"
              onClick={() => setValue('propertyType', type)}
              className={`px-3 py-2 rounded-lg border text-sm transition-colors ${
                selectedType === type
                  ? 'bg-[#1a1a2e] text-white border-[#1a1a2e]'
                  : 'bg-white text-gray-600 border-gray-200'
              }`}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      <div className="flex gap-3">
        <div className="flex-1">
          <label className="block text-sm font-medium mb-1">전용면적 (㎡)</label>
          <input
            className="input-field"
            placeholder="59.94"
            type="number"
            step="0.01"
            {...register('area')}
          />
        </div>
        <div className="flex-1">
          <label className="block text-sm font-medium mb-1">층</label>
          <input
            className="input-field"
            placeholder="5층"
            {...register('floor')}
          />
        </div>
      </div>

      <div className="pt-4">
        <button type="submit" className="btn-primary">다음</button>
      </div>
    </form>
  )
}
