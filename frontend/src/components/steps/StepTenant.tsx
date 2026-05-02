'use client'

import { useState, useRef } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { MapPin } from 'lucide-react'
import AddressSearchModal from '@/components/ui/AddressSearchModal'
import type { TenantInfo } from '@/types/application'

const schema = z.object({
  name: z.string().min(2, '이름을 입력해주세요.'),
  residentNumber: z
    .string()
    .regex(/^\d{6}-?\d{7}$/, '주민등록번호 형식이 올바르지 않습니다.'),
  address: z.string().min(5, '주소를 입력해주세요.'),
  addressDetail: z.string().optional(),
  phone: z.string().min(1, '연락처를 입력해주세요.'),
})

interface Props {
  data?: TenantInfo
  onNext: (data: TenantInfo) => void
}

export default function StepTenant({ data, onNext }: Props) {
  const { register, handleSubmit, control, setValue, watch, formState: { errors } } = useForm<TenantInfo>({
    resolver: zodResolver(schema),
    defaultValues: data,
  })

  const selectedAddress = watch('address')
  const backRef = useRef<HTMLInputElement>(null)

  return (
    <form onSubmit={handleSubmit(onNext)} className="space-y-5">
      <div>
        <label className="label">이름</label>
        <input className="input-field" placeholder="홍길동" {...register('name')} />
        {errors.name && <p className="error-text">{errors.name.message}</p>}
      </div>

      <div>
        <label className="label">주민등록번호</label>
        <Controller
          name="residentNumber"
          control={control}
          render={({ field: { value, onChange } }) => {
            const front = (value ?? '').replace('-', '').slice(0, 6)
            const back = (value ?? '').replace('-', '').slice(6)

            const handleFront = (e: React.ChangeEvent<HTMLInputElement>) => {
              const digits = e.target.value.replace(/\D/g, '').slice(0, 6)
              onChange(digits.length === 6 ? `${digits}-${back}` : digits)
              if (digits.length === 6) backRef.current?.focus()
            }

            const handleBack = (e: React.ChangeEvent<HTMLInputElement>) => {
              const digits = e.target.value.replace(/\D/g, '').slice(0, 7)
              onChange(`${front}-${digits}`)
            }

            return (
              <div
                className="input-field flex items-center gap-2 px-4"
                style={{ display: 'flex' }}
              >
                <input
                  type="text"
                  inputMode="numeric"
                  placeholder="000000"
                  autoComplete="off"
                  value={front}
                  onChange={handleFront}
                  maxLength={6}
                  className="flex-1 bg-transparent outline-none text-center tracking-widest"
                  style={{ color: 'var(--text)', minWidth: 0 }}
                />
                <span style={{ color: 'var(--text-muted)' }}>-</span>
                <input
                  ref={backRef}
                  type="password"
                  inputMode="numeric"
                  placeholder="0000000"
                  autoComplete="off"
                  value={back}
                  onChange={handleBack}
                  maxLength={7}
                  className="flex-1 bg-transparent outline-none text-center tracking-widest"
                  style={{ color: 'var(--text)', minWidth: 0 }}
                />
              </div>
            )
          }}
        />
        {errors.residentNumber && <p className="error-text">{errors.residentNumber.message}</p>}
        <p className="hint-text">주민등록초본 자동 발급에만 사용되며 저장되지 않습니다.</p>
      </div>

      <div>
        <label className="label">주소 (전입 주소)</label>
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
        <input
          className="input-field mt-2"
          placeholder="동, 호수 (예: 101동 202호)"
          {...register('addressDetail')}
        />
      </div>

      <div>
        <label className="label">연락처</label>
        <input
          className="input-field"
          placeholder="010-0000-0000"
          type="tel"
          {...register('phone')}
          onChange={(e) => {
            const digits = e.target.value.replace(/\D/g, '').slice(0, 11)
            const formatted = digits.length > 7
              ? `${digits.slice(0, 3)}-${digits.slice(3, 7)}-${digits.slice(7)}`
              : digits.length > 3
              ? `${digits.slice(0, 3)}-${digits.slice(3)}`
              : digits
            e.target.value = formatted
            register('phone').onChange(e)
          }}
        />
        {errors.phone && <p className="error-text">{errors.phone.message}</p>}
      </div>

      <div className="pt-2">
        <button type="submit" className="btn-primary">다음</button>
      </div>
    </form>
  )
}
