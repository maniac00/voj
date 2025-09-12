import { getBooks } from '@/lib/api'

export default async function BooksPage() {
  const books = await getBooks().catch(() => [])

  return (
    <main className="p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">책 목록</h1>
        <a href="/books/new" className="rounded bg-black px-3 py-2 text-white">새 책 등록</a>
      </div>
      <div className="mt-6 overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead>
            <tr className="border-b">
              <th className="py-2">제목</th>
              <th>저자</th>
              <th>출판사</th>
              <th>상태</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {books.map((b) => (
              <tr key={b.book_id} className="border-b">
                <td className="py-2">{b.title}</td>
                <td>{b.author}</td>
                <td>{b.publisher || '-'}</td>
                <td>{b.status || '-'}</td>
                <td>
                  <a href={`/books/${b.book_id}`} className="text-blue-600">편집</a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  )
}


