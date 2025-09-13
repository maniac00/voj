'use client'

import { useEffect, useCallback } from 'react'

interface KeyboardNavigationOptions {
  onEscape?: () => void
  onEnter?: () => void
  onArrowUp?: () => void
  onArrowDown?: () => void
  onArrowLeft?: () => void
  onArrowRight?: () => void
  onTab?: () => void
  onShiftTab?: () => void
  enabled?: boolean
}

export function useKeyboardNavigation({
  onEscape,
  onEnter,
  onArrowUp,
  onArrowDown,
  onArrowLeft,
  onArrowRight,
  onTab,
  onShiftTab,
  enabled = true
}: KeyboardNavigationOptions) {
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (!enabled) return

    switch (event.key) {
      case 'Escape':
        onEscape?.()
        break
      case 'Enter':
        // 폼 제출이 아닌 경우에만 처리
        if (event.target && !(event.target as HTMLElement).closest('form')) {
          onEnter?.()
        }
        break
      case 'ArrowUp':
        event.preventDefault()
        onArrowUp?.()
        break
      case 'ArrowDown':
        event.preventDefault()
        onArrowDown?.()
        break
      case 'ArrowLeft':
        onArrowLeft?.()
        break
      case 'ArrowRight':
        onArrowRight?.()
        break
      case 'Tab':
        if (event.shiftKey) {
          onShiftTab?.()
        } else {
          onTab?.()
        }
        break
    }
  }, [enabled, onEscape, onEnter, onArrowUp, onArrowDown, onArrowLeft, onArrowRight, onTab, onShiftTab])

  useEffect(() => {
    if (enabled) {
      document.addEventListener('keydown', handleKeyDown)
      return () => document.removeEventListener('keydown', handleKeyDown)
    }
  }, [enabled, handleKeyDown])
}

interface FocusManagementOptions {
  autoFocus?: boolean
  restoreFocus?: boolean
  trapFocus?: boolean
}

export function useFocusManagement({
  autoFocus = false,
  restoreFocus = false,
  trapFocus = false
}: FocusManagementOptions = {}) {
  const focusRef = useCallback((element: HTMLElement | null) => {
    if (element && autoFocus) {
      // 다음 tick에서 포커스 설정 (렌더링 완료 후)
      setTimeout(() => {
        element.focus()
      }, 0)
    }
  }, [autoFocus])

  useEffect(() => {
    let previousActiveElement: Element | null = null

    if (restoreFocus) {
      previousActiveElement = document.activeElement
    }

    return () => {
      if (restoreFocus && previousActiveElement && 'focus' in previousActiveElement) {
        (previousActiveElement as HTMLElement).focus()
      }
    }
  }, [restoreFocus])

  const trapFocusInContainer = useCallback((container: HTMLElement) => {
    if (!trapFocus) return

    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    )
    
    const firstElement = focusableElements[0] as HTMLElement
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement

    const handleTabKey = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return

      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          e.preventDefault()
          lastElement?.focus()
        }
      } else {
        if (document.activeElement === lastElement) {
          e.preventDefault()
          firstElement?.focus()
        }
      }
    }

    container.addEventListener('keydown', handleTabKey)
    
    return () => {
      container.removeEventListener('keydown', handleTabKey)
    }
  }, [trapFocus])

  return {
    focusRef,
    trapFocusInContainer
  }
}

export function useAnnouncement() {
  const announce = useCallback((message: string, priority: 'polite' | 'assertive' = 'polite') => {
    // 스크린 리더를 위한 라이브 리전 생성
    const announcement = document.createElement('div')
    announcement.setAttribute('aria-live', priority)
    announcement.setAttribute('aria-atomic', 'true')
    announcement.className = 'sr-only'
    announcement.textContent = message

    document.body.appendChild(announcement)

    // 1초 후 제거
    setTimeout(() => {
      document.body.removeChild(announcement)
    }, 1000)
  }, [])

  return { announce }
}
