import { useEffect, useMemo, useState } from 'react'
import catalog from '../tomytec_data.json'

const tabs = [
  { id: 'all', label: '全部' },
  { id: 'TLV', label: 'TLV' },
  { id: 'TLV NEO', label: 'TLV-NEO' },
]

const yearOf = (releaseDate) => releaseDate?.match(/^\d{4}/)?.[0] ?? ''
const PAGE_SIZE = 20
const collectionStatuses = {
  owned: { label: '已擁有', badge: 'bg-emerald-600' },
  planned: { label: '預計購買', badge: 'bg-amber-500' },
}

const validStatus = (value) => (value === 'owned' || value === 'planned' ? value : null)

const releaseTimestamp = (releaseDate) => {
  const match = releaseDate?.match(/^(\d{4})年(\d{1,2})月$/)
  return match ? Date.UTC(Number(match[1]), Number(match[2]) - 1, 1) : -Infinity
}

function ProductCard({ product }) {
  const collectionStatus = validStatus(product.collectionStatus)
  const status = collectionStatuses[collectionStatus]
  return (
    <article className={`group overflow-hidden rounded-2xl border bg-white shadow-sm transition duration-200 hover:-translate-y-1 hover:shadow-lg ${
      collectionStatus === 'owned' ? 'border-emerald-400 ring-1 ring-emerald-100' : collectionStatus === 'planned' ? 'border-amber-400 ring-1 ring-amber-100' : 'border-stone-200'
    }`}>
      <div className="aspect-square overflow-hidden bg-stone-100">
        {product.imageUrl ? (
          <img
            className="h-full w-full object-contain p-3 transition duration-300 group-hover:scale-105"
            src={product.imageUrl}
            alt={product.name}
            loading="lazy"
            decoding="async"
          />
        ) : (
          <div className="grid h-full place-items-center text-sm text-stone-400">No image</div>
        )}
      </div>
      <div className="space-y-2 p-3 sm:p-4">
        <div className="flex items-center justify-between gap-2">
          <span className="inline-flex min-h-6 items-center rounded-full bg-red-700 px-2 py-0.5 text-xs font-bold tracking-wide text-white">
            {product.modelNumber || 'OTHER'}
          </span>
          <span className="shrink-0 text-xs font-medium text-stone-500">{product.releaseDate || '上市日期未公布'}</span>
        </div>
        <h2 className="line-clamp-2 min-h-10 text-sm font-semibold leading-5 text-stone-900 sm:text-base">
          {product.name}
        </h2>
        {status && (
          <span className={`inline-flex rounded-full px-2 py-1 text-xs font-bold text-white ${status.badge}`}>
            {status.label}
          </span>
        )}
      </div>
    </article>
  )
}

export default function App() {
  const [query, setQuery] = useState('')
  const [activeTab, setActiveTab] = useState('all')
  const [year, setYear] = useState('all')
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE)

  const years = useMemo(
    () => [...new Set(catalog.map((product) => yearOf(product.releaseDate)).filter(Boolean))].sort((a, b) => b.localeCompare(a)),
    [],
  )

  const products = useMemo(() => {
    const term = query.trim().toLocaleLowerCase()
    return catalog
      .filter((product) => {
        const matchesTab = activeTab === 'all' || product.series === activeTab
        const matchesYear = year === 'all' || yearOf(product.releaseDate) === year
        const haystack = `${product.modelNumber} ${product.name}`.toLocaleLowerCase()
        return matchesTab && matchesYear && (!term || haystack.includes(term))
      })
      .sort((a, b) => releaseTimestamp(b.releaseDate) - releaseTimestamp(a.releaseDate))
  }, [activeTab, query, year])

  // A new filter/search result should always start at the first 20 cards.
  useEffect(() => {
    setVisibleCount(PAGE_SIZE)
  }, [activeTab, query, year])

  const visibleProducts = products.slice(0, visibleCount)
  const hasMore = visibleProducts.length < products.length

  return (
    <main className="min-h-screen bg-stone-50 text-stone-900">
      <header className="border-b border-stone-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          <p className="text-xs font-bold tracking-[0.2em] text-red-700">TOMYTEC CATALOG</p>
          <h1 className="mt-2 text-3xl font-black tracking-tight sm:text-4xl">Tomica Limited Vintage</h1>
          <p className="mt-2 text-sm text-stone-600">瀏覽 TLV 與 TLV-NEO 迷你車型錄</p>
        </div>
      </header>

      <section className="sticky top-0 z-10 border-b border-stone-200 bg-stone-50/95 backdrop-blur">
        <div className="mx-auto max-w-7xl space-y-4 px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex gap-2 overflow-x-auto pb-1" role="tablist" aria-label="產品系列">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                type="button"
                role="tab"
                aria-selected={activeTab === tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`shrink-0 rounded-full px-4 py-2 text-sm font-bold transition ${
                  activeTab === tab.id ? 'bg-stone-900 text-white' : 'bg-white text-stone-600 ring-1 ring-stone-200 hover:bg-stone-100'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="grid gap-3 sm:grid-cols-[1fr_11rem]">
            <label className="relative block">
              <span className="sr-only">搜尋型號或名稱</span>
              <input
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="搜尋型號或產品名稱…"
                className="w-full rounded-xl border border-stone-300 bg-white px-4 py-3 text-sm outline-none transition placeholder:text-stone-400 focus:border-red-600 focus:ring-2 focus:ring-red-100"
              />
            </label>
            <label className="sr-only" htmlFor="year">上市年份</label>
            <select
              id="year"
              value={year}
              onChange={(event) => setYear(event.target.value)}
              className="rounded-xl border border-stone-300 bg-white px-3 py-3 text-sm font-medium outline-none focus:border-red-600 focus:ring-2 focus:ring-red-100"
            >
              <option value="all">所有上市年份</option>
              {years.map((item) => <option key={item} value={item}>{item} 年</option>)}
            </select>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-7 sm:px-6 lg:px-8">
        <p className="mb-5 text-sm text-stone-600" aria-live="polite">
          找到 <strong className="font-bold text-stone-900">{products.length}</strong> 項產品，已顯示 {visibleProducts.length} 項
        </p>
        {products.length ? (
          <>
            <div className="grid grid-cols-2 gap-3 sm:gap-4 md:grid-cols-4 xl:grid-cols-5">
              {visibleProducts.map((product, index) => (
                <ProductCard
                  key={`${product.series}-${product.modelNumber}-${product.name}-${index}`}
                  product={product}
                />
              ))}
            </div>
            {hasMore && (
              <div className="mt-8 flex justify-center">
                <button
                  type="button"
                  onClick={() => setVisibleCount((count) => count + PAGE_SIZE)}
                  className="rounded-xl bg-stone-900 px-6 py-3 text-sm font-bold text-white transition hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
                >
                  載入更多（還有 {products.length - visibleProducts.length} 項）
                </button>
              </div>
            )}
          </>
        ) : (
          <div className="rounded-2xl border border-dashed border-stone-300 bg-white px-6 py-16 text-center text-stone-500">
            找不到符合目前條件的產品。
          </div>
        )}
      </section>
    </main>
  )
}
