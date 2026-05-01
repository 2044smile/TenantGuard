'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { MapPin } from 'lucide-react'
import AddressSearchModal from '@/components/ui/AddressSearchModal'
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
  const selectedAddress = watch('address')

  return (
    <form onSubmit={handleSubmit(onNext)} className="space-y-5">
      <div>
        <label className="label">임차 목적물 주소</label>
        <AddressSearchModal
          onSelect={(address) => setValue('address', address, { shouldValidate: true })}
          trigger={
            <button
              type="button"
              className="input-field w-full text-left flex items-center gap-2"
              style={{ color: selectedAddress ? 'var(--text)' : 'var(--text-muted)' }}
            >
              <MapPin className="w-4 h-4 shrink-0" style={{ color: 'var(--primary)' }} />
              <span className="truncate">
                {selectedAddress || '주소 검색'}
              </span>
            </button>
          }
        />
        {errors.address && <p className="error-text">{errors.address.message}</p>}
      </div>

      <div>
        <label className="label">건물 유형</label>
        <div className="flex flex-wrap gap-2">
          {PROPERTY_TYPES.map((type) => {
            const active = selectedType === type
            return (
              <button
                key={type}
                type="button"
                onClick={() => setValue('propertyType', type)}
                className="px-3.5 py-2 rounded-lg text-sm font-medium transition-all"
                style={{
                  background: active ? 'var(--primary)' : 'var(--surface-3)',
                  color: active ? '#fff' : 'var(--text-secondary)',
                  border: `1px solid ${active ? 'var(--primary)' : 'var(--border)'}`,
                  boxShadow: active ? '0 2px 8px rgba(99,102,241,0.25)' : 'none',
                }}
              >
                {type}
              </button>
            )
          })}
        </div>
      </div>

      <div className="flex gap-3">
        <div className="flex-1">
          <label className="label">전용면적 (㎡)</label>
          <input className="input-field" placeholder="59.94" type="number" step="0.01" {...register('area')} />
        </div>
        <div className="flex-1">
          <label className="label">층</label>
          <input className="input-field" placeholder="5층" {...register('floor')} />
        </div>
      </div>

      <div className="pt-2">
        <button type="submit" className="btn-primary">다음</button>
      </div>
    </form>
  )
}
