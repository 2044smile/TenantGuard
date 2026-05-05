'use client'

import { useState } from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import { Search, X, MapPin, Loader2 } from 'lucide-react'
import { searchAddress, type AddressResult } from '@/lib/api'

interface Props {
  onSelect: (address: string, result?: AddressResult) => void
  trigger: React.ReactNode
}

export default function AddressSearchModal({ onSelect, trigger }: Props) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<AddressResult[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSearch = async () => {
    if (!query.trim()) return
    setLoading(true)
    setError(null)
    setSearched(false)
    try {
      const data = await searchAddress(query.trim())
      setResults(data)
      setSearched(true)
    } catch {
      setError('주소 검색에 실패했습니다. 다시 시도해주세요.')
    } finally {
      setLoading(false)
    }
  }

  const handleSelect = (result: AddressResult) => {
    onSelect(result.road_address || result.jibun_address, result)
    setOpen(false)
    setQuery('')
    setResults([])
    setSearched(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSearch()
  }

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Trigger asChild>{trigger}</Dialog.Trigger>

      <Dialog.Portal>
        <Dialog.Overlay
          className="fixed inset-0 z-40"
          style={{ background: 'rgba(0,0,0,0.7)' }}
        />
        <Dialog.Content
          className="fixed z-50 flex flex-col rounded-2xl shadow-xl"
          style={{
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: 'calc(100% - 40px)',
            maxWidth: '420px',
            maxHeight: '80vh',
          }}
        >
          {/* 헤더 */}
          <div
            className="flex items-center justify-between px-5 py-4"
            style={{ borderBottom: '1px solid var(--border)' }}
          >
            <Dialog.Title
              className="text-base font-bold"
              style={{ color: 'var(--text)' }}
            >
              도로명 주소 검색
            </Dialog.Title>
            <Dialog.Close
              className="w-8 h-8 rounded-lg flex items-center justify-center"
              style={{ background: 'var(--surface-2)', color: 'var(--text-muted)' }}
            >
              <X className="w-4 h-4" />
            </Dialog.Close>
          </div>

          {/* 검색 입력 */}
          <div className="px-5 pt-4 pb-3">
            <div className="flex gap-2">
              <input
                className="input-field flex-1"
                placeholder="도로명 또는 지번 주소 입력"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                autoFocus
              />
              <button
                onClick={handleSearch}
                disabled={loading || !query.trim()}
                className="w-11 h-11 rounded-xl flex items-center justify-center shrink-0 transition-opacity disabled:opacity-50"
                style={{ background: 'var(--primary)', color: '#fff' }}
              >
                {loading
                  ? <Loader2 className="w-4 h-4 animate-spin" />
                  : <Search className="w-4 h-4" />
                }
              </button>
            </div>
            <p className="text-xs mt-2" style={{ color: 'var(--text-muted)' }}>
              예) 반포대로 201, 서초동 1700
            </p>
          </div>

          {/* 결과 목록 */}
          <div className="flex-1 overflow-y-auto px-5 pb-5">
            {error && (
              <p className="text-sm text-center py-4" style={{ color: 'var(--error)' }}>
                {error}
              </p>
            )}

            {searched && results.length === 0 && !error && (
              <p className="text-sm text-center py-8" style={{ color: 'var(--text-muted)' }}>
                검색 결과가 없습니다.
              </p>
            )}

            {results.length > 0 && (
              <div className="space-y-2">
                {results.map((r, i) => (
                  <button
                    key={i}
                    onClick={() => handleSelect(r)}
                    className="w-full text-left rounded-xl p-3 transition-colors"
                    style={{ background: 'var(--surface-2)', border: '1px solid var(--border)' }}
                  >
                    <div className="flex items-start gap-2.5">
                      <MapPin
                        className="w-4 h-4 mt-0.5 shrink-0"
                        style={{ color: 'var(--primary)' }}
                      />
                      <div>
                        <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>
                          {r.road_address}
                        </p>
                        {r.jibun_address && (
                          <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
                            지번 {r.jibun_address}
                          </p>
                        )}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
