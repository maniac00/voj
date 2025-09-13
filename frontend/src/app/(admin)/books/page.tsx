'use client'

import React, { useEffect, useState, useMemo } from 'react'
import Link from 'next/link'
import { getBooks, deleteBook, BookDto } from '@/lib/api'
import { DeleteBookDialog } from '@/components/ui/delete-book-dialog'
import { TableSkeleton } from '@/components/ui/loading-spinner'
import { ErrorState } from '@/components/ui/error-state'
import { useNotification } from '@/contexts/notification-context'
import { AccessibleTable, AccessibleTableHeader } from '@/components/accessibility/accessible-table'
import { ScreenReaderAnnouncement, LiveRegion } from '@/components/accessibility/screen-reader-announcements'
import { useAnnouncement } from '@/hooks/use-keyboard-navigation'

type SortField = 'title' | 'author' | 'publisher' | 'status' | 'created_at'
type SortDirection = 'asc' | 'desc'

export default function BooksPage() {
  const [books, setBooks] = useState<BookDto[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const { success, error: showError } = useNotification()
  const { announce } = useAnnouncement()
  
  // 필터링 및 정렬 상태
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [genreFilter, setGenreFilter] = useState('')
  const [sortField, setSortField] = useState<SortField>('created_at')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')
  
  // 삭제 관련 상태
  const [bookToDelete, setBookToDelete] = useState<BookDto | null>(null)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    const loadBooks = async () => {
      try {
        const data = await getBooks()
        setBooks(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : '책 목록을 불러오는데 실패했습니다.')
      } finally {
        setLoading(false)
      }
    }

    loadBooks()
  }, [])

  // 필터링 및 정렬된 책 목록
  const filteredAndSortedBooks = useMemo(() => {
    let filtered = books

    // 검색 필터
    if (searchTerm) {
      const term = searchTerm.toLowerCase()
      filtered = filtered.filter(book => 
        book.title.toLowerCase().includes(term) ||
        book.author.toLowerCase().includes(term) ||
        (book.publisher || '').toLowerCase().includes(term)
      )
    }

    // 상태 필터
    if (statusFilter) {
      filtered = filtered.filter(book => book.status === statusFilter)
    }

    // 장르 필터
    if (genreFilter) {
      filtered = filtered.filter(book => book.genre === genreFilter)
    }

    // 정렬
    filtered.sort((a, b) => {
      let aValue: string | number = ''
      let bValue: string | number = ''

      switch (sortField) {
        case 'title':
          aValue = a.title || ''
          bValue = b.title || ''
          break
        case 'author':
          aValue = a.author || ''
          bValue = b.author || ''
          break
        case 'publisher':
          aValue = a.publisher || ''
          bValue = b.publisher || ''
          break
        case 'status':
          aValue = a.status || ''
          bValue = b.status || ''
          break
        case 'created_at':
          aValue = a.created_at || ''
          bValue = b.created_at || ''
          break
      }

      if (typeof aValue === 'string' && typeof bValue === 'string') {
        const comparison = aValue.localeCompare(bValue)
        return sortDirection === 'asc' ? comparison : -comparison
      }

      return 0
    })

    return filtered
  }, [books, searchTerm, statusFilter, genreFilter, sortField, sortDirection])

  // 정렬 핸들러
  const handleSort = (field: SortField) => {
    const newDirection = sortField === field 
      ? (sortDirection === 'asc' ? 'desc' : 'asc')
      : 'asc'
    
    setSortField(field)
    setSortDirection(newDirection)
    
    // 스크린 리더를 위한 알림
    const fieldNames = {
      title: '제목',
      author: '저자', 
      publisher: '출판사',
      status: '상태',
      created_at: '등록일'
    }
    
    const directionText = newDirection === 'asc' ? '오름차순' : '내림차순'
    announce(`${fieldNames[field]} ${directionText}으로 정렬되었습니다.`)
  }

  // 필터 초기화
  const clearFilters = () => {
    setSearchTerm('')
    setStatusFilter('')
    setGenreFilter('')
    setSortField('created_at')
    setSortDirection('desc')
    
    // 스크린 리더를 위한 알림
    announce('모든 필터가 초기화되었습니다.')
  }

  // 고유 값들 추출 (필터 옵션용)
  const uniqueStatuses = useMemo(() => 
    [...new Set(books.map(book => book.status).filter(Boolean))],
    [books]
  )
  
  const uniqueGenres = useMemo(() => 
    [...new Set(books.map(book => book.genre).filter(Boolean))],
    [books]
  )

  // 삭제 핸들러
  const handleDeleteBook = async () => {
    if (!bookToDelete) return

    setDeleting(true)
    
    try {
      await deleteBook(bookToDelete.book_id)
      
      // 목록에서 삭제된 책 제거
      setBooks(prev => prev.filter(book => book.book_id !== bookToDelete.book_id))
      setBookToDelete(null)
      
      // 성공 알림
      success(`"${bookToDelete.title}" 책이 성공적으로 삭제되었습니다.`)
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '책 삭제에 실패했습니다.'
      showError(errorMessage)
    } finally {
      setDeleting(false)
    }
  }

  // 상태별 색상 매핑
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'published':
        return 'bg-green-100 text-green-800'
      case 'draft':
        return 'bg-gray-100 text-gray-800'
      case 'processing':
        return 'bg-yellow-100 text-yellow-800'
      case 'error':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  // 정렬 아이콘 컴포넌트
  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) {
      return <span className="text-gray-400">↕</span>
    }
    return sortDirection === 'asc' ? <span className="text-gray-700">↑</span> : <span className="text-gray-700">↓</span>
  }

  if (loading) {
    return (
      <div className="p-6">
        <div className="mb-6">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-1/3"></div>
        </div>
        <div className="bg-gray-200 h-12 rounded mb-6"></div>
        <TableSkeleton rows={5} columns={8} />
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <ErrorState
          title="책 목록을 불러올 수 없습니다"
          message={error}
          showRetry={true}
          onRetry={() => window.location.reload()}
          showHome={false}
        />
      </div>
    )
  }

  return (
    <div className="p-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">책 목록</h1>
          <p className="mt-1 text-sm text-gray-600">
            총 {books.length}권 중 {filteredAndSortedBooks.length}권 표시
          </p>
        </div>
        <Link 
          href="/books/new" 
          className="bg-black text-white px-4 py-2 rounded-md hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-black focus:ring-offset-2"
        >
          새 책 등록
        </Link>
      </div>

      {/* 필터 및 검색 */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 mb-6" role="search" aria-label="책 검색 및 필터링">
        <h2 className="text-lg font-medium text-gray-900 mb-4">검색 및 필터</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* 검색 */}
          <div>
            <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-1">
              검색
            </label>
            <input
              id="search"
              type="text"
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value)
                if (e.target.value) {
                  announce(`검색어 "${e.target.value}"로 검색 중`)
                }
              }}
              placeholder="제목, 저자, 출판사 검색..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
              aria-describedby="search-help"
            />
            <div id="search-help" className="sr-only">
              제목, 저자, 출판사에서 검색됩니다. 검색어를 입력하면 실시간으로 결과가 필터링됩니다.
            </div>
          </div>

          {/* 상태 필터 */}
          <div>
            <label htmlFor="status-filter" className="block text-sm font-medium text-gray-700 mb-1">
              상태 필터
            </label>
            <select
              id="status-filter"
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value)
                const statusText = e.target.value || '모든 상태'
                announce(`상태 필터가 ${statusText}로 변경되었습니다.`)
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
              aria-describedby="status-filter-help"
            >
              <option value="">모든 상태</option>
              {uniqueStatuses.map(status => (
                <option key={status} value={status}>{status}</option>
              ))}
            </select>
            <div id="status-filter-help" className="sr-only">
              책의 상태별로 필터링할 수 있습니다.
            </div>
          </div>

          {/* 장르 필터 */}
          <div>
            <label htmlFor="genre-filter" className="block text-sm font-medium text-gray-700 mb-1">
              장르 필터
            </label>
            <select
              id="genre-filter"
              value={genreFilter}
              onChange={(e) => {
                setGenreFilter(e.target.value)
                const genreText = e.target.value || '모든 장르'
                announce(`장르 필터가 ${genreText}로 변경되었습니다.`)
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
              aria-describedby="genre-filter-help"
            >
              <option value="">모든 장르</option>
              {uniqueGenres.map(genre => (
                <option key={genre} value={genre || ''}>{genre}</option>
              ))}
            </select>
            <div id="genre-filter-help" className="sr-only">
              책의 장르별로 필터링할 수 있습니다.
            </div>
          </div>

          {/* 필터 초기화 */}
          <div className="flex items-end">
            <button
              onClick={clearFilters}
              className="w-full px-3 py-2 text-sm text-gray-600 bg-gray-100 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
              aria-label="모든 검색 조건 및 필터 초기화"
            >
              필터 초기화
            </button>
          </div>
        </div>
        
        {/* 검색 결과 요약 */}
        <LiveRegion>
          <div className="mt-4 text-sm text-gray-600" aria-live="polite">
            {searchTerm || statusFilter || genreFilter ? (
              `필터 적용됨: ${filteredAndSortedBooks.length}개 결과`
            ) : (
              `전체 ${books.length}개 책`
            )}
          </div>
        </LiveRegion>
      </div>
      
      {/* 책 목록 테이블 */}
      {filteredAndSortedBooks.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
          {books.length === 0 ? (
            <>
              <p className="text-gray-500 mb-4">등록된 책이 없습니다.</p>
              <Link 
                href="/books/new" 
                className="inline-block text-black hover:underline"
              >
                첫 번째 책을 등록해보세요
              </Link>
            </>
          ) : (
            <>
              <p className="text-gray-500 mb-4">검색 조건에 맞는 책이 없습니다.</p>
              <button
                onClick={clearFilters}
                className="text-black hover:underline"
              >
                필터 초기화
              </button>
            </>
          )}
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden rounded-lg border border-gray-200">
          <AccessibleTable 
            caption={`책 목록 테이블. 총 ${books.length}권 중 ${filteredAndSortedBooks.length}권 표시됨.`}
            onRowActivate={(rowIndex) => {
              const book = filteredAndSortedBooks[rowIndex]
              if (book) {
                window.location.href = `/books/${book.book_id}`
              }
            }}
          >
            <thead className="bg-gray-50">
              <tr role="row">
                <AccessibleTableHeader
                  sortable={true}
                  sortDirection={sortField === 'title' ? sortDirection : null}
                  onSort={() => handleSort('title')}
                >
                  제목
                </AccessibleTableHeader>
                
                <AccessibleTableHeader
                  sortable={true}
                  sortDirection={sortField === 'author' ? sortDirection : null}
                  onSort={() => handleSort('author')}
                >
                  저자
                </AccessibleTableHeader>
                
                <AccessibleTableHeader
                  sortable={true}
                  sortDirection={sortField === 'publisher' ? sortDirection : null}
                  onSort={() => handleSort('publisher')}
                >
                  출판사
                </AccessibleTableHeader>
                
                <AccessibleTableHeader>
                  장르
                </AccessibleTableHeader>
                
                <AccessibleTableHeader
                  sortable={true}
                  sortDirection={sortField === 'status' ? sortDirection : null}
                  onSort={() => handleSort('status')}
                >
                  상태
                </AccessibleTableHeader>
                
                <AccessibleTableHeader>
                  챕터
                </AccessibleTableHeader>
                
                <AccessibleTableHeader
                  sortable={true}
                  sortDirection={sortField === 'created_at' ? sortDirection : null}
                  onSort={() => handleSort('created_at')}
                >
                  등록일
                </AccessibleTableHeader>
                
                <AccessibleTableHeader>
                  작업
                </AccessibleTableHeader>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredAndSortedBooks.map((book, index) => (
                <tr 
                  key={book.book_id} 
                  className="hover:bg-gray-50"
                  role="row"
                  aria-rowindex={index + 2}
                  aria-label={`${book.title}, 저자: ${book.author}, 상태: ${book.status || 'draft'}`}
                >
                  <td className="px-6 py-4 whitespace-nowrap" role="gridcell">
                    <div className="text-sm font-medium text-gray-900">
                      {book.title}
                    </div>
                    {book.description && (
                      <div className="text-sm text-gray-500 truncate max-w-xs">
                        {book.description}
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500" role="gridcell">
                    {book.author}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500" role="gridcell">
                    {book.publisher || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500" role="gridcell">
                    {book.genre || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap" role="gridcell">
                    <span 
                      className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(book.status || 'draft')}`}
                      aria-label={`상태: ${book.status || 'draft'}`}
                    >
                      {book.status || 'draft'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500" role="gridcell">
                    <span aria-label={`총 ${book.total_chapters || 0}개 챕터`}>
                      {book.total_chapters || 0}개
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500" role="gridcell">
                    {book.created_at ? new Date(book.created_at).toLocaleDateString('ko-KR') : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium" role="gridcell">
                    <div className="button-group" role="group" aria-label={`${book.title} 작업`}>
                      <Link 
                        href={`/books/${book.book_id}`} 
                        className="text-black hover:text-gray-700 px-2 py-1 rounded focus:outline-none focus:ring-2 focus:ring-black"
                        aria-label={`${book.title} 편집`}
                      >
                        편집
                      </Link>
                      <Link 
                        href={`/books/${book.book_id}/audios`} 
                        className="text-blue-600 hover:text-blue-800 px-2 py-1 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                        aria-label={`${book.title} 오디오 관리`}
                      >
                        오디오
                      </Link>
                      <button
                        onClick={() => setBookToDelete(book)}
                        className="text-red-600 hover:text-red-800 px-2 py-1 rounded hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-500"
                        aria-label={`${book.title} 삭제`}
                      >
                        삭제
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </AccessibleTable>
        </div>
      )}

      {/* 삭제 확인 다이얼로그 */}
      <DeleteBookDialog
        book={bookToDelete}
        isOpen={bookToDelete !== null}
        onClose={() => setBookToDelete(null)}
        onConfirm={handleDeleteBook}
        loading={deleting}
      />
    </div>
  )
}


