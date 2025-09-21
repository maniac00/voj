'use client'

import React, { useState, useRef, useEffect } from 'react'
import { useKeyboardNavigation } from '@/hooks/use-keyboard-navigation'

interface AccessibleTableProps {
  children: React.ReactNode
  caption?: string
  className?: string
  onRowSelect?: (rowIndex: number) => void
  onRowActivate?: (rowIndex: number) => void
}

export function AccessibleTable({ 
  children, 
  caption, 
  className = '',
  onRowSelect,
  onRowActivate
}: AccessibleTableProps) {
  const [focusedRow, setFocusedRow] = useState(-1)
  const tableRef = useRef<HTMLTableElement>(null)
  const [totalRows, setTotalRows] = useState(0)

  useEffect(() => {
    if (tableRef.current) {
      const rows = tableRef.current.querySelectorAll('tbody tr')
      setTotalRows(rows.length)
    }
  }, [children])

  useKeyboardNavigation({
    onArrowUp: () => {
      if (focusedRow > 0) {
        const newRow = focusedRow - 1
        setFocusedRow(newRow)
        focusRow(newRow)
        onRowSelect?.(newRow)
      }
    },
    onArrowDown: () => {
      if (focusedRow < totalRows - 1) {
        const newRow = focusedRow + 1
        setFocusedRow(newRow)
        focusRow(newRow)
        onRowSelect?.(newRow)
      }
    },
    onEnter: () => {
      if (focusedRow >= 0) {
        onRowActivate?.(focusedRow)
      }
    },
    enabled: focusedRow >= 0
  })

  const focusRow = (rowIndex: number) => {
    if (tableRef.current) {
      const rows = tableRef.current.querySelectorAll('tbody tr')
      const targetRow = rows[rowIndex] as HTMLElement
      if (targetRow) {
        targetRow.focus()
      }
    }
  }

  const handleRowFocus = (rowIndex: number) => {
    setFocusedRow(rowIndex)
    onRowSelect?.(rowIndex)
  }

  const handleRowClick = (rowIndex: number) => {
    setFocusedRow(rowIndex)
    onRowActivate?.(rowIndex)
  }

  return (
    <div className="overflow-x-auto">
      <table 
        ref={tableRef}
        className={`min-w-full divide-y divide-gray-200 ${className}`}
        role="table"
        aria-label={caption}
      >
        {caption && (
          <caption className="sr-only">
            {caption}
          </caption>
        )}
        {React.Children.map(children, (child, index) => {
          if (React.isValidElement(child) && (child.type as any) === 'tbody') {
            const tbodyEl = child as React.ReactElement<any>
            const tbodyChildren = (tbodyEl.props?.children ?? []) as React.ReactNode
            return React.cloneElement(tbodyEl, undefined, React.Children.map(tbodyChildren, (row, rowIndex) => {
                if (React.isValidElement(row) && (row.type as any) === 'tr') {
                  const rowEl = row as React.ReactElement<any>
                  return React.cloneElement(rowEl, {
                    ...rowEl.props,
                    tabIndex: 0,
                    'aria-rowindex': rowIndex + 1,
                    className: `${rowEl.props?.className || ''} table-row-focusable cursor-pointer`,
                    onFocus: () => handleRowFocus(rowIndex),
                    onClick: () => handleRowClick(rowIndex),
                    onKeyDown: (e: React.KeyboardEvent) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault()
                        onRowActivate?.(rowIndex)
                      }
                    }
                  })
                }
                return row
              }))
          }
          return child
        })}
      </table>
    </div>
  )
}

interface AccessibleTableHeaderProps {
  children: React.ReactNode
  sortable?: boolean
  sortDirection?: 'asc' | 'desc' | null
  onSort?: () => void
  className?: string
}

export function AccessibleTableHeader({ 
  children, 
  sortable = false, 
  sortDirection = null,
  onSort,
  className = ''
}: AccessibleTableHeaderProps) {
  const getSortAriaLabel = () => {
    if (!sortable) return undefined
    
    if (sortDirection === 'asc') {
      return '오름차순으로 정렬됨, 클릭하여 내림차순으로 변경'
    } else if (sortDirection === 'desc') {
      return '내림차순으로 정렬됨, 클릭하여 오름차순으로 변경'
    } else {
      return '정렬되지 않음, 클릭하여 정렬'
    }
  }

  if (sortable) {
    return (
      <th 
        className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 focus:bg-gray-100 focus:outline-none ${className}`}
        onClick={onSort}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            onSort?.()
          }
        }}
        tabIndex={0}
        role="columnheader"
        aria-sort={
          sortDirection === 'asc' ? 'ascending' :
          sortDirection === 'desc' ? 'descending' : 
          'none'
        }
        aria-label={getSortAriaLabel()}
      >
        <div className="flex items-center space-x-1">
          <span>{children}</span>
          <span aria-hidden="true">
            {sortDirection === null && '↕'}
            {sortDirection === 'asc' && '↑'}
            {sortDirection === 'desc' && '↓'}
          </span>
        </div>
      </th>
    )
  }

  return (
    <th 
      className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${className}`}
      role="columnheader"
    >
      {children}
    </th>
  )
}
