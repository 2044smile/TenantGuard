'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import type { ContractInfo } from '@/types/application'

const schema = z.object({
  contractDate: z.string().min(1, '계약일을 선택해주세요.'),
  depositAmount: z.coerce.number().min(1, '보증금을 입력해주세요.'),
  confirmedDate: z.string().optional(),
  moveInDate: z.string().optional(),
})

interface Props {
  data?: ContractInfo
  onNext: (data: ContractInfo) => void
}

function formatKoreanAmount(amount: number): string {
  if (!amount) return ''
  const eok = Math.floor(amount / 100_000_000)
  const man = Math.floor((amount % 100_000_000) / 10_000)
  const parts = []
  if (eok > 0) parts.push(`${eok}억`)
  if (man > 0) parts.push(`${man}만`)
  return parts.join(' ') + '원'
}

export default function StepContract({ data, onNext }: Props) {
  const { register, handleSubmit, watch, formState: { errors } } = useForm<ContractInfo>({
    resolver: zodResolver(schema),
    defaultValues: data,
  })

  const depositRaw = watch('depositAmount')

  return (
    <form onSubmit={handleSubmit(onNext)} className="space-y-4">
      <div>
        <label className="block text-sm font-medium mb-1">계약일</label>
        <input
          className="input-field"
          type="date"
          {...register('contractDate')}
        />
        {errors.contractDate && (
          <p className="text-xs text-red-500 mt-1">{errors.contractDate.message}</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">보증금 (원)</label>
        <input
          className="input-field"
          type="number"
          placeholder="300000000"
          {...register('depositAmount')}
        />
        {depositRaw > 0 && (
          <p className="text-xs text-blue-600 mt-1">{formatKoreanAmount(Number(depositRaw))}</p>
        )}
        {errors.depositAmount && (
          <p className="text-xs text-red-500 mt-1">{errors.depositAmount.message}</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">확정일자</label>
        <input
          className="input-field"
          type="date"
          {...register('confirmedDate')}
        />
        <p className="text-xs text-gray-400 mt-1">임대차계약서의 확정일자 도장 날짜</p>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">전입일</label>
        <input
          className="input-field"
          type="date"
          {...register('moveInDate')}
        />
      </div>

      <div className="pt-4">
        <button type="submit" className="btn-primary">다음</button>
      </div>
    </form>
  )
}
