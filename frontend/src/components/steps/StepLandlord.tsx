'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { MapPin, ChevronDown, ChevronUp } from 'lucide-react'
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
  agent: z.object({
    name: z.string().min(2, '대리인 이름을 입력해주세요.'),
    address: z.string().min(5, '대리인 주소를 입력해주세요.'),
    addressDetail: z.string().optional(),
    phone: z.string().min(1, '대리인 연락처를 입력해주세요.'),
  }).optional(),
})

type FormData = z.infer<typeof schema>

interface Props {
  landlordData?: LandlordInfo
  propertyData?: PropertyInfo
  onNext: (landlord: LandlordInfo, property: PropertyInfo) => void
}

export default function StepLandlord({ landlordData, propertyData, onNext }: Props) {
  const [isCorporate, setIsCorporate] = useState(landlordData?.isCorporate ?? false)
  const [hasAgent, setHasAgent] = useState(!!landlordData?.agent)

  const { register, handleSubmit, setValue, watch, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      landlord: landlordData ?? { isCorporate: false },
      property: propertyData ?? {},
    },
  })

  const landlordAddress = watch('landlord.address')
  const propertyAddress = watch('property.address')
  const agentAddress = watch('agent.address')

  const onSubmit = (data: FormData) => {
    onNext(
      { ...data.landlord, isCorporate, agent: hasAgent ? data.agent : undefined },
      data.property,
    )
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">

      {/* ── 임차 목적물 섹션 ── */}
      <div>
        <p className="text-xs font-bold uppercase tracking-widest mb-1" style={{ color: 'var(--text-muted)' }}>
          임차 목적물
        </p>
        <p className="text-xs mb-3 leading-relaxed" style={{ color: 'var(--text-muted)' }}>
          임차권등기를 설정할 부동산 주소입니다. 전입신고한 주소와 동일해야 합니다.
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

      {/* 구분선 */}
      <div style={{ borderTop: '1px solid var(--border)' }} />

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

      {/* ── 대리인 섹션 ── */}
      <div>
        <button
          type="button"
          onClick={() => setHasAgent((v) => !v)}
          className="w-full flex items-center justify-between px-4 py-3 rounded-xl transition-colors"
          style={{
            background: hasAgent ? 'rgba(99,102,241,0.08)' : 'var(--surface-2)',
            border: `1px solid ${hasAgent ? 'var(--primary)' : 'var(--border)'}`,
          }}
        >
          <div className="text-left">
            <p className="text-sm font-semibold" style={{ color: hasAgent ? 'var(--primary)' : 'var(--text)' }}>
              임대인 대리인 있음
            </p>
            <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
              부동산 중개인, 법인 대표 등 대리인이 계약한 경우
            </p>
          </div>
          {hasAgent
            ? <ChevronUp className="w-4 h-4 shrink-0" style={{ color: 'var(--primary)' }} />
            : <ChevronDown className="w-4 h-4 shrink-0" style={{ color: 'var(--text-muted)' }} />
          }
        </button>

        {hasAgent && (
          <div className="mt-4 space-y-4">
            <div>
              <label className="label">대리인 이름</label>
              <input
                className="input-field"
                placeholder="홍길동"
                {...register('agent.name')}
              />
              {errors.agent?.name && <p className="error-text">{errors.agent.name.message}</p>}
            </div>

            <div>
              <label className="label">대리인 연락처</label>
              <input
                className="input-field"
                placeholder="010-0000-0000"
                type="tel"
                {...register('agent.phone')}
                onChange={(e) => {
                  const digits = e.target.value.replace(/\D/g, '').slice(0, 11)
                  const formatted = digits.length > 7
                    ? `${digits.slice(0, 3)}-${digits.slice(3, 7)}-${digits.slice(7)}`
                    : digits.length > 3
                    ? `${digits.slice(0, 3)}-${digits.slice(3)}`
                    : digits
                  e.target.value = formatted
                  register('agent.phone').onChange(e)
                }}
              />
              {errors.agent?.phone && <p className="error-text">{errors.agent.phone.message}</p>}
            </div>

            <div>
              <label className="label">대리인 주소</label>
              <AddressSearchModal
                onSelect={(address) => setValue('agent.address', address, { shouldValidate: true })}
                trigger={
                  <button
                    type="button"
                    className="input-field w-full text-left flex items-center gap-2"
                    style={{ color: agentAddress ? 'var(--text)' : 'var(--text-muted)' }}
                  >
                    <MapPin className="w-4 h-4 shrink-0" style={{ color: 'var(--primary)' }} />
                    <span className="truncate">{agentAddress || '주소 검색'}</span>
                  </button>
                }
              />
              {errors.agent?.address && <p className="error-text">{errors.agent.address.message}</p>}
              <input
                className="input-field mt-2"
                placeholder="동, 호수 (예: 101동 202호)"
                {...register('agent.addressDetail')}
              />
            </div>
          </div>
        )}
      </div>

      <div className="pt-2">
        <button type="submit" className="btn-primary">다음</button>
      </div>
    </form>
  )
}
