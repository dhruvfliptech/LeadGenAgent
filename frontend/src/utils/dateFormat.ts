import { format, formatDistanceToNow, isToday, isYesterday, parseISO } from 'date-fns'

/**
 * Formats a date string or Date object consistently across the app
 * - Shows "X minutes/hours ago" for recent dates (within 24 hours)
 * - Shows "Today at HH:mm" for today's dates
 * - Shows "Yesterday at HH:mm" for yesterday's dates
 * - Shows "MMM d, yyyy" for older dates
 */
export function formatDate(date: string | Date | null | undefined): string {
  if (!date) return '—'

  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date

    // For very recent dates (within 24 hours), show relative time
    const hoursDiff = (Date.now() - dateObj.getTime()) / (1000 * 60 * 60)
    if (hoursDiff < 24) {
      return formatDistanceToNow(dateObj, { addSuffix: true })
    }

    // For today
    if (isToday(dateObj)) {
      return `Today at ${format(dateObj, 'HH:mm')}`
    }

    // For yesterday
    if (isYesterday(dateObj)) {
      return `Yesterday at ${format(dateObj, 'HH:mm')}`
    }

    // For older dates
    return format(dateObj, 'MMM d, yyyy')
  } catch (error) {
    console.error('Error formatting date:', error)
    return '—'
  }
}

/**
 * Formats a date with time - shows full date and time
 * Format: "MMM d, yyyy at HH:mm"
 */
export function formatDateTime(date: string | Date | null | undefined): string {
  if (!date) return '—'

  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date
    return format(dateObj, 'MMM d, yyyy \'at\' HH:mm')
  } catch (error) {
    console.error('Error formatting datetime:', error)
    return '—'
  }
}

/**
 * Formats relative time (e.g., "5 minutes ago", "2 hours ago")
 */
export function formatRelativeTime(date: string | Date | null | undefined): string {
  if (!date) return '—'

  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date
    return formatDistanceToNow(dateObj, { addSuffix: true })
  } catch (error) {
    console.error('Error formatting relative time:', error)
    return '—'
  }
}

/**
 * Formats just the date without time
 * Format: "MMM d, yyyy"
 */
export function formatDateOnly(date: string | Date | null | undefined): string {
  if (!date) return '—'

  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date
    return format(dateObj, 'MMM d, yyyy')
  } catch (error) {
    console.error('Error formatting date only:', error)
    return '—'
  }
}

/**
 * Formats just the time
 * Format: "HH:mm:ss"
 */
export function formatTimeOnly(date: string | Date | null | undefined): string {
  if (!date) return '—'

  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date
    return format(dateObj, 'HH:mm:ss')
  } catch (error) {
    console.error('Error formatting time only:', error)
    return '—'
  }
}
