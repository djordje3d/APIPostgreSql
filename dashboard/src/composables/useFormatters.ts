/**
 * Shared formatters for dates, numbers, and money.
 * formatMoney accepts number or string and always returns "X RSD" or "–".
 * formatNumber returns formatted number only (no RSD), for use when suffix is added in template.
 */
export function formatTime(s: string | null | undefined): string {
  if (s == null || s === '') return '–'
  try {
    return new Date(s).toLocaleString()
  } catch {
    return String(s)
  }
}

export function formatNumber(value: string | number | null | undefined): string {
  if (value == null || value === '') return '–'
  const n = typeof value === 'number' ? value : parseFloat(String(value))
  if (Number.isNaN(n)) return '–'
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(n)
}

export function formatMoney(value: string | number | null | undefined): string {
  const formatted = formatNumber(value)
  if (formatted === '–') return '–'
  return formatted + ' RSD'
}

export function formatRate(value: string | number | null | undefined): string {
  return formatNumber(value)
}
