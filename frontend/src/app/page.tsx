import { redirect } from 'next/navigation'

export default function HomePage() {
  // SSR 단계에서 기본적으로 로그인 페이지로 리다이렉트
  redirect('/login')
}


