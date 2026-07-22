/**
 * ====================================================
 * Utility Functions
 * ====================================================
 */
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

// Tailwind class merger
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs))
}

// Number formatting
export function formatNumber(value: number | null | undefined, decimals = 0): string {
  if (value == null) return 'N/A'
  return new Intl.NumberFormat('en-IN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value)
}

export function formatCompact(value: number | null | undefined): string {
  if (value == null) return 'N/A'
  return new Intl.NumberFormat('en-IN', { notation: 'compact' }).format(value)
}

export function formatPercent(value: number | null | undefined, decimals = 1): string {
  if (value == null) return 'N/A'
  return `${value.toFixed(decimals)}%`
}

export function formatScore(value: number | null | undefined): string {
  if (value == null) return 'N/A'
  return value.toFixed(1)
}

// Date formatting
export function formatDate(value: string | number | Date | null | undefined): string {
  if (!value) return 'N/A'
  return new Date(value).toLocaleString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatRelativeTime(value: number | string | Date): string {
  const date = new Date(value).getTime()
  const now = Date.now()
  const diff = now - date
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (seconds < 60) return `${seconds}s ago`
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  return `${days}d ago`
}

// Risk color
export function getRiskColor(score: number): string {
  if (score >= 80) return '#ef4444' // critical (red)
  if (score >= 60) return '#f97316' // high (orange)
  if (score >= 40) return '#eab308' // medium (yellow)
  return '#10b981' // low (green)
}

export function getRiskLevel(score: number): 'low' | 'medium' | 'high' | 'critical' {
  if (score >= 80) return 'critical'
  if (score >= 60) return 'high'
  if (score >= 40) return 'medium'
  return 'low'
}

export function getRiskBadgeClass(score: number): string {
  const level = getRiskLevel(score)
  return {
    low: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    critical: 'bg-red-500/20 text-red-400 border-red-500/30',
  }[level]
}

// Trend direction
export function getTrendIcon(direction: string): '↑' | '↓' | '→' {
  if (direction === 'up') return '↑'
  if (direction === 'down') return '↓'
  return '→'
}

export function getTrendColor(direction: string): string {
  if (direction === 'up') return 'text-red-400'
  if (direction === 'down') return 'text-emerald-400'
  return 'text-slate-400'
}

// Download helpers
export function downloadFile(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  window.URL.revokeObjectURL(url)
}

export function downloadFromUrl(url: string, filename: string) {
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.target = '_blank'
  a.rel = 'noopener noreferrer'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}
