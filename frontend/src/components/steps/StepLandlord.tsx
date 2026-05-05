'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { MapPin } from 'lucide-react'
import AddressSearchModal from '@/components/ui/AddressSearchModal'
import type { LandlordInfo, PropertyInfo } from '@/types/application'

const schema = z.object({
  landlord: z.object({
    name: z.string().min(2, '임대인 이름을 입력해주세요.'),
    address: z.string().min(5, '임대인 주소를 입력해주세요.'),
    addressDetail: z.string().optional(),
    phone: z.string().min(1, '연락처를 입력해주세요.'),
    isCorporate: z.boolean(),
    corpNumber: z.string().optional(),
  }),
  property: z.object({
    address: z.string().min(5, '임차 목적물 주소를 입력해주세요.'),
    addressDetail: z.string().optional(),
    sigunguCode: z.string().optional(),
    bdongCode: z.string().optional(),
    bun: z.string().optional(),
    ji: z.string().optional(),
    platGbCd: z.string().optional(),
  }),
})

type FormData = z.infer<typeof schema>

interface Props {
  landlordData?: LandlordInfo
  propertyData?: PropertyInfo
  onNext: (landlord: LandlordInfo, property: PropertyInfo) => void
}

export default function StepLandlord({ landlordData, propertyData, onNext }: Props) {
  const [isCorporate, setIsCorporate] = useState(landlordData?.isCorporate ?? false)

  const { register, handleSubmit, setValue, watch, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      landlord: landlordData ?? { isCorporate: false },
      property: propertyData ?? {},
    },
  })

  const landlordAddress = watch('landlord.address')
  const propertyAddress = watch('property.address')

  const onSubmit = (data: FormData) => {
    onNext(
      { ...data.landlord, isCorporate },
      data.property,
    )
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">

      {/* ── 임대인 섹션 ── */}
      <div>
        <p className="text-xs font-bold uppercase tracking-widest mb-3" style={{ color: 'var(--text-muted)' }}>
          임대인 정보
        </p>
        <div className="space-y-4">
          {/* 개인 / 법인 토글 */}
          <div className="flex gap-2 p-1 rounded-xl" style={{ background: 'var(--surface-3)' }}>
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

          <div>
            <label className="label">{isCorporate ? '법인명' : '임대인 이름'}</label>
            <input
              className="input-field"
              placeholder={isCorporate ? '(주)예시부동산' : '홍길동'}
              {...register('landlord.name')}
            />
            {errors.landlord?.name && <p className="error-text">{errors.landlord.name.message}</p>}
          </div>

          {isCorporate && (
            <div>
              <label className="label">법인등록번호</label>
              <input className="input-field" placeholder="000000-0000000" {...register('landlord.corpNumber')} />
            </div>
          )}

          <div>
            <label className="label">연락처</label>
            <input
              className="input-field"
              placeholder="010-0000-0000"
              type="tel"
              {...register('landlord.phone')}
              onChange={(e) => {
                const digits = e.target.value.replace(/\D/g, '').slice(0, 11)
                const formatted = digits.length > 7
                  ? `${digits.slice(0, 3)}-${digits.slice(3, 7)}-${digits.slice(7)}`
                  : digits.length > 3
                  ? `${digits.slice(0, 3)}-${digits.slice(3)}`
                  : digits
                e.target.value = formatted
                register('landlord.phone').onChange(e)
              }}
            />
            {errors.landlord?.phone && <p className="error-text">{errors.landlord.phone.message}</p>}
          </div>

          <div>
            <label className="label">임대인 주소</label>
            <AddressSearchModal
              onSelect={(address) => setValue('landlord.address', address, { shouldValidate: true })}
              trigger={
                <button
                  type="button"
                  className="input-field w-full text-left flex items-center gap-2"
                  style={{ color: landlordAddress ? 'var(--text)' : 'var(--text-muted)' }}
                >
                  <MapPin className="w-4 h-4 shrink-0" style={{ color: 'var(--primary)' }} />
                  <span className="truncate">{landlordAddress || '주소 검색'}</span>
                </button>
              }
            />
            {errors.landlord?.address && <p className="error-text">{errors.landlord.address.message}</p>}
            <input
              className="input-field mt-2"
              placeholder="동, 호수 (예: 101동 202호)"
              {...register('landlord.addressDetail')}
            />
          </div>
        </div>
      </div>

      {/* 구분선 */}
      <div style={{ borderTop: '1px solid var(--border)' }} />

      {/* ── 임차 목적물 섹션 ── */}
      <div>
        <p className="text-xs font-bold uppercase tracking-widest mb-3" style={{ color: 'var(--text-muted)' }}>
          임차 목적물
        </p>
        <div className="space-y-2">
          <AddressSearchModal
            onSelect={(address, result) => {
              setValue('property.address', address, { shouldValidate: true })
              if (result) {
                setValue('property.sigunguCode', result.sigungu_code)
                setValue('property.bdongCode', result.bdong_code)
                setValue('property.bun', result.bun)
                setValue('property.ji', result.ji)
                setValue('property.platGbCd', result.plat_gb_cd)
              }
            }}
            trigger={
              <button
                type="button"
                className="input-field w-full text-left flex items-center gap-2"
                style={{ color: propertyAddress ? 'var(--text)' : 'var(--text-muted)' }}
              >
                <MapPin className="w-4 h-4 shrink-0" style={{ color: 'var(--primary)' }} />
                <span className="truncate">{propertyAddress || '주소 검색'}</span>
              </button>
            }
          />
          {errors.property?.address && <p className="error-text">{errors.property.address.message}</p>}
          <input
            className="input-field"
            placeholder="동, 호수 (예: 101동 202호)"
            {...register('property.addressDetail')}
          />
        </div>
      </div>

      <div className="pt-2">
        <button type="submit" className="btn-primary">다음</button>
      </div>
    </form>
  )
}
