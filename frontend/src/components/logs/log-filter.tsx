'use client'

import React, { useState, useEffect } from 'react'
import { LogMessage } from '@/hooks/use-websocket-logs'

export interface LogFilter {
  levels: string[]
  categories: string[]
  searchTerm: string
  dateRange: {
    start?: Date
    end?: Date
  }
  chapterIds: string[]
  jobIds: string[]
  showOnlyErrors: boolean
  showOnlyRecent: boolean
}

interface LogFilterProps {
  logs: LogMessage[]
  onFilterChange: (filteredLogs: LogMessage[]) => void
  className?: string
}

export function LogFilter({ logs, onFilterChange, className = '' }: LogFilterProps) {
  const [filter, setFilter] = useState<LogFilter>({
    levels: [],
    categories: [],
    searchTerm: '',
    dateRange: {},
    chapterIds: [],
    jobIds: [],
    showOnlyErrors: false,
    showOnlyRecent: false
  })

  const [isAdvancedMode, setIsAdvancedMode] = useState(false)
  const [savedFilters, setSavedFilters] = useState<Array<{ name: string; filter: LogFilter }>>([])

  // 고유 값들 추출
  const uniqueLevels = [...new Set(logs.map(log => log.level))]
  const uniqueCategories = [...new Set(logs.map(log => log.category))]
  const uniqueChapterIds = [...new Set(logs.map(log => log.chapter_id).filter(Boolean))]
  const uniqueJobIds = [...new Set(logs.map(log => log.job_id).filter(Boolean))]

  // 필터 적용
  useEffect(() => {
    let filtered = logs

    // 레벨 필터
    if (filter.levels.length > 0) {
      filtered = filtered.filter(log => filter.levels.includes(log.level))
    }

    // 카테고리 필터
    if (filter.categories.length > 0) {
      filtered = filtered.filter(log => filter.categories.includes(log.category))
    }

    // 검색어 필터
    if (filter.searchTerm) {
      const term = filter.searchTerm.toLowerCase()
      filtered = filtered.filter(log => 
        log.message.toLowerCase().includes(term) ||
        (log.details && JSON.stringify(log.details).toLowerCase().includes(term)) ||
        (log.chapter_id && log.chapter_id.toLowerCase().includes(term)) ||
        (log.job_id && log.job_id.toLowerCase().includes(term))
      )
    }

    // 날짜 범위 필터
    if (filter.dateRange.start || filter.dateRange.end) {
      filtered = filtered.filter(log => {
        const logDate = new Date(log.timestamp)
        
        if (filter.dateRange.start && logDate < filter.dateRange.start) {
          return false
        }
        
        if (filter.dateRange.end && logDate > filter.dateRange.end) {
          return false
        }
        
        return true
      })
    }

    // 챕터 ID 필터
    if (filter.chapterIds.length > 0) {
      filtered = filtered.filter(log => 
        log.chapter_id && filter.chapterIds.includes(log.chapter_id)
      )
    }

    // 작업 ID 필터
    if (filter.jobIds.length > 0) {
      filtered = filtered.filter(log => 
        log.job_id && filter.jobIds.includes(log.job_id)
      )
    }

    // 에러만 보기
    if (filter.showOnlyErrors) {
      filtered = filtered.filter(log => 
        log.level === 'error' || log.level === 'critical'
      )
    }

    // 최근 로그만 보기 (10분 내)
    if (filter.showOnlyRecent) {
      const tenMinutesAgo = new Date(Date.now() - 10 * 60 * 1000)
      filtered = filtered.filter(log => 
        new Date(log.timestamp) > tenMinutesAgo
      )
    }

    onFilterChange(filtered)
  }, [logs, filter, onFilterChange])

  const updateFilter = (updates: Partial<LogFilter>) => {
    setFilter(prev => ({ ...prev, ...updates }))
  }

  const clearAllFilters = () => {
    setFilter({
      levels: [],
      categories: [],
      searchTerm: '',
      dateRange: {},
      chapterIds: [],
      jobIds: [],
      showOnlyErrors: false,
      showOnlyRecent: false
    })
  }

  const saveCurrentFilter = () => {
    const name = prompt('필터 이름을 입력하세요:')
    if (name) {
      setSavedFilters(prev => [...prev, { name, filter: { ...filter } }])
    }
  }

  const loadSavedFilter = (savedFilter: LogFilter) => {
    setFilter(savedFilter)
  }

  const deleteSavedFilter = (index: number) => {
    setSavedFilters(prev => prev.filter((_, i) => i !== index))
  }

  return (
    <div className={`bg-white rounded-lg border border-gray-200 ${className}`}>
      <div className="px-4 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">로그 필터</h3>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setIsAdvancedMode(!isAdvancedMode)}
              className={`text-sm px-3 py-1 rounded ${
                isAdvancedMode ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700'
              }`}
            >
              {isAdvancedMode ? '기본 모드' : '고급 모드'}
            </button>
            <button
              onClick={clearAllFilters}
              className="text-sm text-gray-600 hover:text-gray-800 px-2 py-1 rounded"
            >
              초기화
            </button>
          </div>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* 기본 필터 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* 검색 */}
          <div>
            <label htmlFor="log-search" className="block text-sm font-medium text-gray-700 mb-1">
              검색
            </label>
            <input
              id="log-search"
              type="text"
              value={filter.searchTerm}
              onChange={(e) => updateFilter({ searchTerm: e.target.value })}
              placeholder="메시지, ID 검색..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
            />
          </div>

          {/* 레벨 필터 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              로그 레벨
            </label>
            <div className="space-y-1">
              {uniqueLevels.map(level => (
                <label key={level} className="flex items-center text-sm">
                  <input
                    type="checkbox"
                    checked={filter.levels.includes(level)}
                    onChange={(e) => {
                      const newLevels = e.target.checked
                        ? [...filter.levels, level]
                        : filter.levels.filter(l => l !== level)
                      updateFilter({ levels: newLevels })
                    }}
                    className="mr-2 h-4 w-4 text-black focus:ring-black border-gray-300 rounded"
                  />
                  <span className={`uppercase ${
                    level === 'error' ? 'text-red-600' :
                    level === 'warning' ? 'text-yellow-600' :
                    level === 'info' ? 'text-blue-600' :
                    'text-gray-600'
                  }`}>
                    {level}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* 카테고리 필터 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              카테고리
            </label>
            <div className="space-y-1">
              {uniqueCategories.map(category => (
                <label key={category} className="flex items-center text-sm">
                  <input
                    type="checkbox"
                    checked={filter.categories.includes(category)}
                    onChange={(e) => {
                      const newCategories = e.target.checked
                        ? [...filter.categories, category]
                        : filter.categories.filter(c => c !== category)
                      updateFilter({ categories: newCategories })
                    }}
                    className="mr-2 h-4 w-4 text-black focus:ring-black border-gray-300 rounded"
                  />
                  <span>
                    {category === 'upload' ? '업로드' :
                     category === 'encoding' ? '인코딩' :
                     category === 'processing' ? '처리' :
                     category === 'system' ? '시스템' :
                     category === 'error' ? '에러' : category}
                  </span>
                </label>
              ))}
            </div>
          </div>
        </div>

        {/* 빠른 필터 */}
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => updateFilter({ showOnlyErrors: !filter.showOnlyErrors })}
            className={`text-sm px-3 py-1 rounded-full border ${
              filter.showOnlyErrors
                ? 'bg-red-100 text-red-700 border-red-200'
                : 'bg-gray-100 text-gray-700 border-gray-200'
            }`}
          >
            에러만 보기
          </button>
          
          <button
            onClick={() => updateFilter({ showOnlyRecent: !filter.showOnlyRecent })}
            className={`text-sm px-3 py-1 rounded-full border ${
              filter.showOnlyRecent
                ? 'bg-blue-100 text-blue-700 border-blue-200'
                : 'bg-gray-100 text-gray-700 border-gray-200'
            }`}
          >
            최근 10분
          </button>
          
          <button
            onClick={() => updateFilter({ 
              levels: ['info', 'warning', 'error'],
              categories: ['encoding']
            })}
            className="text-sm px-3 py-1 rounded-full border bg-gray-100 text-gray-700 border-gray-200"
          >
            인코딩 로그만
          </button>
          
          <button
            onClick={() => updateFilter({ 
              levels: ['info'],
              categories: ['upload']
            })}
            className="text-sm px-3 py-1 rounded-full border bg-gray-100 text-gray-700 border-gray-200"
          >
            업로드 로그만
          </button>
        </div>

        {/* 고급 필터 */}
        {isAdvancedMode && (
          <div className="border-t border-gray-200 pt-4 space-y-4">
            {/* 날짜 범위 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                날짜 범위
              </label>
              <div className="grid grid-cols-2 gap-2">
                <input
                  type="datetime-local"
                  value={filter.dateRange.start?.toISOString().slice(0, 16) || ''}
                  onChange={(e) => updateFilter({
                    dateRange: {
                      ...filter.dateRange,
                      start: e.target.value ? new Date(e.target.value) : undefined
                    }
                  })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                />
                <input
                  type="datetime-local"
                  value={filter.dateRange.end?.toISOString().slice(0, 16) || ''}
                  onChange={(e) => updateFilter({
                    dateRange: {
                      ...filter.dateRange,
                      end: e.target.value ? new Date(e.target.value) : undefined
                    }
                  })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                />
              </div>
            </div>

            {/* 챕터 ID 필터 */}
            {uniqueChapterIds.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  챕터 필터
                </label>
                <div className="max-h-32 overflow-y-auto space-y-1">
                  {uniqueChapterIds.map((chapterId) => (
                    <label key={chapterId} className="flex items-center text-sm">
                      <input
                        type="checkbox"
                        checked={chapterId ? filter.chapterIds.includes(chapterId as string) : false}
                        onChange={(e) => {
                          const id = String(chapterId || '')
                          const newChapterIds = e.target.checked
                            ? [...filter.chapterIds, id]
                            : filter.chapterIds.filter(existing => existing !== id)
                          updateFilter({ chapterIds: newChapterIds })
                        }}
                        className="mr-2 h-4 w-4 text-black focus:ring-black border-gray-300 rounded"
                      />
                      <span className="font-mono text-xs">
                        {String(chapterId).slice(0, 8)}...
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {/* 저장된 필터 */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-700">
                  저장된 필터
                </label>
                <button
                  onClick={() => {
                    const name = prompt('필터 이름을 입력하세요:')
                    if (name && name.trim()) {
                      setSavedFilters(prev => [...prev, { name: name.trim(), filter: { ...filter } }])
                    }
                  }}
                  className="text-xs text-blue-600 hover:text-blue-800"
                >
                  현재 필터 저장
                </button>
              </div>
              
              {savedFilters.length > 0 ? (
                <div className="space-y-1">
                  {savedFilters.map((saved, index) => (
                    <div key={index} className="flex items-center justify-between bg-gray-50 px-2 py-1 rounded">
                      <button
                        onClick={() => setFilter(saved.filter)}
                        className="text-sm text-gray-700 hover:text-gray-900 flex-1 text-left"
                      >
                        {saved.name}
                      </button>
                      <button
                        onClick={() => setSavedFilters(prev => prev.filter((_, i) => i !== index))}
                        className="text-xs text-red-600 hover:text-red-800 ml-2"
                      >
                        삭제
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-gray-500">저장된 필터가 없습니다</div>
              )}
            </div>
          </div>
        )}

        {/* 필터 요약 */}
        <div className="border-t border-gray-200 pt-4">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <div>
              {getActiveFilterCount() > 0 && (
                <span>
                  {getActiveFilterCount()}개 필터 활성화
                </span>
              )}
            </div>
            <div>
              {logs.length > 0 && (
                <span>
                  {logs.length}개 로그 중 필터 적용 결과 표시
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )

  function getActiveFilterCount(): number {
    let count = 0
    if (filter.levels.length > 0) count++
    if (filter.categories.length > 0) count++
    if (filter.searchTerm) count++
    if (filter.dateRange.start || filter.dateRange.end) count++
    if (filter.chapterIds.length > 0) count++
    if (filter.jobIds.length > 0) count++
    if (filter.showOnlyErrors) count++
    if (filter.showOnlyRecent) count++
    return count
  }
}

interface LogSearchProps {
  logs: LogMessage[]
  onSearch: (results: LogMessage[]) => void
  className?: string
}

export function LogSearch({ logs, onSearch, className = '' }: LogSearchProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [searchType, setSearchType] = useState<'simple' | 'regex' | 'advanced'>('simple')
  const [caseSensitive, setCaseSensitive] = useState(false)

  useEffect(() => {
    if (!searchTerm) {
      onSearch(logs)
      return
    }

    let filtered: LogMessage[] = []

    try {
      switch (searchType) {
        case 'simple':
          const term = caseSensitive ? searchTerm : searchTerm.toLowerCase()
          filtered = logs.filter(log => {
            const message = caseSensitive ? log.message : log.message.toLowerCase()
            const details = log.details ? 
              (caseSensitive ? JSON.stringify(log.details) : JSON.stringify(log.details).toLowerCase()) : ''
            
            return message.includes(term) || details.includes(term)
          })
          break

        case 'regex':
          const regex = new RegExp(searchTerm, caseSensitive ? 'g' : 'gi')
          filtered = logs.filter(log => 
            regex.test(log.message) || 
            (log.details && regex.test(JSON.stringify(log.details)))
          )
          break

        case 'advanced':
          // 고급 검색: field:value 형식
          filtered = performAdvancedSearch(logs, searchTerm, caseSensitive)
          break
      }

      onSearch(filtered)
    } catch (error) {
      // 정규식 오류 등의 경우 원본 반환
      onSearch(logs)
    }
  }, [logs, searchTerm, searchType, caseSensitive, onSearch])

  return (
    <div className={`bg-white rounded-lg border border-gray-200 p-4 ${className}`}>
      <h3 className="text-lg font-medium text-gray-900 mb-3">로그 검색</h3>
      
      <div className="space-y-3">
        {/* 검색 입력 */}
        <div>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder={
              searchType === 'simple' ? '검색어 입력...' :
              searchType === 'regex' ? '정규식 입력...' :
              'level:error message:encoding 형식으로 입력...'
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
          />
        </div>

        {/* 검색 옵션 */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <select
              value={searchType}
              onChange={(e) => setSearchType(e.target.value as any)}
              className="text-sm border border-gray-300 rounded px-2 py-1"
            >
              <option value="simple">단순 검색</option>
              <option value="regex">정규식</option>
              <option value="advanced">고급 검색</option>
            </select>
            
            <label className="flex items-center text-sm">
              <input
                type="checkbox"
                checked={caseSensitive}
                onChange={(e) => setCaseSensitive(e.target.checked)}
                className="mr-1 h-4 w-4 text-black focus:ring-black border-gray-300 rounded"
              />
              대소문자 구분
            </label>
          </div>
          
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              className="text-sm text-gray-600 hover:text-gray-800"
            >
              검색 지우기
            </button>
          )}
        </div>

        {/* 고급 검색 도움말 */}
        {searchType === 'advanced' && (
          <div className="bg-blue-50 border border-blue-200 rounded p-3 text-sm text-blue-700">
            <div className="font-medium mb-1">고급 검색 문법:</div>
            <div className="space-y-1 text-xs">
              <div><code>level:error</code> - 에러 레벨 로그만</div>
              <div><code>category:encoding</code> - 인코딩 카테고리만</div>
              <div><code>message:upload</code> - 메시지에 'upload' 포함</div>
              <div><code>chapter:abc123</code> - 특정 챕터 ID</div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function performAdvancedSearch(logs: LogMessage[], searchTerm: string, caseSensitive: boolean): LogMessage[] {
  const terms = searchTerm.split(' ').filter(term => term.includes(':'))
  
  if (terms.length === 0) {
    return logs
  }

  return logs.filter(log => {
    return terms.every(term => {
      const [field, value] = term.split(':')
      const searchValue = caseSensitive ? value : value.toLowerCase()
      
      switch (field) {
        case 'level':
          return log.level === searchValue
        case 'category':
          return log.category === searchValue
        case 'message':
          const message = caseSensitive ? log.message : log.message.toLowerCase()
          return message.includes(searchValue)
        case 'chapter':
          return log.chapter_id?.includes(searchValue) || false
        case 'job':
          return log.job_id?.includes(searchValue) || false
        default:
          return false
      }
    })
  })
}
