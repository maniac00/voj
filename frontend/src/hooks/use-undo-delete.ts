'use client'

import { useState, useCallback } from 'react'
import { BookDto } from '@/lib/api'

interface DeletedItem {
  book: BookDto
  deletedAt: number
  timeout: NodeJS.Timeout
}

const UNDO_TIMEOUT = 10000 // 10초

export function useUndoDelete() {
  const [deletedItems, setDeletedItems] = useState<Map<string, DeletedItem>>(new Map())

  const addDeletedItem = useCallback((book: BookDto, onUndo: (book: BookDto) => void) => {
    const timeout = setTimeout(() => {
      setDeletedItems(prev => {
        const newMap = new Map(prev)
        newMap.delete(book.book_id)
        return newMap
      })
    }, UNDO_TIMEOUT)

    const deletedItem: DeletedItem = {
      book,
      deletedAt: Date.now(),
      timeout
    }

    setDeletedItems(prev => {
      const newMap = new Map(prev)
      
      // 기존 타이머가 있다면 취소
      const existing = newMap.get(book.book_id)
      if (existing) {
        clearTimeout(existing.timeout)
      }
      
      newMap.set(book.book_id, deletedItem)
      return newMap
    })

    return () => {
      // Undo 함수
      const item = deletedItems.get(book.book_id)
      if (item) {
        clearTimeout(item.timeout)
        setDeletedItems(prev => {
          const newMap = new Map(prev)
          newMap.delete(book.book_id)
          return newMap
        })
        onUndo(book)
      }
    }
  }, [deletedItems])

  const clearDeletedItem = useCallback((bookId: string) => {
    setDeletedItems(prev => {
      const newMap = new Map(prev)
      const item = newMap.get(bookId)
      if (item) {
        clearTimeout(item.timeout)
        newMap.delete(bookId)
      }
      return newMap
    })
  }, [])

  const getDeletedItems = useCallback(() => {
    return Array.from(deletedItems.values()).map(item => ({
      book: item.book,
      deletedAt: item.deletedAt,
      timeLeft: Math.max(0, UNDO_TIMEOUT - (Date.now() - item.deletedAt))
    }))
  }, [deletedItems])

  return {
    addDeletedItem,
    clearDeletedItem,
    getDeletedItems,
    hasDeletedItems: deletedItems.size > 0
  }
}
