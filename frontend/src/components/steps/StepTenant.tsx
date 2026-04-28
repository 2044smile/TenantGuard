'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import type { TenantInfo } from '@/types/application'

const schema = z.object({
  name: z.string().min(2, '이름을 입력해주세요.'),
  residentNumber: z
    .string()
    .regex(/^\d{6}-?\d{7}$/, '주민등록번호 형식이 올바르지 않습니다.'),
  address: z.string().min(5, '주소를 입력해주세요.'),
  phone: z.string().optional(),
})

interface Props {
  data?: TenantInfo
  onNext: (data: TenantInfo) => void
}

export default function StepTenant({ data, onNext }: Props) {
  const { register, handleSubmit, formState: { errors } } = useForm<TenantInfo>({
    resolver: zodResolver(schema),
    defaultValues: data,
  })

  return (
    <form onSubmit={handleSubmit(onNext)} className="space-y-5">
      <div>
        <label className="label">이름</label>
        <input className="input-field" placeholder="홍길동" {...register('name')} />
        {errors.name && <p className="error-text">{errors.name.message}</p>}
      </div>

      <div>
        <label className="label">주민등록번호</label>
        <input
          className="input-field"
          placeholder="000000-0000000"
          type="password"
          autoComplete="off"
          {...register('residentNumber')}
        />
        {errors.residentNumber && <p className="error-text">{errors.residentNumber.message}</p>}
        <p className="hint-text">주민등록초본 자동 발급에만 사용되며 저장되지 않습니다.</p>
      </div>

      <div>
        <label className="label">주소 (전입 주소)</label>
        <input
          className="input-field"
          placeholder="서울특별시 서초구 반포대로 201"
          {...register('address')}
        />
        {errors.address && <p className="error-text">{errors.address.message}</p>}
      </div>

      <div>
        <label className="label">연락처 (선택)</label>
        <input className="input-field" placeholder="010-0000-0000" type="tel" {...register('phone')} />
      </div>

      <div className="pt-2">
        <button type="submit" className="btn-primary">다음</button>
      </div>
    </form>
  )
}
