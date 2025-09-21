'use client'

import React, { useEffect, useState } from 'react'
import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { deleteBook, getBook, updateBook, BookDto, UpdateBookPayload } from '@/lib/api'
import { DeleteBookDialog } from '@/components/ui/delete-book-dialog'
import { FormSkeleton } from '@/components/ui/loading-spinner'
import { ErrorState } from '@/components/ui/error-state'
import { useNotification } from '@/contexts/notification-context'

interface FormErrors {
  title?: string
  author?: string
  publisher?: string
  description?: string
  general?: string
}

export default function EditBookPage() {
  const params = useParams()
  const bookId = String(params?.bookId || '')
  const router = useRouter()
  const { success, error: showError } = useNotification()
  
  const [book, setBook] = useState<BookDto | null>(null)
  const [formData, setFormData] = useState({
    title: '',
    author: '',
    publisher: '',
    description: '',
    genre: '',
    language: 'ko'
  })
  const [errors, setErrors] = useState<FormErrors>({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    const loadBook = async () => {
      if (!bookId) return
      
      try {
        const bookData = await getBook(bookId)
        setBook(bookData)
        setFormData({
          title: bookData.title || '',
          author: bookData.author || '',
          publisher: bookData.publisher || '',
          description: bookData.description || '',
          genre: bookData.genre || '',
          language: bookData.language || 'ko'
        })
      } catch (err) {
        setErrors({ 
          general: err instanceof Error ? err.message : '책 정보를 불러오는데 실패했습니다.' 
        })
      } finally {
        setLoading(false)
      }
    }

    loadBook()
  }, [bookId])

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {}

    // 제목 검증
    if (!formData.title.trim()) {
      newErrors.title = '제목을 입력해주세요.'
    } else if (formData.title.length > 200) {
      newErrors.title = '제목은 200자 이하로 입력해주세요.'
    }

    // 저자 검증
    if (!formData.author.trim()) {
      newErrors.author = '저자를 입력해주세요.'
    } else if (formData.author.length > 100) {
      newErrors.author = '저자는 100자 이하로 입력해주세요.'
    }

    // 출판사 검증 (선택적)
    if (formData.publisher && formData.publisher.length > 100) {
      newErrors.publisher = '출판사는 100자 이하로 입력해주세요.'
    }

    // 설명 검증 (선택적)
    if (formData.description && formData.description.length > 1000) {
      newErrors.description = '설명은 1000자 이하로 입력해주세요.'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    
    // 입력 시 해당 필드 에러 제거
    if (errors[field as keyof FormErrors]) {
      setErrors(prev => ({ ...prev, [field]: undefined }))
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }

    setSaving(true)
    setErrors({})

    try {
      const updatePayload: UpdateBookPayload = {
        title: formData.title.trim(),
        author: formData.author.trim(),
        publisher: formData.publisher.trim() || undefined,
        description: formData.description.trim() || undefined,
        genre: formData.genre || undefined,
        language: formData.language
      }

      const updatedBook = await updateBook(bookId, updatePayload)
      setBook(updatedBook)
      
      // 성공 알림
      success('책 정보가 성공적으로 수정되었습니다.')
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '책 수정에 실패했습니다.'
      setErrors({ general: errorMessage })
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    setDeleting(true)
    
    try {
      await deleteBook(bookId)
      // 성공적으로 삭제되면 목록 페이지로 이동
      success('책이 성공적으로 삭제되었습니다.')
      router.push('/books')
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '책 삭제에 실패했습니다.'
      showError(errorMessage)
      setShowDeleteDialog(false)
    } finally {
      setDeleting(false)
    }
  }

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="mb-6">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-2/3"></div>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <FormSkeleton fields={6} />
          </div>
          <div className="space-y-6">
            <div className="bg-gray-200 h-48 rounded"></div>
            <div className="bg-gray-200 h-32 rounded"></div>
          </div>
        </div>
      </div>
    )
  }

  if (!book && !loading) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <ErrorState
          title="책을 찾을 수 없습니다"
          message="요청하신 책이 존재하지 않거나 접근 권한이 없습니다."
          showHome={true}
        />
      </div>
    )
  }

  const b = book as BookDto
  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* 헤더 */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">책 편집</h1>
            <p className="mt-1 text-sm text-gray-600">
              책 정보를 수정하거나 오디오 파일을 관리할 수 있습니다.
            </p>
          </div>
          <Link 
            href="/books"
            className="text-gray-600 hover:text-gray-900 text-sm"
          >
            ← 목록으로 돌아가기
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 왼쪽: 책 정보 편집 */}
        <div className="lg:col-span-2">
          <div className="bg-white shadow-sm rounded-lg border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900">기본 정보</h2>
            </div>
            
            <form onSubmit={handleSubmit} className="p-6 space-y-6">
              {/* 일반 에러 메시지 */}
              {errors.general && (
                <div 
                  className="bg-red-50 border border-red-200 rounded-md p-4"
                  role="alert"
                  aria-live="polite"
                >
                  <div className="text-red-600 text-sm">
                    {errors.general}
                  </div>
                </div>
              )}

              {/* 제목 */}
              <div>
                <label 
                  htmlFor="title" 
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  제목 <span className="text-red-500" aria-label="필수">*</span>
                </label>
                <input
                  id="title"
                  type="text"
                  value={formData.title}
                  onChange={(e) => handleInputChange('title', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent ${
                    errors.title ? 'border-red-300 bg-red-50' : 'border-gray-300'
                  }`}
                  required
                  maxLength={200}
                  aria-describedby={errors.title ? 'title-error' : undefined}
                />
                {errors.title && (
                  <p id="title-error" className="mt-1 text-sm text-red-600" role="alert">
                    {errors.title}
                  </p>
                )}
                <p className="mt-1 text-xs text-gray-500">
                  {formData.title.length}/200자
                </p>
              </div>

              {/* 저자 */}
              <div>
                <label 
                  htmlFor="author" 
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  저자 <span className="text-red-500" aria-label="필수">*</span>
                </label>
                <input
                  id="author"
                  type="text"
                  value={formData.author}
                  onChange={(e) => handleInputChange('author', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent ${
                    errors.author ? 'border-red-300 bg-red-50' : 'border-gray-300'
                  }`}
                  required
                  maxLength={100}
                  aria-describedby={errors.author ? 'author-error' : undefined}
                />
                {errors.author && (
                  <p id="author-error" className="mt-1 text-sm text-red-600" role="alert">
                    {errors.author}
                  </p>
                )}
                <p className="mt-1 text-xs text-gray-500">
                  {formData.author.length}/100자
                </p>
              </div>

              {/* 출판사 */}
              <div>
                <label 
                  htmlFor="publisher" 
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  출판사 <span className="text-gray-400 text-xs">(선택)</span>
                </label>
                <input
                  id="publisher"
                  type="text"
                  value={formData.publisher}
                  onChange={(e) => handleInputChange('publisher', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent ${
                    errors.publisher ? 'border-red-300 bg-red-50' : 'border-gray-300'
                  }`}
                  maxLength={100}
                  aria-describedby={errors.publisher ? 'publisher-error' : undefined}
                />
                {errors.publisher && (
                  <p id="publisher-error" className="mt-1 text-sm text-red-600" role="alert">
                    {errors.publisher}
                  </p>
                )}
                <p className="mt-1 text-xs text-gray-500">
                  {formData.publisher.length}/100자
                </p>
              </div>

              {/* 설명 */}
              <div>
                <label 
                  htmlFor="description" 
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  설명 <span className="text-gray-400 text-xs">(선택)</span>
                </label>
                <textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  rows={3}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent ${
                    errors.description ? 'border-red-300 bg-red-50' : 'border-gray-300'
                  }`}
                  maxLength={1000}
                  aria-describedby={errors.description ? 'description-error' : undefined}
                />
                {errors.description && (
                  <p id="description-error" className="mt-1 text-sm text-red-600" role="alert">
                    {errors.description}
                  </p>
                )}
                <p className="mt-1 text-xs text-gray-500">
                  {formData.description.length}/1000자
                </p>
              </div>

              {/* 장르 */}
              <div>
                <label 
                  htmlFor="genre" 
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  장르 <span className="text-gray-400 text-xs">(선택)</span>
                </label>
                <select
                  id="genre"
                  value={formData.genre}
                  onChange={(e) => handleInputChange('genre', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
                >
                  <option value="">장르 선택</option>
                  <option value="소설">소설</option>
                  <option value="에세이">에세이</option>
                  <option value="자기계발">자기계발</option>
                  <option value="역사">역사</option>
                  <option value="과학">과학</option>
                  <option value="철학">철학</option>
                  <option value="종교">종교</option>
                  <option value="어린이">어린이</option>
                  <option value="기타">기타</option>
                </select>
              </div>

              {/* 언어 */}
              <div>
                <label 
                  htmlFor="language" 
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  언어
                </label>
                <select
                  id="language"
                  value={formData.language}
                  onChange={(e) => handleInputChange('language', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
                >
                  <option value="ko">한국어</option>
                  <option value="en">영어</option>
                  <option value="ja">일본어</option>
                  <option value="zh">중국어</option>
                </select>
              </div>

              {/* 버튼 */}
              <div className="flex justify-between pt-4">
                <button
                  type="button"
                  onClick={() => setShowDeleteDialog(true)}
                  className="px-4 py-2 text-sm font-medium text-red-700 bg-red-50 border border-red-200 rounded-md hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
                >
                  책 삭제
                </button>
                
                <div className="flex space-x-3">
                  <Link
                    href="/books"
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-black focus:ring-offset-2"
                  >
                    취소
                  </Link>
                  <button
                    type="submit"
                    disabled={saving}
                    className="px-4 py-2 text-sm font-medium text-white bg-black border border-transparent rounded-md hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-black focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {saving ? '저장 중...' : '변경사항 저장'}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>

        {/* 오른쪽: 책 정보 및 빠른 작업 */}
        <div className="space-y-6">
          {/* 책 상태 정보 */}
          <div className="bg-white shadow-sm rounded-lg border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">책 상태</h3>
            </div>
            <div className="p-6 space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">상태</span>
                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                  b.status === 'published' ? 'bg-green-100 text-green-800' :
                  b.status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                  b.status === 'error' ? 'bg-red-100 text-red-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {b.status || 'draft'}
                </span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">총 챕터</span>
                <span className="text-sm font-medium">{b.total_chapters || 0}개</span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">총 재생시간</span>
                <span className="text-sm font-medium">
                  {b.total_duration ? `${Math.floor(b.total_duration / 60)}분` : '0분'}
                </span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">등록일</span>
                <span className="text-sm font-medium">
                  {b.created_at ? new Date(b.created_at).toLocaleDateString('ko-KR') : '-'}
                </span>
              </div>
            </div>
          </div>

          {/* 빠른 작업 */}
          <div className="bg-white shadow-sm rounded-lg border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">빠른 작업</h3>
            </div>
            <div className="p-6 space-y-3">
              <Link
                href={`/books/${bookId}/audios`}
                className="w-full flex items-center justify-center px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-black focus:ring-offset-2"
              >
                오디오 파일 관리
              </Link>
              
              <button
                onClick={() => window.open(`/books/${bookId}/preview`, '_blank')}
                className="w-full flex items-center justify-center px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-black focus:ring-offset-2"
              >
                미리보기
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 삭제 확인 다이얼로그 */}
      <DeleteBookDialog
        book={book}
        isOpen={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        onConfirm={handleDelete}
        loading={deleting}
      />
    </div>
  )
}


