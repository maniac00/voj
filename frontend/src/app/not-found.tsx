import Link from 'next/link'

export default function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center space-y-6">
        <div className="space-y-2">
          <h1 className="text-6xl font-bold text-gray-900">404</h1>
          <h2 className="text-2xl font-semibold text-gray-700">페이지를 찾을 수 없습니다</h2>
          <p className="text-gray-600">
            요청하신 페이지가 존재하지 않거나 이동되었습니다.
          </p>
        </div>
        
        <div className="space-x-4">
          <Link 
            href="/"
            className="inline-block bg-black text-white px-6 py-3 rounded-md hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-black focus:ring-offset-2"
          >
            홈으로 돌아가기
          </Link>
          
          <Link 
            href="/books"
            className="inline-block bg-gray-100 text-gray-700 px-6 py-3 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
          >
            책 목록 보기
          </Link>
        </div>
        
        <div className="text-sm text-gray-500">
          문제가 지속되면 관리자에게 문의해주세요.
        </div>
      </div>
    </div>
  )
}
