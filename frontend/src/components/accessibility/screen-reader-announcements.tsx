'use client'

import React, { useEffect, useRef } from 'react'

interface ScreenReaderAnnouncementProps {
  message: string
  priority?: 'polite' | 'assertive'
  clearAfter?: number
}

export function ScreenReaderAnnouncement({ 
  message, 
  priority = 'polite',
  clearAfter = 1000 
}: ScreenReaderAnnouncementProps) {
  const announcementRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (message && announcementRef.current) {
      announcementRef.current.textContent = message

      if (clearAfter > 0) {
        const timer = setTimeout(() => {
          if (announcementRef.current) {
            announcementRef.current.textContent = ''
          }
        }, clearAfter)

        return () => clearTimeout(timer)
      }
    }
  }, [message, clearAfter])

  return (
    <div
      ref={announcementRef}
      aria-live={priority}
      aria-atomic="true"
      className="sr-only"
    />
  )
}

interface LiveRegionProps {
  children: React.ReactNode
  priority?: 'polite' | 'assertive'
  atomic?: boolean
  relevant?: 'additions' | 'removals' | 'text' | 'all'
}

export function LiveRegion({ 
  children, 
  priority = 'polite',
  atomic = true,
  relevant = 'all'
}: LiveRegionProps) {
  return (
    <div
      aria-live={priority}
      aria-atomic={atomic}
      aria-relevant={relevant}
    >
      {children}
    </div>
  )
}

interface SkipLinkProps {
  href: string
  children: React.ReactNode
}

export function SkipLink({ href, children }: SkipLinkProps) {
  return (
    <a
      href={href}
      className="skip-link focus:top-0 focus:left-4 bg-black text-white px-4 py-2 rounded-md z-50"
    >
      {children}
    </a>
  )
}

interface VisuallyHiddenProps {
  children: React.ReactNode
  focusable?: boolean
}

export function VisuallyHidden({ children, focusable = false }: VisuallyHiddenProps) {
  return (
    <span className={focusable ? 'sr-only focus:not-sr-only' : 'sr-only'}>
      {children}
    </span>
  )
}
