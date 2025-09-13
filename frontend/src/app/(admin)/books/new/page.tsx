'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { createBook } from '@/lib/api'
import { useNotification } from '@/contexts/notification-context'

interface FormErrors {
  title?: string
  author?: string
  publisher?: string
  general?: string
}

export default function NewBookPage() {
  const router = useRouter()
  const { success, error: showError } = useNotification()
  const [formData, setFormData] = useState({
    title: '',
    author: '',
    publisher: '',
    description: '',
    genre: '',
    language: 'ko'
  })
  const [errors, setErrors] = useState<FormErrors>({})
  const [submitting, setSubmitting] = useState(false)

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

    setSubmitting(true)
    setErrors({})

    try {
      const newBook = await createBook({
        title: formData.title.trim(),
        author: formData.author.trim(),
        publisher: formData.publisher.trim() || undefined,
        description: formData.description.trim() || undefined,
        genre: formData.genre || undefined,
        language: formData.language
      })
      
      // 성공 알림
      success(`"${newBook.title}" 책이 성공적으로 등록되었습니다.`)
      
      router.push('/books')
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '책 등록에 실패했습니다.'
      showError(errorMessage)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto p-6">
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold text-gray-900">새 책 등록</h1>
          <Link 
            href="/books"
            className="text-gray-600 hover:text-gray-900 text-sm"
          >
            ← 목록으로 돌아가기
          </Link>
        </div>
        <p className="mt-2 text-sm text-gray-600">
          새로운 오디오북을 등록합니다. 필수 정보를 입력해주세요.
        </p>
      </div>

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
              <div className="flex">
                <div className="text-red-600 text-sm">
                  {errors.general}
                </div>
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
              placeholder="예: 해리포터와 마법사의 돌"
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
              placeholder="예: J.K. 롤링"
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
              placeholder="예: 문학동네"
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
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
              placeholder="책에 대한 간단한 설명을 입력하세요..."
              maxLength={1000}
            />
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
          <div className="flex justify-end space-x-3 pt-4">
            <Link
              href="/books"
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-black focus:ring-offset-2"
            >
              취소
            </Link>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 text-sm font-medium text-white bg-black border border-transparent rounded-md hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-black focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? '등록 중...' : '책 등록'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}


